import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import patch # For mocking the LLM call
from typing import Dict, Generator

from app.backend.core import crud, models, schemas
from app.backend.auth.security import create_access_token # For auth_headers
from datetime import timedelta, date

API_V1_PREFIX = "/api/v1" # Consistent with conftest.py

# --- Fixtures ---

@pytest.fixture(scope="function")
def test_user_owner_data() -> dict:
    return {"username": "actionowner", "email": "actionowner@example.com", "password": "actionpassword"}

@pytest.fixture(scope="function")
def test_user_owner(db_session: Session, test_user_owner_data: dict) -> models.User:
    user_schema = schemas.UserCreate(**test_user_owner_data)
    return crud.create_user(db=db_session, user=user_schema)

@pytest.fixture(scope="function")
def auth_headers(test_user_owner: models.User) -> Dict[str, str]:
    """Fixture to create authentication headers for the test_user_owner."""
    access_token = create_access_token(
        data={"sub": test_user_owner.username},
        expires_delta=timedelta(minutes=15)
    )
    return {"Authorization": f"Bearer {access_token}"}

@pytest.fixture(scope="function")
def test_business(db_session: Session, test_user_owner: models.User) -> models.Business:
    business_schema = schemas.BusinessCreate(
        business_name="Action Test Business",
        contact_email="contact@actionbusiness.com",
        user_id=test_user_owner.id # Link to the owner
    )
    return crud.create_business(db=db_session, business=business_schema)

@pytest.fixture(scope="function")
def test_customer(db_session: Session, test_business: models.Business) -> models.Customer:
    customer_schema = schemas.CustomerCreate(
        customer_name="Action Test Customer",
        email="customer@actiontest.com",
        address="123 Action St",
        business_id=test_business.id # Link to the business
    )
    return crud.create_customer(db=db_session, customer=customer_schema)

@pytest.fixture(scope="function")
def test_debt(db_session: Session, test_customer: models.Customer, test_business: models.Business) -> models.Debt:
    debt_schema = schemas.DebtCreate(
        original_amount=1000.00,
        outstanding_amount=800.00,
        due_date=date(2010, 1, 1), # Significantly in the past to ensure statute-barred check
        status="Overdue",
        customer_id=test_customer.id,
        business_id=test_business.id # Link to the business
    )
    return crud.create_debt(db=db_session, debt=debt_schema)

# --- Tests ---

def test_generate_letter_preview_success(
    client: TestClient,
    test_debt: models.Debt,
    auth_headers: Dict[str, str]
):
    """Test successful letter preview generation."""
    letter_request_data = {"letter_type": "initial_reminder", "state": "NSW"}

    # Mock the actual LLM call within the actions router context
    with patch('app.backend.routers.actions.generate_letter_content', return_value="Mocked letter content from LLM") as mock_llm_call:
        response = client.post(
            f"{API_V1_PREFIX}/actions/debts/{test_debt.id}/generate-letter-preview",
            json=letter_request_data,
            headers=auth_headers
        )

    assert response.status_code == 200
    data = response.json()
    assert data["content"] == "Mocked letter content from LLM"

    mock_llm_call.assert_called_once()
    # You can add more detailed assertions about the arguments passed to mock_llm_call
    # e.g., mock_llm_call.call_args[1]['debt_data']['outstanding_amount'] == str(test_debt.outstanding_amount)


def test_generate_letter_preview_statute_barred_check(
    client: TestClient,
    test_debt: models.Debt, # This debt is >6 years overdue by fixture design
    auth_headers: Dict[str, str]
):
    """Test that the statute-barred check influences the data passed to LLM."""
    letter_request_data = {"letter_type": "formal_demand", "state": "VIC"}

    with patch('app.backend.routers.actions.generate_letter_content', return_value="Statute barred content") as mock_llm_call:
        response = client.post(
            f"{API_V1_PREFIX}/actions/debts/{test_debt.id}/generate-letter-preview",
            json=letter_request_data,
            headers=auth_headers
        )

    assert response.status_code == 200
    mock_llm_call.assert_called_once()
    # Check that 'is_potentially_statute_barred': True was passed in debt_data
    call_args = mock_llm_call.call_args[1] # .kwargs
    assert call_args['debt_data']['is_potentially_statute_barred'] is True


def test_generate_letter_preview_debt_not_found(
    client: TestClient,
    auth_headers: Dict[str, str]
):
    """Test letter preview for a non-existent or unauthorized debt."""
    non_existent_debt_id = 99999
    letter_request_data = {"letter_type": "initial_reminder", "state": "NSW"}

    response = client.post(
        f"{API_V1_PREFIX}/actions/debts/{non_existent_debt_id}/generate-letter-preview",
        json=letter_request_data,
        headers=auth_headers
    )

    assert response.status_code == 403 # Expecting 403 due to get_authorized_business_id check
    # The detail message might vary based on which check fails first (no business vs. debt not found for business)
    # For a user with no businesses, it's "User has no associated businesses."
    # If user has businesses but debt not found for that business_id, it's "Debt not found or not authorized"
    # For this test, the user (test_user_owner) IS created but might not have businesses if fixture isn't used.
    # Let's assume the auth_headers fixture correctly creates a user that *could* have businesses.
    # The error would then be about the specific debt not being found for that user's business context.
    # However, the get_authorized_business_id() is called first in the endpoint.
    # If test_user_owner fixture doesn't create a business for this specific test, it will be 403.
    # The fixture `auth_headers` uses `test_user_owner`. `test_user_owner` itself doesn't create a business.
    # Other fixtures `test_business` do, but this test doesn't depend on `test_business`.
    # So, the user `actionowner` will not have `current_user.businesses` populated.
    assert "User has no associated businesses." in response.json()["detail"]


def test_generate_letter_preview_unauthenticated(client: TestClient, test_debt: models.Debt):
    """Test letter preview without authentication."""
    letter_request_data = {"letter_type": "initial_reminder", "state": "NSW"}
    response = client.post(
        f"{API_V1_PREFIX}/actions/debts/{test_debt.id}/generate-letter-preview",
        json=letter_request_data
    )
    assert response.status_code == 401 # Expecting 401 Unauthorized
    assert "Not authenticated" in response.json()["detail"]
