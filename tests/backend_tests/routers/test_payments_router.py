import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from typing import Dict, List
from decimal import Decimal
from datetime import date, timedelta, datetime

from app.backend.core import crud, models, schemas
from app.backend.auth.security import create_access_token

API_V1_PREFIX = "/api/v1"

# --- Fixtures ---
@pytest.fixture(scope="function")
def test_user_payment_router(db: Session) -> models.User:
    user_data = {"username": "paymentuser", "email": "paymentuser@example.com", "password": "paymentpassword"}
    return crud.create_user(db=db, user=schemas.UserCreate(**user_data))

@pytest.fixture(scope="function")
def test_user_payment_router_2(db: Session) -> models.User: # Another user
    user_data = {"username": "paymentuser2", "email": "paymentuser2@example.com", "password": "paymentpassword2"}
    return crud.create_user(db=db, user=schemas.UserCreate(**user_data))

@pytest.fixture(scope="function")
def payment_auth_headers(client: TestClient, test_user_payment_router: models.User) -> Dict[str, str]:
    login_data = {"username": test_user_payment_router.username, "password": "paymentpassword"}
    response = client.post(f"{API_V1_PREFIX}/auth/token", data=login_data)
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture(scope="function")
def test_business_for_payment(db: Session, test_user_payment_router: models.User) -> models.Business:
    return crud.create_business(db=db, business=schemas.BusinessCreate(
        business_name="Payment Test Biz", contact_email="contact@paymentbiz.com", user_id=test_user_payment_router.id
    ))

@pytest.fixture(scope="function")
def test_customer_for_payment(db: Session, test_business_for_payment: models.Business) -> models.Customer:
    return crud.create_customer(db=db, customer=schemas.CustomerCreate(
        customer_name="Payment Test Customer", email="cust.payment@example.com", address="1 Pay St",
        business_id=test_business_for_payment.id
    ))

@pytest.fixture(scope="function")
def test_debt_for_payment(db: Session, test_customer_for_payment: models.Customer, test_business_for_payment: models.Business) -> models.Debt:
    return crud.create_debt(db=db, debt=schemas.DebtCreate(
        original_amount=Decimal("1000.00"), outstanding_amount=Decimal("800.00"),
        due_date=date.today() - timedelta(days=30), status="Overdue", customer_id=test_customer_for_payment.id,
        business_id=test_business_for_payment.id, debt_type="Service", invoice_number="INV-PAY-001"
    ))

@pytest.fixture(scope="function")
def test_payment(db: Session, test_debt_for_payment: models.Debt) -> models.Payment:
    # Create a payment to ensure the debt's outstanding amount is updated for subsequent tests
    payment_schema = schemas.PaymentCreate(
        debt_id=test_debt_for_payment.id,
        amount_paid=Decimal("100.00"),
        payment_date=date.today() - timedelta(days=1)
    )
    return crud.create_payment(db=db, payment=payment_schema, debt_id=test_debt_for_payment.id)


# --- Payment Endpoint Tests ---

def test_create_payment_success(client: TestClient, payment_auth_headers: Dict[str, str], test_debt_for_payment: models.Debt, db:Session):
    initial_outstanding = test_debt_for_payment.outstanding_amount
    payment_amount = Decimal("50.00")
    payment_data = {
        "debt_id": test_debt_for_payment.id,
        "amount_paid": str(payment_amount), # Pydantic will convert to Decimal
        "payment_date": str(date.today()),
        "payment_method": "Credit Card",
        "notes": "Test payment successful"
    }
    response = client.post(f"{API_V1_PREFIX}/payments/", json=payment_data, headers=payment_auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["debt_id"] == test_debt_for_payment.id
    assert Decimal(data["amount_paid"]) == payment_amount
    assert data["payment_method"] == "Credit Card"

    # Verify debt outstanding amount updated
    db.refresh(test_debt_for_payment) # Refresh from DB
    assert test_debt_for_payment.outstanding_amount == initial_outstanding - payment_amount

def test_create_payment_for_unauthorized_debt(client: TestClient, payment_auth_headers: Dict[str, str], test_user_payment_router_2: models.User, db: Session):
    # Create a debt for another user
    other_biz = crud.create_business(db, schemas.BusinessCreate(business_name="OtherBizPay", contact_email="o@b.c", user_id=test_user_payment_router_2.id))
    other_cust = crud.create_customer(db, schemas.CustomerCreate(customer_name="OtherCustPay", email="oc@p.c", address="ocp st", business_id=other_biz.id))
    other_debt = crud.create_debt(db, schemas.DebtCreate(original_amount=100, outstanding_amount=100, due_date=date.today(), status="New", customer_id=other_cust.id, business_id=other_biz.id))

    payment_data = {"debt_id": other_debt.id, "amount_paid": "10.00", "payment_date": str(date.today())}
    response = client.post(f"{API_V1_PREFIX}/payments/", json=payment_data, headers=payment_auth_headers) # User1's token
    assert response.status_code == 404 # Because get_authorized_debt uses get_debt_by_id_for_user
    assert "Debt not found or not authorized" in response.json()["detail"]


def test_list_payments_for_debt_success(client: TestClient, payment_auth_headers: Dict[str, str], test_debt_for_payment: models.Debt, test_payment: models.Payment):
    response = client.get(f"{API_V1_PREFIX}/payments/?debt_id={test_debt_for_payment.id}", headers=payment_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert any(p["id"] == test_payment.id for p in data)

def test_list_payments_for_unauthorized_debt(client: TestClient, payment_auth_headers: Dict[str, str], test_user_payment_router_2: models.User, db: Session):
    other_biz = crud.create_business(db, schemas.BusinessCreate(business_name="OtherBizPayList", contact_email="o@bl.c", user_id=test_user_payment_router_2.id))
    other_cust = crud.create_customer(db, schemas.CustomerCreate(customer_name="OtherCustPayList", email="oc@pl.c", address="ocpl st", business_id=other_biz.id))
    other_debt = crud.create_debt(db, schemas.DebtCreate(original_amount=100, outstanding_amount=100, due_date=date.today(), status="New", customer_id=other_cust.id, business_id=other_biz.id))

    response = client.get(f"{API_V1_PREFIX}/payments/?debt_id={other_debt.id}", headers=payment_auth_headers)
    assert response.status_code == 404 # Debt not found for this user
    assert "Debt not found or not authorized" in response.json()["detail"]


def test_read_payment_success(client: TestClient, payment_auth_headers: Dict[str, str], test_payment: models.Payment):
    response = client.get(f"{API_V1_PREFIX}/payments/{test_payment.id}", headers=payment_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_payment.id
    assert Decimal(data["amount_paid"]) == test_payment.amount_paid

def test_update_payment_success(client: TestClient, payment_auth_headers: Dict[str, str], test_payment: models.Payment, test_debt_for_payment: models.Debt, db: Session):
    initial_debt_outstanding = test_debt_for_payment.outstanding_amount
    old_payment_amount = test_payment.amount_paid
    new_payment_amount = Decimal("20.00")

    update_data = {"amount_paid": str(new_payment_amount), "notes": "Updated payment amount"}
    response = client.put(f"{API_V1_PREFIX}/payments/{test_payment.id}", json=update_data, headers=payment_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert Decimal(data["amount_paid"]) == new_payment_amount
    assert data["notes"] == "Updated payment amount"

    db.refresh(test_debt_for_payment)
    expected_outstanding = initial_debt_outstanding + old_payment_amount - new_payment_amount
    assert test_debt_for_payment.outstanding_amount == expected_outstanding

def test_delete_payment_success(client: TestClient, payment_auth_headers: Dict[str, str], test_payment: models.Payment, test_debt_for_payment: models.Debt, db: Session):
    initial_debt_outstanding = test_debt_for_payment.outstanding_amount
    payment_amount_to_restore = test_payment.amount_paid

    response = client.delete(f"{API_V1_PREFIX}/payments/{test_payment.id}", headers=payment_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_payment.id # Returns deleted payment

    # Verify payment is deleted
    deleted_db_payment = crud.get_payment(db, payment_id=test_payment.id)
    assert deleted_db_payment is None

    # Verify debt outstanding amount is updated
    db.refresh(test_debt_for_payment)
    assert test_debt_for_payment.outstanding_amount == initial_debt_outstanding + payment_amount_to_restore
