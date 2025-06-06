import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from decimal import Decimal
from datetime import date, timedelta, datetime, timezone
from typing import Dict, List, Optional

from app.backend.core import crud, models, schemas
from app.backend.auth.security import create_access_token

API_V1_PREFIX = "/api/v1"

# --- Helper Functions for Test Data Creation ---
def _create_user(db: Session, user_suffix: str) -> models.User:
    user_data = {"username": f"reportuser{user_suffix}", "email": f"reportuser{user_suffix}@example.com", "password": "reportpassword"}
    return crud.create_user(db=db, user=schemas.UserCreate(**user_data))

def _create_business(db: Session, user: models.User, business_suffix: str) -> models.Business:
    return crud.create_business(db=db, business=schemas.BusinessCreate(
        business_name=f"Report Test Business {business_suffix}", contact_email=f"contact@reportbiz{business_suffix}.com", user_id=user.id
    ))

def _create_customer(db: Session, business: models.Business, customer_suffix: str) -> models.Customer:
    # Ensure unique email for customer to avoid conflicts if tests run in ways that don't fully isolate DB state for this detail
    unique_email = f"cust_report_{customer_suffix}_{datetime.now().timestamp()}@example.com"
    return crud.create_customer(db=db, customer=schemas.CustomerCreate(
        customer_name=f"Report Test Customer {customer_suffix}", email=unique_email,
        address=f"123 Report St {customer_suffix}", business_id=business.id
    ))

def _create_debt(db: Session, customer: models.Customer, business: models.Business, amount: Decimal,
                 due_date: date, status: str, outstanding_amount: Optional[Decimal] = None,
                 is_archived: bool = False, invoice_number_suffix: str = "") -> models.Debt:
    if outstanding_amount is None: outstanding_amount = amount
    inv_num = f"INV-{business.id}-{customer.id}-{datetime.now().timestamp()}-{amount}-{invoice_number_suffix}"
    return crud.create_debt(db=db, debt=schemas.DebtCreate(
        original_amount=amount, outstanding_amount=outstanding_amount, due_date=due_date, status=status,
        customer_id=customer.id, business_id=business.id, is_archived=is_archived, invoice_number=inv_num
    ))

# --- Pytest Fixtures ---
@pytest.fixture(scope="function")
def test_user_reports(db: Session) -> models.User: return _create_user(db, "_reports_main")
@pytest.fixture(scope="function")
def test_user_reports_2(db: Session) -> models.User: return _create_user(db, "_reports_other")

@pytest.fixture(scope="function")
def auth_headers_reports(client: TestClient, test_user_reports: models.User) -> Dict[str, str]:
    login_data = {"username": test_user_reports.username, "password": "reportpassword"}
    response = client.post(f"{API_V1_PREFIX}/auth/token", data=login_data)
    assert response.status_code == 200, f"Login failed for {test_user_reports.username}: {response.text}"
    return {"Authorization": f"Bearer {response.json()['access_token']}"}

@pytest.fixture(scope="function")
def test_business_reports(db: Session, test_user_reports: models.User) -> models.Business:
    return _create_business(db, test_user_reports, "_main")

@pytest.fixture(scope="function")
def test_business_reports_2(db: Session, test_user_reports_2: models.User) -> models.Business:
    return _create_business(db, test_user_reports_2, "_other")

@pytest.fixture(scope="function")
def diverse_debt_data(db: Session, test_business_reports: models.Business):
    today = datetime.now(timezone.utc).date()
    cust1 = _create_customer(db, test_business_reports, "c1_diverse")
    cust2 = _create_customer(db, test_business_reports, "c2_diverse")
    cust3 = _create_customer(db, test_business_reports, "c3_diverse")

    debts = [
        _create_debt(db, cust1, test_business_reports, Decimal("100.00"), today - timedelta(days=90), "Paid", Decimal("0.00"), invoice_number_suffix="d1"),
        _create_debt(db, cust1, test_business_reports, Decimal("200.00"), today - timedelta(days=30), "Overdue", Decimal("200.00"), invoice_number_suffix="d2"),
        _create_debt(db, cust2, test_business_reports, Decimal("300.00"), today - timedelta(days=60), "Overdue", Decimal("300.00"), invoice_number_suffix="d3"),
        _create_debt(db, cust1, test_business_reports, Decimal("400.00"), today + timedelta(days=30), "Outstanding", Decimal("400.00"), invoice_number_suffix="d4"),
        _create_debt(db, cust2, test_business_reports, Decimal("500.00"), today - timedelta(days=10), "Overdue", Decimal("500.00"), is_archived=True, invoice_number_suffix="d5"),
        _create_debt(db, cust3, test_business_reports, Decimal("50.00"), today - timedelta(days=1), "Outstanding", Decimal("50.00"), invoice_number_suffix="d6"),
        _create_debt(db, cust1, test_business_reports, Decimal("250.00"), today - timedelta(days=45), "Disputed", Decimal("250.00"), invoice_number_suffix="d7"),
        _create_debt(db, cust2, test_business_reports, Decimal("75.00"), today, "Outstanding", Decimal("75.00"), invoice_number_suffix="d8"),
        _create_debt(db, cust3, test_business_reports, Decimal("100.00"), today - timedelta(days=5), "Outstanding", Decimal("0.00"), invoice_number_suffix="d9"),
        _create_debt(db, cust2, test_business_reports, Decimal("120.00"), today - timedelta(days=10), "Pending", Decimal("120.00"), invoice_number_suffix="d10")
    ]
    return {"debts": debts, "cust1_id": cust1.id, "cust2_id": cust2.id, "cust3_id": cust3.id}

# --- Tests for GET /reports/summary/{business_id} ---
def test_get_summary_no_debts(client: TestClient, auth_headers_reports: Dict[str, str], test_business_reports: models.Business):
    response = client.get(f"{API_V1_PREFIX}/reports/summary/{test_business_reports.id}", headers=auth_headers_reports)
    assert response.status_code == 200
    data = response.json()
    assert Decimal(data["total_outstanding_debt"]) == Decimal("0.00")
    assert data["overdue_accounts_count"] == 0
    assert data["average_overdue_days"] == 0.0

def test_get_summary_various_debts(client: TestClient, auth_headers_reports: Dict[str, str], test_business_reports: models.Business, diverse_debt_data: dict):
    # Expected Calculations based on NON_PAID_STATUSES and overdue = due_date < today
    # Total Outstanding: Debts 2(200), 3(300), 4(400), 6(50), 7(250), 8(75), 9(0), 10(120). Excludes 1(Paid), 5(Archived).
    expected_total_outstanding = sum([Decimal(x) for x in ["200.00", "300.00", "400.00", "50.00", "250.00", "75.00", "0.00", "120.00"]])
    # Overdue Accounts: Cust1 (Debts 2, 7), Cust2 (Debts 3, 10), Cust3 (Debts 6, 9). Total 3 distinct customers.
    expected_overdue_accounts_count = 3
    # Average Overdue Days: Debts 2(30), 3(60), 6(1), 7(45), 9(5), 10(10). Total 6 debts. Sum of days = 30+60+1+45+5+10 = 151. Avg = 151/6.
    expected_average_overdue_days = 151 / 6.0 if 6 > 0 else 0.0

    response = client.get(f"{API_V1_PREFIX}/reports/summary/{test_business_reports.id}", headers=auth_headers_reports)
    assert response.status_code == 200, response.text
    data = response.json()
    assert Decimal(data["total_outstanding_debt"]) == expected_total_outstanding
    assert data["overdue_accounts_count"] == expected_overdue_accounts_count
    assert abs(data["average_overdue_days"] - expected_average_overdue_days) < 0.01

def test_get_summary_unauthorized(client: TestClient, auth_headers_reports: Dict[str, str], test_business_reports_2: models.Business):
    response = client.get(f"{API_V1_PREFIX}/reports/summary/{test_business_reports_2.id}", headers=auth_headers_reports)
    assert response.status_code == 403
    assert "Not authorized to access reports for this business." in response.json()["detail"]

# --- Tests for GET /reports/debt-status-breakdown/{business_id} ---
def test_get_debt_status_report_no_debts(client: TestClient, auth_headers_reports: Dict[str, str], test_business_reports: models.Business):
    response = client.get(f"{API_V1_PREFIX}/reports/debt-status-breakdown/{test_business_reports.id}", headers=auth_headers_reports)
    assert response.status_code == 200
    data = response.json()
    assert data["status_breakdown"] == []

def test_get_debt_status_report_various_debts(client: TestClient, auth_headers_reports: Dict[str, str], test_business_reports: models.Business, diverse_debt_data: dict):
    response = client.get(f"{API_V1_PREFIX}/reports/debt-status-breakdown/{test_business_reports.id}", headers=auth_headers_reports)
    assert response.status_code == 200, response.text
    data = response.json()["status_breakdown"]

    # Expected: (status: count, sum_of_outstanding_amounts for that status, excluding archived)
    # Debts: 1(Paid,0), 2(Overdue,200), 3(Overdue,300), 4(Outstanding,400),
    #        6(Outstanding,50), 7(Disputed,250), 8(Outstanding,75), 9(Outstanding,0), 10(Pending,120)
    # Debt 5 (Archived, Overdue, 500) is EXCLUDED.
    expected_summary_map = {
        "Paid": {"count": 1, "total_amount": Decimal("0.00")}, # Debt 1
        "Overdue": {"count": 2, "total_amount": Decimal("200.00") + Decimal("300.00")}, # Debts 2, 3
        "Outstanding": {"count": 4, "total_amount": Decimal("400.00") + Decimal("50.00") + Decimal("75.00") + Decimal("0.00")}, # Debts 4, 6, 8, 9
        "Disputed": {"count": 1, "total_amount": Decimal("250.00")},   # Debt 7
        "Pending": {"count": 1, "total_amount": Decimal("120.00")}    # Debt 10
    }

    response_summary_map = {item["status"]: {"count": item["count"], "total_amount": Decimal(item["total_amount"])} for item in data}

    assert len(response_summary_map) == len(expected_summary_map)
    for status_key, expected_values in expected_summary_map.items():
        assert status_key in response_summary_map, f"Status '{status_key}' missing in response."
        assert response_summary_map[status_key]["count"] == expected_values["count"], f"Count mismatch for status '{status_key}'"
        assert response_summary_map[status_key]["total_amount"] == expected_values["total_amount"], f"Total amount mismatch for status '{status_key}'"

def test_get_debt_status_report_unauthorized(client: TestClient, auth_headers_reports: Dict[str, str], test_business_reports_2: models.Business):
    response = client.get(f"{API_V1_PREFIX}/reports/debt-status-breakdown/{test_business_reports_2.id}", headers=auth_headers_reports)
    assert response.status_code == 403
    assert "Not authorized to access reports for this business." in response.json()["detail"]
