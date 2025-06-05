import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from decimal import Decimal
from datetime import date, timedelta, datetime, timezone # Added timezone
from typing import Dict, List, Optional

from app.backend.core import crud, models, schemas
from app.backend.auth.security import create_access_token # For auth_headers

API_V1_PREFIX = "/api/v1" # Consistent with conftest.py

# --- Helper Functions for Test Data Creation ---

def _create_user(db: Session, user_suffix: str) -> models.User:
    user_data = {
        "username": f"reportuser{user_suffix}",
        "email": f"reportuser{user_suffix}@example.com",
        "password": "reportpassword"
    }
    user_schema = schemas.UserCreate(**user_data)
    return crud.create_user(db=db, user=user_schema)

def _create_business(db: Session, user: models.User, business_suffix: str) -> models.Business:
    business_schema = schemas.BusinessCreate(
        business_name=f"Report Test Business {business_suffix}",
        contact_email=f"contact@reportbusiness{business_suffix}.com",
        user_id=user.id
    )
    return crud.create_business(db=db, business=business_schema)

def _create_customer(db: Session, business: models.Business, customer_suffix: str) -> models.Customer:
    customer_schema = schemas.CustomerCreate(
        customer_name=f"Report Test Customer {customer_suffix}",
        email=f"customer_report{customer_suffix}@example.com",
        address=f"123 Report St {customer_suffix}",
        business_id=business.id
    )
    return crud.create_customer(db=db, customer=customer_schema)

def _create_debt(
    db: Session,
    customer: models.Customer,
    business: models.Business,
    amount: Decimal,
    due_date: date,
    status: str,
    outstanding_amount: Optional[Decimal] = None,
    is_archived: bool = False,
    invoice_number: Optional[str] = None
) -> models.Debt:
    if outstanding_amount is None:
        outstanding_amount = amount

    debt_schema = schemas.DebtCreate(
        original_amount=amount,
        outstanding_amount=outstanding_amount,
        due_date=due_date,
        status=status,
        customer_id=customer.id,
        business_id=business.id,
        is_archived=is_archived,
        invoice_number=invoice_number or f"INV-{datetime.now().timestamp()}" # Ensure unique invoice numbers
    )
    return crud.create_debt(db=db, debt=debt_schema)

# --- Pytest Fixtures ---

@pytest.fixture(scope="function")
def test_user_reports(db: Session) -> models.User: # Uses 'db' from conftest.py
    return _create_user(db, "_reports")

@pytest.fixture(scope="function")
def test_user_reports_2(db: Session) -> models.User: # Another user for auth tests
    return _create_user(db, "_reports2")

@pytest.fixture(scope="function")
def auth_headers_reports(client: TestClient, test_user_reports: models.User) -> Dict[str, str]:
    # Need to login the user via the /auth/token endpoint to get a real token
    login_data = {
        "username": test_user_reports.username,
        "password": "reportpassword" # Password used in _create_user
    }
    response = client.post(f"{API_V1_PREFIX}/auth/token", data=login_data)
    assert response.status_code == 200, "Failed to log in test user for reports"
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture(scope="function")
def test_business_reports(db: Session, test_user_reports: models.User) -> models.Business:
    return _create_business(db, test_user_reports, "_reports")

@pytest.fixture(scope="function")
def test_business_reports_2(db: Session, test_user_reports_2: models.User) -> models.Business:
    return _create_business(db, test_user_reports_2, "_reports2")

# --- Tests for GET /reports/summary/{business_id} ---

def test_get_summary_no_debts(client: TestClient, auth_headers_reports: Dict[str, str], test_business_reports: models.Business):
    response = client.get(
        f"{API_V1_PREFIX}/reports/summary/{test_business_reports.id}",
        headers=auth_headers_reports
    )
    assert response.status_code == 200
    data = response.json()
    assert Decimal(data["total_outstanding_debt"]) == Decimal("0.00")
    assert data["overdue_accounts_count"] == 0
    assert data["average_overdue_days"] == 0.0

def test_get_summary_various_debts(client: TestClient, db: Session, auth_headers_reports: Dict[str, str], test_business_reports: models.Business):
    today = datetime.now(timezone.utc).date()
    cust1 = _create_customer(db, test_business_reports, "c1_sum")
    cust2 = _create_customer(db, test_business_reports, "c2_sum")

    # Debt 1: Paid
    _create_debt(db, cust1, test_business_reports, Decimal("100.00"), today - timedelta(days=90), "Paid", Decimal("0.00"))
    # Debt 2: Outstanding, Overdue (30 days)
    _create_debt(db, cust1, test_business_reports, Decimal("200.00"), today - timedelta(days=30), "Overdue", Decimal("200.00"))
    # Debt 3: Outstanding, Overdue (60 days) - different customer
    _create_debt(db, cust2, test_business_reports, Decimal("300.00"), today - timedelta(days=60), "Overdue", Decimal("300.00"))
    # Debt 4: Outstanding, Not Overdue yet
    _create_debt(db, cust2, test_business_reports, Decimal("400.00"), today + timedelta(days=30), "Outstanding", Decimal("400.00"))
    # Debt 5: Archived, Overdue (would count if not archived)
    _create_debt(db, cust1, test_business_reports, Decimal("500.00"), today - timedelta(days=10), "Overdue", Decimal("500.00"), is_archived=True)
    # Debt 6: Outstanding, Overdue (0 days, due today but not paid) - this counts as overdue by "< today" logic in CRUD
    # Let's make it 1 day overdue for clarity
    _create_debt(db, cust2, test_business_reports, Decimal("50.00"), today - timedelta(days=1), "Outstanding", Decimal("50.00"))


    expected_total_outstanding = Decimal("200.00") + Decimal("300.00") + Decimal("400.00") + Decimal("50.00") # Debts 2, 3, 4, 6
    expected_overdue_accounts_count = 2 # cust1 (for debt 2) and cust2 (for debt 3 and 6)
    expected_average_overdue_days = (30 + 60 + 1) / 3.0 # Debts 2, 3, 6

    response = client.get(
        f"{API_V1_PREFIX}/reports/summary/{test_business_reports.id}",
        headers=auth_headers_reports
    )
    assert response.status_code == 200
    data = response.json()

    assert Decimal(data["total_outstanding_debt"]) == expected_total_outstanding
    assert data["overdue_accounts_count"] == expected_overdue_accounts_count
    assert abs(data["average_overdue_days"] - expected_average_overdue_days) < 0.01 # Using tolerance for float comparison

def test_get_summary_unauthorized(client: TestClient, auth_headers_reports: Dict[str, str], test_business_reports_2: models.Business):
    response = client.get(
        f"{API_V1_PREFIX}/reports/summary/{test_business_reports_2.id}", # Accessing business of user 2
        headers=auth_headers_reports # Using token of user 1
    )
    assert response.status_code == 403 # Or 404 depending on specific check order in endpoint
    # The current reports endpoint doesn't have explicit ownership check, relies on business_id passed.
    # The get_current_active_user authenticates, but the endpoint itself doesn't check if business_id belongs to user.
    # This should be updated in the endpoint if strict ownership is required for reports.
    # For now, assuming it *would* pass if data existed, or fail if business_id is simply not found by CRUDs (which is fine).
    # Let's assume the report functions correctly scope by business_id, so if the business_id is valid, it returns data for it.
    # The "unauthorized" part here would mean the user cannot see *any* report if they don't own the business_id.
    # This test needs the endpoint to implement an ownership check.
    # If the endpoint doesn't have an ownership check, it would return 200 with data for test_business_reports_2.
    # Given the current structure of reports router, it does not perform an ownership check on business_id vs current_user.
    # So, this test will likely pass with 200 unless we modify the endpoint.
    # For this subtask, I'll assume the endpoint *should* have this check.
    # Let's add a temporary pass for now and note this needs endpoint update.
    # pytest.skip("Skipping until report endpoint implements business ownership check for current_user")
    # If the endpoint is expected to just use business_id, then 200 is fine.
    # The current setup: reports router doesn't use current_user. Let's test it as is.
    # It will return a 200 with 0 values for the other user's business if it has no debts.
    # UPDATE: Now that ownership check is added to the endpoint, we expect 403.
    assert response.status_code == 403
    assert "Not authorized to access reports for this business." in response.json()["detail"]


# --- Tests for GET /reports/debt-status-breakdown/{business_id} ---

def test_get_debt_status_report_no_debts(client: TestClient, auth_headers_reports: Dict[str, str], test_business_reports: models.Business):
    response = client.get(
        f"{API_V1_PREFIX}/reports/debt-status-breakdown/{test_business_reports.id}",
        headers=auth_headers_reports
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status_breakdown"] == []

def test_get_debt_status_report_various_debts(client: TestClient, db: Session, auth_headers_reports: Dict[str, str], test_business_reports: models.Business):
    today = datetime.now(timezone.utc).date()
    cust1 = _create_customer(db, test_business_reports, "c1_stat")
    cust2 = _create_customer(db, test_business_reports, "c2_stat")

    _create_debt(db, cust1, test_business_reports, Decimal("100"), today - timedelta(days=10), "Paid", Decimal("0.00"))
    _create_debt(db, cust1, test_business_reports, Decimal("200"), today - timedelta(days=20), "Overdue")
    _create_debt(db, cust2, test_business_reports, Decimal("300"), today - timedelta(days=30), "Overdue")
    _create_debt(db, cust1, test_business_reports, Decimal("400"), today + timedelta(days=10), "Outstanding")
    _create_debt(db, cust2, test_business_reports, Decimal("500"), today - timedelta(days=5), "Disputed")
    _create_debt(db, cust1, test_business_reports, Decimal("600"), today - timedelta(days=15), "Overdue", is_archived=True) # Archived, should be excluded

    response = client.get(
        f"{API_V1_PREFIX}/reports/debt-status-breakdown/{test_business_reports.id}",
        headers=auth_headers_reports
    )
    assert response.status_code == 200
    data = response.json()["status_breakdown"]

    expected_summary = {
        "Paid": {"count": 1, "total_amount": Decimal("0.00")}, # Outstanding amount for paid is 0
        "Overdue": {"count": 2, "total_amount": Decimal("200.00") + Decimal("300.00")},
        "Outstanding": {"count": 1, "total_amount": Decimal("400.00")},
        "Disputed": {"count": 1, "total_amount": Decimal("500.00")}
    }

    response_summary = {item["status"]: {"count": item["count"], "total_amount": Decimal(item["total_amount"])} for item in data}

    assert len(data) == len(expected_summary) # Ensure no extra statuses
    for status, values in expected_summary.items():
        assert status in response_summary
        assert response_summary[status]["count"] == values["count"]
        assert response_summary[status]["total_amount"] == values["total_amount"]

def test_get_debt_status_report_unauthorized(client: TestClient, auth_headers_reports: Dict[str, str], test_business_reports_2: models.Business):
    response = client.get(
        f"{API_V1_PREFIX}/reports/debt-status-breakdown/{test_business_reports_2.id}",
        headers=auth_headers_reports
    )
    # See comment in test_get_summary_unauthorized. Expect 200 if endpoint doesn't check business ownership against current_user.
    # UPDATE: Now that ownership check is added to the endpoint, we expect 403.
    assert response.status_code == 403
    assert "Not authorized to access reports for this business." in response.json()["detail"]
