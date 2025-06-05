import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from typing import Dict, List

from app.backend.core import crud, models, schemas
from app.backend.auth.security import create_access_token
from datetime import timedelta

API_V1_PREFIX = "/api/v1" # Consistent with conftest.py and main.py customer router prefix

# --- Fixtures ---

@pytest.fixture(scope="function")
def test_user_customer_router(db: Session) -> models.User: # Uses 'db' from conftest.py
    user_data = {"username": "custrouteruser", "email": "custrouter@example.com", "password": "custpassword"}
    user_schema = schemas.UserCreate(**user_data)
    return crud.create_user(db=db, user=user_schema)

@pytest.fixture(scope="function")
def test_user_customer_router_2(db: Session) -> models.User:
    user_data = {"username": "custrouteruser2", "email": "custrouter2@example.com", "password": "custpassword2"}
    user_schema = schemas.UserCreate(**user_data)
    return crud.create_user(db=db, user=user_schema)

@pytest.fixture(scope="function")
def customer_auth_headers(client: TestClient, test_user_customer_router: models.User) -> Dict[str, str]:
    login_data = {"username": test_user_customer_router.username, "password": "custpassword"}
    response = client.post(f"{API_V1_PREFIX}/auth/token", data=login_data)
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture(scope="function")
def test_business_for_customer_tests(db: Session, test_user_customer_router: models.User) -> models.Business:
    business_schema = schemas.BusinessCreate(
        business_name="Customer Test Biz",
        contact_email="ctb@example.com",
        user_id=test_user_customer_router.id
    )
    return crud.create_business(db=db, business=business_schema)

@pytest.fixture(scope="function")
def test_business_for_customer_tests_user2(db: Session, test_user_customer_router_2: models.User) -> models.Business:
    business_schema = schemas.BusinessCreate(
        business_name="Customer Test Biz User2",
        contact_email="ctb2@example.com",
        user_id=test_user_customer_router_2.id
    )
    return crud.create_business(db=db, business=business_schema)


@pytest.fixture(scope="function")
def sample_customer(db: Session, test_business_for_customer_tests: models.Business) -> models.Customer:
    customer_schema = schemas.CustomerCreate(
        customer_name="Sample Customer One",
        email="sample.cust1@example.com",
        address="123 Main St",
        business_id=test_business_for_customer_tests.id
    )
    return crud.create_customer(db=db, customer=customer_schema)

# --- Customer Endpoint Tests ---

def test_create_customer_success(client: TestClient, customer_auth_headers: Dict[str, str], test_business_for_customer_tests: models.Business):
    customer_data = {
        "customer_name": "New Test Customer",
        "email": "newcust@example.com",
        "address": "456 New Ave",
        "phone": "1234567890",
        "business_id": test_business_for_customer_tests.id,
        "is_active": True
    }
    response = client.post(f"{API_V1_PREFIX}/customers/", json=customer_data, headers=customer_auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["customer_name"] == "New Test Customer"
    assert data["email"] == "newcust@example.com"
    assert data["business_id"] == test_business_for_customer_tests.id

def test_create_customer_unauthorized_business(client: TestClient, customer_auth_headers: Dict[str, str], test_business_for_customer_tests_user2: models.Business):
    customer_data = {
        "customer_name": "Unauthorized Cust",
        "email": "unauth@example.com",
        "address": "789 Unauth St",
        "business_id": test_business_for_customer_tests_user2.id # Belongs to user 2
    }
    response = client.post(f"{API_V1_PREFIX}/customers/", json=customer_data, headers=customer_auth_headers) # User 1's token
    assert response.status_code == 403
    assert "Business not found or not authorized" in response.json()["detail"]

def test_list_customers_success(client: TestClient, customer_auth_headers: Dict[str, str], test_business_for_customer_tests: models.Business, sample_customer: models.Customer):
    response = client.get(f"{API_V1_PREFIX}/customers/?business_id={test_business_for_customer_tests.id}", headers=customer_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert any(c["id"] == sample_customer.id for c in data)

def test_list_customers_missing_business_id(client: TestClient, customer_auth_headers: Dict[str, str]):
    response = client.get(f"{API_V1_PREFIX}/customers/", headers=customer_auth_headers)
    assert response.status_code == 400 # As per router logic
    assert "The 'business_id' query parameter is required." in response.json()["detail"] # Exact match


def test_list_customers_unauthorized_business(client: TestClient, customer_auth_headers: Dict[str, str], test_business_for_customer_tests_user2: models.Business):
    response = client.get(f"{API_V1_PREFIX}/customers/?business_id={test_business_for_customer_tests_user2.id}", headers=customer_auth_headers)
    assert response.status_code == 403

def test_read_customer_success(client: TestClient, customer_auth_headers: Dict[str, str], sample_customer: models.Customer):
    response = client.get(f"{API_V1_PREFIX}/customers/{sample_customer.id}", headers=customer_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == sample_customer.id
    assert data["customer_name"] == sample_customer.customer_name

def test_read_customer_unauthorized(client: TestClient, db:Session, customer_auth_headers: Dict[str, str], test_business_for_customer_tests_user2: models.Business):
    # Create a customer for user 2's business
    other_user_customer_schema = schemas.CustomerCreate(
        customer_name="Other User Customer", email="other@example.com", address="Other St",
        business_id=test_business_for_customer_tests_user2.id
    )
    other_user_customer = crud.create_customer(db, customer=other_user_customer_schema)

    response = client.get(f"{API_V1_PREFIX}/customers/{other_user_customer.id}", headers=customer_auth_headers) # User 1 token
    assert response.status_code == 404 # Because get_customer_by_id_for_user won't find it for this user
    assert "Customer not found or not authorized" in response.json()["detail"]


def test_read_customer_not_found(client: TestClient, customer_auth_headers: Dict[str, str]):
    response = client.get(f"{API_V1_PREFIX}/customers/99999", headers=customer_auth_headers)
    assert response.status_code == 404

def test_update_customer_success(client: TestClient, customer_auth_headers: Dict[str, str], sample_customer: models.Customer):
    update_data = {"customer_name": "Updated Sample Customer", "phone": "0400123456"}
    response = client.put(f"{API_V1_PREFIX}/customers/{sample_customer.id}", json=update_data, headers=customer_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["customer_name"] == "Updated Sample Customer"
    assert data["phone"] == "0400123456"
    assert data["id"] == sample_customer.id

def test_update_customer_unauthorized(client: TestClient, db:Session, customer_auth_headers: Dict[str, str], test_business_for_customer_tests_user2: models.Business):
    other_user_customer_schema = schemas.CustomerCreate(
        customer_name="Other User Customer Update", email="otherupdate@example.com", address="Other Update St",
        business_id=test_business_for_customer_tests_user2.id
    )
    other_user_customer = crud.create_customer(db, customer=other_user_customer_schema)
    update_data = {"customer_name": "Attempted Update"}
    response = client.put(f"{API_V1_PREFIX}/customers/{other_user_customer.id}", json=update_data, headers=customer_auth_headers)
    assert response.status_code == 404
    assert "Customer not found or not authorized" in response.json()["detail"]


def test_archive_customer_success(client: TestClient, customer_auth_headers: Dict[str, str], sample_customer: models.Customer, db: Session):
    response = client.delete(f"{API_V1_PREFIX}/customers/{sample_customer.id}", headers=customer_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["is_active"] is False
    assert data["id"] == sample_customer.id

    # Verify in DB
    db_customer = crud.get_customer_by_id_unscoped(db, customer_id=sample_customer.id)
    assert db_customer.is_active is False

def test_archive_customer_unauthorized(client: TestClient, db:Session, customer_auth_headers: Dict[str, str], test_business_for_customer_tests_user2: models.Business):
    other_user_customer_schema = schemas.CustomerCreate(
        customer_name="Other User Customer Archive", email="otherarchive@example.com", address="Other Archive St",
        business_id=test_business_for_customer_tests_user2.id
    )
    other_user_customer = crud.create_customer(db, customer=other_user_customer_schema)

    response = client.delete(f"{API_V1_PREFIX}/customers/{other_user_customer.id}", headers=customer_auth_headers)
    assert response.status_code == 404
    assert "Customer not found or not authorized" in response.json()["detail"]
