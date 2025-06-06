import pytest
from sqlalchemy.orm import Session
from decimal import Decimal
from datetime import date, timedelta

from app.backend.core import crud, models, schemas
from pydantic import ValidationError # For testing schema validation

# --- Fixtures for Debt CRUD Tests ---

@pytest.fixture(scope="function")
def test_user_for_debt_crud(db: Session) -> models.User:
    user_data = {"username": "debtcruduser", "email": "debtcrud@example.com", "password": "debtpassword"}
    return crud.create_user(db=db, user=schemas.UserCreate(**user_data))

@pytest.fixture(scope="function")
def test_business_for_debt_crud(db: Session, test_user_for_debt_crud: models.User) -> models.Business:
    return crud.create_business(db=db, business=schemas.BusinessCreate(
        business_name="Debt CRUD Test Biz",
        contact_email="biz.debtcrud@example.com",
        user_id=test_user_for_debt_crud.id
    ))

@pytest.fixture(scope="function")
def test_customer_for_debt_crud(db: Session, test_business_for_debt_crud: models.Business) -> models.Customer:
    return crud.create_customer(db=db, customer=schemas.CustomerCreate(
        customer_name="Debt CRUD Customer",
        email="cust.debtcrud@example.com",
        address="1 Test Rd",
        business_id=test_business_for_debt_crud.id
    ))

@pytest.fixture(scope="function")
def test_debt(db: Session, test_customer_for_debt_crud: models.Customer, test_business_for_debt_crud: models.Business) -> models.Debt:
    debt_data = schemas.DebtCreate(
        original_amount=Decimal("500.00"),
        outstanding_amount=Decimal("400.00"),
        due_date=date.today() - timedelta(days=10),
        status="Overdue",
        debt_type="Invoice",
        invoice_number="INV-DEBTCRUD-001",
        customer_id=test_customer_for_debt_crud.id,
        business_id=test_business_for_debt_crud.id
    )
    return crud.create_debt(db=db, debt=debt_data)

# --- Debt CRUD Tests ---

def test_create_debt(db: Session, test_customer_for_debt_crud: models.Customer, test_business_for_debt_crud: models.Business):
    """Test creating a new debt."""
    debt_data = schemas.DebtCreate(
        original_amount=Decimal("1000.00"),
        outstanding_amount=Decimal("1000.00"),
        due_date=date.today() + timedelta(days=30),
        status="Outstanding",
        debt_type="Service Fee",
        customer_id=test_customer_for_debt_crud.id,
        business_id=test_business_for_debt_crud.id
    )
    created_debt = crud.create_debt(db=db, debt=debt_data)
    assert created_debt is not None
    assert created_debt.original_amount == Decimal("1000.00")
    assert created_debt.status == "Outstanding"
    assert created_debt.id is not None

def test_get_debt_by_id_for_user(db: Session, test_debt: models.Debt, test_user_for_debt_crud: models.User):
    """Test fetching a debt by ID, ensuring user authorization."""
    fetched_debt = crud.get_debt_by_id_for_user(db, debt_id=test_debt.id, user_id=test_user_for_debt_crud.id)
    assert fetched_debt is not None
    assert fetched_debt.id == test_debt.id
    assert fetched_debt.invoice_number == "INV-DEBTCRUD-001"

    # Test with a wrong user_id
    wrong_user_id = test_user_for_debt_crud.id + 99 # Assuming this ID doesn't exist or doesn't own the business
    unauthorized_debt = crud.get_debt_by_id_for_user(db, debt_id=test_debt.id, user_id=wrong_user_id)
    assert unauthorized_debt is None


def test_update_debt_partial(db_session: Session, test_debt: models.Debt):
    """Test partially updating a debt's status and notes."""
    update_data = schemas.DebtUpdate(status="Paid In Part", notes="Partial payment received.", outstanding_amount=Decimal("150.00"))
    updated_debt = crud.update_debt(
        db=db_session,
        debt_id=test_debt.id,
        debt_update=update_data,
        business_id=test_debt.business_id # Required for auth in crud.update_debt
    )
    assert updated_debt is not None
    assert updated_debt.status == "Paid In Part"
    assert updated_debt.notes == "Partial payment received."
    assert updated_debt.outstanding_amount == Decimal("150.00")
    assert updated_debt.original_amount == test_debt.original_amount # Should remain unchanged
    assert updated_debt.debt_type == test_debt.debt_type # Should remain unchanged

def test_archive_debt(db_session: Session, test_debt: models.Debt):
    """Test archiving a debt."""
    assert test_debt.is_archived is False # Pre-condition

    archived_debt = crud.archive_debt(
        db=db_session,
        debt_id=test_debt.id,
        business_id=test_debt.business_id # Required for auth in crud.archive_debt
    )
    assert archived_debt is not None
    assert archived_debt.is_archived is True

    # Fetch again to confirm
    refetched_debt = crud.get_debt_by_id_unscoped(db_session, debt_id=test_debt.id)
    assert refetched_debt is not None
    assert refetched_debt.is_archived is True


def test_debt_schema_amount_validation():
    """Test Pydantic schema validation for debt amounts."""
    # Valid case
    try:
        schemas.DebtCreate(
            original_amount=Decimal("100.00"), outstanding_amount=Decimal("50.00"),
            due_date=date.today(), status="Outstanding", debt_type="Test", customer_id=1, business_id=1
        )
    except ValueError:
        pytest.fail("Valid amounts raised ValueError unexpectedly.")

    # Invalid case: outstanding > original
    with pytest.raises(ValidationError) as excinfo: # Pydantic v2 raises ValidationError containing ValueErrors
        schemas.DebtCreate(
            original_amount=Decimal("100.00"), outstanding_amount=Decimal("150.00"),
            due_date=date.today(), status="Outstanding", debt_type="Test", customer_id=1, business_id=1
        )
    assert "Outstanding amount cannot be greater than original amount." in str(excinfo.value)

    # Test with DebtUpdate schema as well
    try:
        schemas.DebtUpdate(original_amount=Decimal("100.00"), outstanding_amount=Decimal("50.00"))
    except ValueError:
        pytest.fail("Valid update amounts raised ValueError unexpectedly.")

    with pytest.raises(ValidationError) as excinfo_update:
         schemas.DebtUpdate(original_amount=Decimal("100.00"), outstanding_amount=Decimal("150.00"))
    assert "Outstanding amount cannot be greater than original amount." in str(excinfo_update.value)

    # Case where only one is provided (should not trigger validation)
    try:
        schemas.DebtUpdate(outstanding_amount=Decimal("150.00"))
        schemas.DebtUpdate(original_amount=Decimal("100.00"))
    except ValueError:
        pytest.fail("Providing only one amount field raised ValueError unexpectedly.")
