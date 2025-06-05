import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from typing import Dict, List

from app.backend.core import crud, models, schemas
from app.backend.auth.security import create_access_token
from datetime import timedelta, date

API_V1_PREFIX = "/api/v1" # Consistent with conftest.py

# --- Fixtures (can be shared from conftest.py or defined locally if specific) ---
# Re-using fixtures from test_actions_router.py for brevity if they were in conftest.py
# For now, defining them here to be self-contained for this example.

@pytest.fixture(scope="function")
def test_user_comm_owner_data() -> dict: # Renamed to avoid conflict if these were global
    return {"username": "commowner", "email": "commowner@example.com", "password": "commpassword"}

@pytest.fixture(scope="function")
def test_user_comm_owner(db_session: Session, test_user_comm_owner_data: dict) -> models.User:
    user_schema = schemas.UserCreate(**test_user_comm_owner_data)
    return crud.create_user(db=db_session, user=user_schema)

@pytest.fixture(scope="function")
def comm_auth_headers(test_user_comm_owner: models.User) -> Dict[str, str]:
    access_token = create_access_token(
        data={"sub": test_user_comm_owner.username},
        expires_delta=timedelta(minutes=15)
    )
    return {"Authorization": f"Bearer {access_token}"}

@pytest.fixture(scope="function")
def comm_test_business(db_session: Session, test_user_comm_owner: models.User) -> models.Business:
    business_schema = schemas.BusinessCreate(
        business_name="Comm Test Business",
        contact_email="contact@commbusiness.com",
        user_id=test_user_comm_owner.id
    )
    return crud.create_business(db=db_session, business=business_schema)

@pytest.fixture(scope="function")
def comm_test_customer(db_session: Session, comm_test_business: models.Business) -> models.Customer:
    customer_schema = schemas.CustomerCreate(
        customer_name="Comm Test Customer",
        email="customer@commtest.com",
        address="123 Comm St",
        business_id=comm_test_business.id
    )
    return crud.create_customer(db=db_session, customer=customer_schema)

@pytest.fixture(scope="function")
def comm_test_debt(db_session: Session, comm_test_customer: models.Customer, comm_test_business: models.Business) -> models.Debt:
    debt_schema = schemas.DebtCreate(
        original_amount=500.00,
        outstanding_amount=250.00,
        due_date=date(2024, 1, 1),
        status="Overdue",
        customer_id=comm_test_customer.id,
        business_id=comm_test_business.id
    )
    return crud.create_debt(db=db_session, debt=debt_schema)

# --- Tests ---

def test_create_log_for_debt_success(
    client: TestClient,
    comm_test_debt: models.Debt,
    comm_auth_headers: Dict[str, str]
):
    """Test successful creation of a communication log for a debt."""
    log_data = {
        "debt_id": comm_test_debt.id, # This is part of schema but router uses path for debt_id
        "communication_type": "Email",
        "status": "Sent",
        "generated_content_snapshot": "This is a test email content."
    }
    # The POST endpoint is /api/v1/communications/debt/{debt_id}
    response = client.post(
        f"{API_V1_PREFIX}/communications/debt/{comm_test_debt.id}",
        json=log_data,
        headers=comm_auth_headers
    )
    assert response.status_code == 200 # Assuming 200 OK for successful POST
    data = response.json()
    assert data["debt_id"] == comm_test_debt.id
    assert data["communication_type"] == "Email"
    assert data["status"] == "Sent"
    assert data["generated_content_snapshot"] == "This is a test email content."
    assert "id" in data

    # Verify log is in DB
    db_log = crud.get_communication_log(db=next(client.app.dependency_overrides[comms_get_db_dependency]()), log_id=data["id"])
    assert db_log is not None
    assert db_log.communication_type == "Email"


def test_read_debt_communication_logs_success(
    client: TestClient,
    comm_test_debt: models.Debt,
    comm_auth_headers: Dict[str, str],
    db_session: Session # Using db_session directly to create a log first
):
    """Test retrieving communication logs for a specific debt."""
    # Create a log first directly via CRUD for this test
    log_create_schema = schemas.CommunicationLogCreate(
        debt_id=comm_test_debt.id,
        communication_type="Initial Call",
        status="Completed"
    )
    crud.create_communication_log(db=db_session, log=log_create_schema, debt_id=comm_test_debt.id)

    response = client.get(
        f"{API_V1_PREFIX}/communications/debt/{comm_test_debt.id}",
        headers=comm_auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0 # Expecting at least the one we created
    assert data[0]["communication_type"] == "Initial Call" # Assuming default sort order by date_sent desc
    assert data[0]["debt_id"] == comm_test_debt.id


def test_read_debt_communication_logs_unauthorized_debt(
    client: TestClient,
    comm_auth_headers: Dict[str, str] # Auth headers for a valid user
):
    """Test retrieving logs for a debt not owned by the user (or non-existent)."""
    non_existent_or_unauthorized_debt_id = 99998
    response = client.get(
        f"{API_V1_PREFIX}/communications/debt/{non_existent_or_unauthorized_debt_id}",
        headers=comm_auth_headers
    )
    assert response.status_code == 403 # Changed from 404
    # This is because get_authorized_business_id will be called.
    # If the user `comm_test_user_owner` is created by its fixture but `comm_test_business` is not used,
    # then this user will have no businesses.
    assert "User has no associated businesses." in response.json()["detail"]
    # If the test setup *did* ensure the user has a business, but the debt ID is simply not found *for that business*,
    # then the router's `crud.get_debt` would return None, leading to a 404 with "Debt not found or not authorized..."
    # The current fixture setup for this specific test does not create a business for comm_test_user_owner.


def test_create_log_for_debt_unauthorized_debt(
    client: TestClient,
    comm_auth_headers: Dict[str, str]
):
    """Test creating a log for a debt not owned by the user."""
    non_existent_or_unauthorized_debt_id = 99997
    log_data = {
        "debt_id": non_existent_or_unauthorized_debt_id,
        "communication_type": "SMS",
        "status": "Failed"
    }
    response = client.post(
        f"{API_V1_PREFIX}/communications/debt/{non_existent_or_unauthorized_debt_id}",
        json=log_data,
        headers=comm_auth_headers
    )
    assert response.status_code == 403 # Changed from 404
    assert "User has no associated businesses." in response.json()["detail"]

def test_read_single_communication_log_success(
    client: TestClient,
    comm_test_debt: models.Debt,
    comm_auth_headers: Dict[str, str],
    db_session: Session
):
    log_create_schema = schemas.CommunicationLogCreate(
        debt_id=comm_test_debt.id, communication_type="Test Log", status="Draft"
    )
    created_log = crud.create_communication_log(db=db_session, log=log_create_schema, debt_id=comm_test_debt.id)

    response = client.get(
        f"{API_V1_PREFIX}/communications/{created_log.id}",
        headers=comm_auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == created_log.id
    assert data["communication_type"] == "Test Log"


def test_update_communication_log_success(
    client: TestClient,
    comm_test_debt: models.Debt,
    comm_auth_headers: Dict[str, str],
    db_session: Session
):
    log_create_schema = schemas.CommunicationLogCreate(
        debt_id=comm_test_debt.id, communication_type="Original Type", status="Original Status"
    )
    created_log = crud.create_communication_log(db=db_session, log=log_create_schema, debt_id=comm_test_debt.id)

    update_data = {"communication_type": "Updated Type", "status": "Updated Status"}
    response = client.put(
        f"{API_V1_PREFIX}/communications/{created_log.id}",
        json=update_data,
        headers=comm_auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == created_log.id
    assert data["communication_type"] == "Updated Type"
    assert data["status"] == "Updated Status"

    # Verify in DB
    updated_db_log = crud.get_communication_log(db_session, log_id=created_log.id)
    assert updated_db_log.communication_type == "Updated Type"
    assert updated_db_log.status == "Updated Status"

# Need to import comms_get_db_dependency for the client.app.dependency_overrides line
from app.backend.routers.communications import get_db as comms_get_db_dependency
