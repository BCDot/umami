import pytest
from sqlalchemy.orm import Session
from typing import Dict
from datetime import datetime, date, timedelta # Added date, timedelta
from decimal import Decimal # Added Decimal

from app.backend.core import crud, models, schemas

# --- Fixtures for CommunicationLog CRUD Tests ---

@pytest.fixture(scope="function")
def test_user_for_comm_log_crud(db: Session) -> models.User:
    user_data = {"username": "commloguser", "email": "commlog@example.com", "password": "commlogpassword"}
    return crud.create_user(db=db, user=schemas.UserCreate(**user_data))

@pytest.fixture(scope="function")
def test_business_for_comm_log_crud(db: Session, test_user_for_comm_log_crud: models.User) -> models.Business:
    return crud.create_business(db=db, business=schemas.BusinessCreate(
        business_name="CommLog Test Biz",
        contact_email="biz.commlog@example.com",
        user_id=test_user_for_comm_log_crud.id
    ))

@pytest.fixture(scope="function")
def test_customer_for_comm_log_crud(db: Session, test_business_for_comm_log_crud: models.Business) -> models.Customer:
    return crud.create_customer(db=db, customer=schemas.CustomerCreate(
        customer_name="CommLog Customer",
        email="cust.commlog@example.com",
        address="1 CommLog Rd",
        business_id=test_business_for_comm_log_crud.id
    ))

@pytest.fixture(scope="function")
def test_debt_for_comm_log_crud(db: Session, test_customer_for_comm_log_crud: models.Customer, test_business_for_comm_log_crud: models.Business) -> models.Debt:
    debt_data = schemas.DebtCreate(
        original_amount=Decimal("300.00"),
        outstanding_amount=Decimal("200.00"),
        due_date=date.today() - timedelta(days=5),
        status="Overdue",
        debt_type="Service",
        customer_id=test_customer_for_comm_log_crud.id,
        business_id=test_business_for_comm_log_crud.id
    )
    return crud.create_debt(db=db, debt=debt_data)

@pytest.fixture(scope="function")
def test_comm_log(db: Session, test_debt_for_comm_log_crud: models.Debt) -> models.CommunicationLog:
    log_data = schemas.CommunicationLogCreate(
        debt_id=test_debt_for_comm_log_crud.id,
        communication_type="Initial Email",
        status="Sent",
        generated_content_snapshot="This is the first email content."
    )
    # crud.create_communication_log takes debt_id as a separate argument
    return crud.create_communication_log(db=db, log=log_data, debt_id=test_debt_for_comm_log_crud.id)

# --- CommunicationLog CRUD Tests ---

def test_create_communication_log(db: Session, test_debt_for_comm_log_crud: models.Debt):
    """Test creating a new communication log."""
    log_data = schemas.CommunicationLogCreate(
        debt_id=test_debt_for_comm_log_crud.id, # debt_id is part of schema
        communication_type="Phone Call",
        status="Completed",
        generated_content_snapshot="Spoke to customer, agreed to payment plan.",
        response_received="Customer will pay $50 weekly."
    )
    created_log = crud.create_communication_log(db=db, log=log_data, debt_id=test_debt_for_comm_log_crud.id)

    assert created_log is not None
    assert created_log.debt_id == test_debt_for_comm_log_crud.id
    assert created_log.communication_type == "Phone Call"
    assert created_log.status == "Completed"
    assert created_log.response_received == "Customer will pay $50 weekly."
    assert created_log.id is not None
    assert isinstance(created_log.date_sent, datetime) # Should be set by server_default

def test_get_communication_log(db: Session, test_comm_log: models.CommunicationLog):
    """Test fetching a communication log by its ID."""
    fetched_log = crud.get_communication_log(db, log_id=test_comm_log.id)
    assert fetched_log is not None
    assert fetched_log.id == test_comm_log.id
    assert fetched_log.communication_type == "Initial Email"

def test_get_communication_logs_for_debt(db: Session, test_debt_for_comm_log_crud: models.Debt, test_comm_log: models.CommunicationLog):
    """Test fetching all communication logs for a specific debt."""
    # Create another log for the same debt to test list retrieval
    log_data2 = schemas.CommunicationLogCreate(
        debt_id=test_debt_for_comm_log_crud.id, communication_type="Follow-up SMS", status="Delivered"
    )
    crud.create_communication_log(db=db, log=log_data2, debt_id=test_debt_for_comm_log_crud.id)

    logs = crud.get_communication_logs_for_debt(db, debt_id=test_debt_for_comm_log_crud.id)
    assert logs is not None
    assert len(logs) == 2 # test_comm_log + log_data2
    # Default order is date_sent desc, so log_data2 should be first if created after.
    # For simplicity, just check if both types are present
    log_types = {log.communication_type for log in logs}
    assert "Initial Email" in log_types
    assert "Follow-up SMS" in log_types

def test_update_communication_log_partial(db: Session, test_comm_log: models.CommunicationLog):
    """Test partially updating a communication log's status and response."""
    update_data = schemas.CommunicationLogUpdate(
        status="Customer Responded",
        response_received="Customer acknowledged the debt via email."
    )
    updated_log = crud.update_communication_log(db=db, log_id=test_comm_log.id, log_update=update_data)

    assert updated_log is not None
    assert updated_log.status == "Customer Responded"
    assert updated_log.response_received == "Customer acknowledged the debt via email."
    assert updated_log.communication_type == test_comm_log.communication_type # Should remain unchanged
    assert updated_log.generated_content_snapshot == test_comm_log.generated_content_snapshot # Should remain unchanged

    # Fetch again to confirm persistence
    refetched_log = crud.get_communication_log(db, log_id=test_comm_log.id)
    assert refetched_log is not None
    assert refetched_log.status == "Customer Responded"
    assert refetched_log.response_received == "Customer acknowledged the debt via email."
