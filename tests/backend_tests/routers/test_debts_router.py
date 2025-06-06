import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from typing import Dict, List
from decimal import Decimal
from datetime import date, timedelta

from app.backend.core import crud, models, schemas
from app.backend.auth.security import create_access_token

API_V1_PREFIX = "/api/v1" # Defined in main.py for including routers

# --- Fixtures ---

@pytest.fixture(scope="function")
def test_user_debt_router(db: Session) -> models.User:
    user_data = {"username": "debtrouteruser", "email": "debtrouter@example.com", "password": "debtpassword"}
    return crud.create_user(db=db, user=schemas.UserCreate(**user_data))

@pytest.fixture(scope="function")
def test_user_debt_router_2(db: Session) -> models.User:
    user_data = {"username": "debtrouteruser2", "email": "debtrouter2@example.com", "password": "debtpassword2"}
    return crud.create_user(db=db, user=schemas.UserCreate(**user_data))

@pytest.fixture(scope="function")
def debt_auth_headers(client: TestClient, test_user_debt_router: models.User) -> Dict[str, str]:
    login_data = {"username": test_user_debt_router.username, "password": "debtpassword"}
    response = client.post(f"{API_V1_PREFIX}/auth/token", data=login_data)
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture(scope="function")
def test_business_for_debt(db: Session, test_user_debt_router: models.User) -> models.Business:
    return crud.create_business(db=db, business=schemas.BusinessCreate(
        business_name="Debt Test Biz", contact_email="dtb@example.com", user_id=test_user_debt_router.id
    ))

@pytest.fixture(scope="function")
def test_business_for_debt_user2(db: Session, test_user_debt_router_2: models.User) -> models.Business:
     return crud.create_business(db=db, business=schemas.BusinessCreate(
        business_name="Debt Test Biz User2", contact_email="dtb2@example.com", user_id=test_user_debt_router_2.id
    ))

@pytest.fixture(scope="function")
def test_customer_for_debt(db: Session, test_business_for_debt: models.Business) -> models.Customer:
    return crud.create_customer(db=db, customer=schemas.CustomerCreate(
        customer_name="Debt Test Customer", email="debtcust@example.com", address="789 Debt St",
        business_id=test_business_for_debt.id
    ))

@pytest.fixture(scope="function")
def sample_debt(db: Session, test_customer_for_debt: models.Customer, test_business_for_debt: models.Business) -> models.Debt:
    return crud.create_debt(db=db, debt=schemas.DebtCreate(
        original_amount=Decimal("100.00"), outstanding_amount=Decimal("75.00"),
        due_date=date.today() - timedelta(days=30), status="Overdue",
        customer_id=test_customer_for_debt.id, business_id=test_business_for_debt.id
    ))

# --- Debt Endpoint Tests ---

def test_create_debt_success(client: TestClient, debt_auth_headers: Dict[str, str], test_customer_for_debt: models.Customer, test_business_for_debt: models.Business):
    debt_data = {
        "original_amount": "250.50", "outstanding_amount": "200.00", "due_date": str(date.today()),
        "status": "Outstanding", "customer_id": test_customer_for_debt.id, "business_id": test_business_for_debt.id
    }
    response = client.post(f"{API_V1_PREFIX}/debts/", json=debt_data, headers=debt_auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert Decimal(data["original_amount"]) == Decimal("250.50")
    assert data["customer_id"] == test_customer_for_debt.id

def test_create_debt_unauthorized_business(client: TestClient, debt_auth_headers: Dict[str, str], test_customer_for_debt: models.Customer, test_business_for_debt_user2: models.Business):
    debt_data = { # Attempting to create debt under business of user2, using user1's token
        "original_amount": "100.00", "outstanding_amount": "100.00", "due_date": str(date.today()),
        "status": "Outstanding", "customer_id": test_customer_for_debt.id, # This customer belongs to user1's business
        "business_id": test_business_for_debt_user2.id # Business of user2
    }
    response = client.post(f"{API_V1_PREFIX}/debts/", json=debt_data, headers=debt_auth_headers)
    assert response.status_code == 403 # Business not owned by current_user

def test_create_debt_customer_not_in_business(client: TestClient, debt_auth_headers: Dict[str, str], test_business_for_debt: models.Business, test_business_for_debt_user2: models.Business, db: Session):
    # Create customer for user2's business
    other_customer = crud.create_customer(db=db, customer=schemas.CustomerCreate(
        customer_name="Other Biz Customer", email="otherbiz@example.com", address="Other Addr",
        business_id=test_business_for_debt_user2.id
    ))
    debt_data = { # Attempting to create debt under user1's business but with customer from user2's business
        "original_amount": "100.00", "outstanding_amount": "100.00", "due_date": str(date.today()),
        "status": "Outstanding", "customer_id": other_customer.id,
        "business_id": test_business_for_debt.id
    }
    response = client.post(f"{API_V1_PREFIX}/debts/", json=debt_data, headers=debt_auth_headers)
    assert response.status_code == 404 # Customer not found for this business
    assert "Customer not found for this business" in response.json()["detail"]


def test_list_debts_by_business_success(client: TestClient, debt_auth_headers: Dict[str, str], sample_debt: models.Debt, test_business_for_debt: models.Business):
    response = client.get(f"{API_V1_PREFIX}/debts/?business_id={test_business_for_debt.id}", headers=debt_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert any(d["id"] == sample_debt.id for d in data)

def test_list_debts_by_business_unauthorized(client: TestClient, debt_auth_headers: Dict[str, str], test_business_for_debt_user2: models.Business):
    response = client.get(f"{API_V1_PREFIX}/debts/?business_id={test_business_for_debt_user2.id}", headers=debt_auth_headers)
    assert response.status_code == 403

def test_list_debts_by_customer_owned_success(client: TestClient, debt_auth_headers: Dict[str, str], test_customer_for_debt: models.Customer, sample_debt: models.Debt):
    """Test listing debts for a specific customer owned by the current user."""
    # sample_debt fixture ensures a debt exists for test_customer_for_debt
    response = client.get(f"{API_V1_PREFIX}/debts/?customer_id={test_customer_for_debt.id}", headers=debt_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert any(d["id"] == sample_debt.id and d["customer_id"] == test_customer_for_debt.id for d in data)

def test_list_debts_by_customer_unowned(client: TestClient, debt_auth_headers: Dict[str, str], db: Session, test_business_for_debt_user2: models.Business):
    """Test listing debts for a customer whose business is not owned by the current user."""
    # Create a customer belonging to user2's business
    other_user_customer = crud.create_customer(db=db, customer=schemas.CustomerCreate(
        customer_name="Unowned Customer for Debt List", email="unownedcustdebt@example.com", address="789 Unowned St",
        business_id=test_business_for_debt_user2.id
    ))
    # Optionally, create a debt for this customer, though not strictly necessary for this auth test
    # crud.create_debt(db=db, debt=schemas.DebtCreate(
    #     original_amount=50, outstanding_amount=50, due_date=date.today(), status="New",
    #     customer_id=other_user_customer.id, business_id=test_business_for_debt_user2.id
    # ))

    response = client.get(f"{API_V1_PREFIX}/debts/?customer_id={other_user_customer.id}", headers=debt_auth_headers) # User1's token
    assert response.status_code == 403 # Or 404 if customer itself is considered not found for this user
    assert "Not authorized to view debts for this customer" in response.json()["detail"]


def test_list_debts_no_params(client: TestClient, debt_auth_headers: Dict[str, str]):
    response = client.get(f"{API_V1_PREFIX}/debts/", headers=debt_auth_headers)
    assert response.status_code == 400
    assert "Either business_id or customer_id query parameter is required" in response.json()["detail"]


def test_read_debt_success(client: TestClient, debt_auth_headers: Dict[str, str], sample_debt: models.Debt):
    response = client.get(f"{API_V1_PREFIX}/debts/{sample_debt.id}", headers=debt_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == sample_debt.id

def test_read_debt_unauthorized(client: TestClient, debt_auth_headers: Dict[str, str], db: Session, test_customer_for_debt: models.Customer, test_business_for_debt_user2: models.Business):
    # Create a debt belonging to user2's business
    other_debt = crud.create_debt(db=db, debt=schemas.DebtCreate(
        original_amount=50, outstanding_amount=50, due_date=date.today(), status="New",
        customer_id=test_customer_for_debt.id, # This customer belongs to business1, but we assign debt to business2
        business_id=test_business_for_debt_user2.id
    ))
    response = client.get(f"{API_V1_PREFIX}/debts/{other_debt.id}", headers=debt_auth_headers) # User1 token
    assert response.status_code == 404 # get_debt_by_id_for_user won't find it for user1
    assert "Debt not found or not authorized" in response.json()["detail"]


def test_update_debt_success(client: TestClient, debt_auth_headers: Dict[str, str], sample_debt: models.Debt):
    update_data = {"status": "Paid", "outstanding_amount": "0.00"}
    response = client.put(f"{API_V1_PREFIX}/debts/{sample_debt.id}", json=update_data, headers=debt_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "Paid"
    assert Decimal(data["outstanding_amount"]) == Decimal("0.00")

def test_archive_debt_success(client: TestClient, debt_auth_headers: Dict[str, str], sample_debt: models.Debt, db: Session):
    response = client.delete(f"{API_V1_PREFIX}/debts/{sample_debt.id}", headers=debt_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["is_archived"] is True
    db_debt = crud.get_debt_by_id_unscoped(db, debt_id=sample_debt.id) # New helper to get any debt
    assert db_debt.is_archived is True
