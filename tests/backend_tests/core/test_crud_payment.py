import pytest
from sqlalchemy.orm import Session
from app.backend.core import crud
from app.backend.core.models import Debt, Payment
from app.backend.core.schemas import PaymentCreate, PaymentUpdate
from datetime import date, timedelta, timezone, datetime
from decimal import Decimal

# Fixtures - these would ideally be in conftest.py but placing them here for simplicity
# based on the prompt structure. Assuming conftest.py provides `db` session.

@pytest.fixture
def test_user(db: Session):
    return crud.create_user(db, username="paymentuser", email="payment@example.com", password="password")

@pytest.fixture
def test_business(db: Session, test_user):
    return crud.create_business(db, name="Payment Test Corp", user_id=test_user.id)

@pytest.fixture
def test_customer(db: Session, test_business):
    return crud.create_customer(db, business_id=test_business.id, name="John Doe", email="john.doe@example.com")

@pytest.fixture
def test_debt(db: Session, test_customer):
    debt_data = {
        "customer_id": test_customer.id,
        "original_amount": Decimal("100.00"),
        "outstanding_amount": Decimal("100.00"),
        "due_date": date.today() - timedelta(days=10),
        "status": "Outstanding",
        "service_description": "Initial service"
    }
    return crud.create_debt(db, **debt_data)

# --- CRUD Tests for Payment ---

def test_create_payment_updates_debt_to_partial(db: Session, test_debt: Debt):
    payment_data = PaymentCreate(debt_id=test_debt.id, amount_paid=Decimal("50.00"), payment_date=date.today())
    payment = crud.create_payment(db, payment_data)
    db.refresh(test_debt)

    assert payment is not None
    assert payment.debt_id == test_debt.id
    assert payment.amount_paid == Decimal("50.00")
    assert test_debt.outstanding_amount == Decimal("50.00")
    assert test_debt.status == "Partially Paid"

def test_create_payment_updates_debt_to_paid(db: Session, test_debt: Debt):
    payment_data = PaymentCreate(debt_id=test_debt.id, amount_paid=Decimal("100.00"), payment_date=date.today())
    payment = crud.create_payment(db, payment_data)
    db.refresh(test_debt)

    assert payment is not None
    assert payment.amount_paid == Decimal("100.00")
    assert test_debt.outstanding_amount == Decimal("0.00")
    assert test_debt.status == "Paid"

def test_create_another_payment_on_paid_debt(db: Session, test_debt: Debt):
    # First payment makes it Paid
    crud.create_payment(db, PaymentCreate(debt_id=test_debt.id, amount_paid=Decimal("100.00"), payment_date=date.today()))
    db.refresh(test_debt)
    assert test_debt.status == "Paid"
    assert test_debt.outstanding_amount == Decimal("0.00")

    # Second payment
    payment_data = PaymentCreate(debt_id=test_debt.id, amount_paid=Decimal("10.00"), payment_date=date.today())
    payment2 = crud.create_payment(db, payment_data) # Should still create payment
    db.refresh(test_debt)
    db.refresh(payment2)

    assert payment2 is not None
    assert payment2.amount_paid == Decimal("10.00")
    # Outstanding amount should ideally not go negative if business logic prevents overpayment adjustment.
    # Current CRUD handles this by just adding payment and reducing outstanding.
    # If outstanding_amount is already 0, it will become negative.
    # Let's assume for now the task implies it just records the payment and outstanding stays 0 or goes negative.
    # Based on current crud.create_payment, it will go negative.
    assert test_debt.outstanding_amount == Decimal("-10.00")
    assert test_debt.status == "Paid" # Status should remain "Paid" or perhaps "Overpaid" if that status exists

def test_create_payment_for_archived_debt_fails(db: Session, test_debt: Debt):
    crud.archive_debt(db, test_debt.id) # Archive the debt
    db.refresh(test_debt)
    assert test_debt.is_archived is True

    payment_data = PaymentCreate(debt_id=test_debt.id, amount_paid=Decimal("10.00"), payment_date=date.today())

    with pytest.raises(ValueError) as excinfo:
        crud.create_payment(db, payment_data)
    assert "Cannot add payment to an archived debt" in str(excinfo.value)

    # Verify debt status hasn't changed
    db.refresh(test_debt)
    assert test_debt.outstanding_amount == Decimal("100.00") # Original amount
    assert test_debt.status == "Outstanding" # Status before archive

def test_create_payment_for_non_existent_debt_fails(db: Session):
    non_existent_debt_id = 99999
    payment_data = PaymentCreate(debt_id=non_existent_debt_id, amount_paid=Decimal("10.00"), payment_date=date.today())

    with pytest.raises(ValueError) as excinfo: # Assuming CRUD raises ValueError for not found debt
        crud.create_payment(db, payment_data)
    assert "Debt not found" in str(excinfo.value) # Or similar error from get_debt_by_id_unscoped

def test_create_payment_negative_amount_fails(db: Session, test_debt: Debt):
    # This should be caught by Pydantic schema (PaymentCreate.amount_paid > 0)
    # If not, CRUD should ideally also check. For now, assuming Pydantic handles it.
    # If PaymentCreate allows negative, then this test is for CRUD's specific check.
    # Based on `PaymentBase` schema, `amount_paid` must be positive.
    # So, this test primarily tests Pydantic validation before CRUD, not a CRUD specific check.
    # If we want to test CRUD specifically, we'd bypass Pydantic.
    with pytest.raises(ValueError): # Pydantic's ValidationError
         PaymentCreate(debt_id=test_debt.id, amount_paid=Decimal("-10.00"), payment_date=date.today())

    # To test CRUD specifically (if it had a redundant check, which it doesn't for this):
    # payment_data = {"debt_id":test_debt.id, "amount_paid": Decimal("-10.00"), "payment_date":date.today()}
    # with pytest.raises(ValueError) as excinfo:
    #     # Hypothetically, if crud.create_payment took dict and did its own validation
    #     crud.create_payment(db, MagicMock(spec=PaymentCreate, **payment_data))
    # assert "Payment amount must be positive" in str(excinfo.value)


def test_get_payment_and_list_for_debt(db: Session, test_debt: Debt):
    p1_data = PaymentCreate(debt_id=test_debt.id, amount_paid=Decimal("20.00"), payment_date=date.today() - timedelta(days=2))
    p2_data = PaymentCreate(debt_id=test_debt.id, amount_paid=Decimal("30.00"), payment_date=date.today() - timedelta(days=1))
    p1 = crud.create_payment(db, p1_data)
    p2 = crud.create_payment(db, p2_data)

    retrieved_p1 = crud.get_payment(db, p1.id)
    assert retrieved_p1 is not None
    assert retrieved_p1.id == p1.id
    assert retrieved_p1.amount_paid == Decimal("20.00")

    payments_for_debt = crud.get_payments_for_debt(db, test_debt.id)
    assert len(payments_for_debt) == 2
    payment_ids = {p.id for p in payments_for_debt}
    assert p1.id in payment_ids
    assert p2.id in payment_ids

def test_update_payment_amount_increases_debt_outstanding(db: Session, test_debt: Debt):
    payment = crud.create_payment(db, PaymentCreate(debt_id=test_debt.id, amount_paid=Decimal("50.00"), payment_date=date.today()))
    db.refresh(test_debt)
    assert test_debt.outstanding_amount == Decimal("50.00")
    assert test_debt.status == "Partially Paid"

    # Update payment to a smaller amount (e.g., refund processed, payment amount reduced)
    payment_update_data = PaymentUpdate(amount_paid=Decimal("30.00"))
    updated_payment = crud.update_payment(db, payment_id=payment.id, payment_update=payment_update_data)
    db.refresh(test_debt)
    db.refresh(updated_payment)

    assert updated_payment.amount_paid == Decimal("30.00")
    assert test_debt.outstanding_amount == Decimal("70.00") # 100 - 30
    assert test_debt.status == "Partially Paid"

def test_update_payment_amount_decreases_debt_outstanding_and_pays_off(db: Session, test_debt: Debt):
    payment = crud.create_payment(db, PaymentCreate(debt_id=test_debt.id, amount_paid=Decimal("30.00"), payment_date=date.today()))
    db.refresh(test_debt)
    assert test_debt.outstanding_amount == Decimal("70.00")
    assert test_debt.status == "Partially Paid"

    # Update payment to a larger amount, paying off the debt
    payment_update_data = PaymentUpdate(amount_paid=Decimal("100.00"))
    updated_payment = crud.update_payment(db, payment_id=payment.id, payment_update=payment_update_data)
    db.refresh(test_debt)
    db.refresh(updated_payment)

    assert updated_payment.amount_paid == Decimal("100.00")
    assert test_debt.outstanding_amount == Decimal("0.00")
    assert test_debt.status == "Paid"

def test_update_payment_amount_results_in_overpayment(db: Session, test_debt: Debt):
    payment = crud.create_payment(db, PaymentCreate(debt_id=test_debt.id, amount_paid=Decimal("30.00"), payment_date=date.today()))
    db.refresh(test_debt) # outstanding = 70

    payment_update_data = PaymentUpdate(amount_paid=Decimal("120.00")) # Original debt 100
    updated_payment = crud.update_payment(db, payment_id=payment.id, payment_update=payment_update_data)
    db.refresh(test_debt)
    db.refresh(updated_payment)

    assert updated_payment.amount_paid == Decimal("120.00")
    assert test_debt.outstanding_amount == Decimal("-20.00") # 100 (original) - 120 (new total payment)
    assert test_debt.status == "Paid" # Or "Overpaid"

def test_update_payment_non_amount_fields(db: Session, test_debt: Debt):
    payment = crud.create_payment(db, PaymentCreate(debt_id=test_debt.id, amount_paid=Decimal("50.00"), payment_date=date.today(), payment_method="Card"))
    db.refresh(test_debt)
    initial_outstanding = test_debt.outstanding_amount

    new_date = date.today() - timedelta(days=5)
    new_method = "Bank Transfer"
    new_notes = "Updated notes"
    payment_update_data = PaymentUpdate(payment_date=new_date, payment_method=new_method, notes=new_notes)

    updated_payment = crud.update_payment(db, payment_id=payment.id, payment_update=payment_update_data)
    db.refresh(test_debt) # Refresh debt to ensure outstanding amount hasn't changed
    db.refresh(updated_payment)

    assert updated_payment.payment_date == new_date
    assert updated_payment.payment_method == new_method
    assert updated_payment.notes == new_notes
    assert updated_payment.amount_paid == Decimal("50.00") # Amount not changed
    assert test_debt.outstanding_amount == initial_outstanding # Outstanding amount unchanged

def test_update_non_existent_payment_fails(db: Session):
    payment_update_data = PaymentUpdate(amount_paid=Decimal("10.00"))
    with pytest.raises(ValueError) as excinfo: # Assuming crud.update_payment raises ValueError for not found
        crud.update_payment(db, payment_id=9999, payment_update=payment_update_data)
    assert "Payment not found" in str(excinfo.value)


def test_delete_payment_restores_debt_outstanding(db: Session, test_debt: Debt):
    payment = crud.create_payment(db, PaymentCreate(debt_id=test_debt.id, amount_paid=Decimal("60.00"), payment_date=date.today()))
    db.refresh(test_debt)
    assert test_debt.outstanding_amount == Decimal("40.00")
    assert test_debt.status == "Partially Paid"

    crud.delete_payment(db, payment_id=payment.id)
    db.refresh(test_debt)

    assert test_debt.outstanding_amount == Decimal("100.00") # Restored to original
    assert test_debt.status == "Outstanding" # Status restored

def test_delete_payment_changes_debt_status_from_paid(db: Session, test_debt: Debt):
    payment = crud.create_payment(db, PaymentCreate(debt_id=test_debt.id, amount_paid=Decimal("100.00"), payment_date=date.today()))
    db.refresh(test_debt)
    assert test_debt.outstanding_amount == Decimal("0.00")
    assert test_debt.status == "Paid"

    crud.delete_payment(db, payment_id=payment.id)
    db.refresh(test_debt)

    assert test_debt.outstanding_amount == Decimal("100.00")
    assert test_debt.status == "Outstanding"

def test_delete_multiple_payments_correctly_adjusts_debt(db: Session, test_debt: Debt):
    p1 = crud.create_payment(db, PaymentCreate(debt_id=test_debt.id, amount_paid=Decimal("30.00"), payment_date=date.today()))
    db.refresh(test_debt) # outstanding = 70
    p2 = crud.create_payment(db, PaymentCreate(debt_id=test_debt.id, amount_paid=Decimal("40.00"), payment_date=date.today()))
    db.refresh(test_debt) # outstanding = 30, status = Partially Paid

    assert test_debt.outstanding_amount == Decimal("30.00")
    assert test_debt.status == "Partially Paid"

    # Delete p2
    crud.delete_payment(db, payment_id=p2.id)
    db.refresh(test_debt)
    assert test_debt.outstanding_amount == Decimal("70.00") # 100 - 30 (p1)
    assert test_debt.status == "Partially Paid"

    # Delete p1
    crud.delete_payment(db, payment_id=p1.id)
    db.refresh(test_debt)
    assert test_debt.outstanding_amount == Decimal("100.00") # 100 - 0
    assert test_debt.status == "Outstanding"


def test_delete_non_existent_payment_fails(db: Session):
    with pytest.raises(ValueError) as excinfo:
        crud.delete_payment(db, payment_id=9999)
    assert "Payment not found" in str(excinfo.value)

def test_update_payment_on_archived_debt_fails(db: Session, test_debt: Debt):
    payment = crud.create_payment(db, PaymentCreate(debt_id=test_debt.id, amount_paid=Decimal("10.00"), payment_date=date.today()))
    db.refresh(test_debt)

    crud.archive_debt(db, test_debt.id)
    db.refresh(test_debt)
    assert test_debt.is_archived

    payment_update_data = PaymentUpdate(amount_paid=Decimal("20.00"))
    with pytest.raises(ValueError) as excinfo:
        crud.update_payment(db, payment_id=payment.id, payment_update=payment_update_data)
    assert "Cannot update payment for an archived debt" in str(excinfo.value)

def test_delete_payment_on_archived_debt_fails(db: Session, test_debt: Debt):
    payment = crud.create_payment(db, PaymentCreate(debt_id=test_debt.id, amount_paid=Decimal("10.00"), payment_date=date.today()))
    db.refresh(test_debt)

    crud.archive_debt(db, test_debt.id)
    db.refresh(test_debt)
    assert test_debt.is_archived

    with pytest.raises(ValueError) as excinfo:
        crud.delete_payment(db, payment_id=payment.id)
    assert "Cannot delete payment for an archived debt" in str(excinfo.value)

# Consider edge case: What if a debt is paid, then a payment is updated to be less, making it partially paid?
def test_update_payment_changes_status_from_paid_to_partially_paid(db: Session, test_debt: Debt):
    payment = crud.create_payment(db, PaymentCreate(debt_id=test_debt.id, amount_paid=Decimal("100.00"), payment_date=date.today()))
    db.refresh(test_debt)
    assert test_debt.status == "Paid"
    assert test_debt.outstanding_amount == Decimal("0.00")

    payment_update_data = PaymentUpdate(amount_paid=Decimal("80.00"))
    crud.update_payment(db, payment_id=payment.id, payment_update=payment_update_data)
    db.refresh(test_debt)

    assert test_debt.outstanding_amount == Decimal("20.00")
    assert test_debt.status == "Partially Paid"

# Test for payment_method and notes updates in PaymentUpdate
def test_update_payment_only_metadata(db: Session, test_debt: Debt):
    payment = crud.create_payment(db, PaymentCreate(
        debt_id=test_debt.id,
        amount_paid=Decimal("50.00"),
        payment_date=date.today(),
        payment_method="Cash",
        notes="Initial payment"
    ))
    db.refresh(test_debt)
    assert test_debt.outstanding_amount == Decimal("50.00")

    new_payment_method = "Credit Card"
    new_notes = "Updated payment details"
    update_schema = PaymentUpdate(payment_method=new_payment_method, notes=new_notes)

    updated_payment = crud.update_payment(db, payment_id=payment.id, payment_update=update_schema)
    db.refresh(updated_payment)
    db.refresh(test_debt)

    assert updated_payment.payment_method == new_payment_method
    assert updated_payment.notes == new_notes
    assert updated_payment.amount_paid == Decimal("50.00") # Ensure amount didn't change
    assert test_debt.outstanding_amount == Decimal("50.00") # Ensure debt outstanding amount is still correct
    assert test_debt.status == "Partially Paid"

# Test for payment date update
def test_update_payment_date(db: Session, test_debt: Debt):
    initial_date = date.today()
    payment = crud.create_payment(db, PaymentCreate(
        debt_id=test_debt.id,
        amount_paid=Decimal("50.00"),
        payment_date=initial_date
    ))
    db.refresh(test_debt)
    assert test_debt.outstanding_amount == Decimal("50.00")

    new_payment_date = date.today() - timedelta(days=5)
    update_schema = PaymentUpdate(payment_date=new_payment_date)

    updated_payment = crud.update_payment(db, payment_id=payment.id, payment_update=update_schema)
    db.refresh(updated_payment)
    db.refresh(test_debt)

    assert updated_payment.payment_date == new_payment_date
    assert updated_payment.amount_paid == Decimal("50.00") # Ensure amount didn't change
    assert test_debt.outstanding_amount == Decimal("50.00") # Ensure debt outstanding amount is still correct

# Test creation of payment with all fields
def test_create_payment_all_fields(db: Session, test_debt: Debt):
    payment_data = PaymentCreate(
        debt_id=test_debt.id,
        amount_paid=Decimal("75.00"),
        payment_date=date.today(),
        payment_method="Online Transfer",
        notes="Regular monthly payment"
    )
    payment = crud.create_payment(db, payment_data)
    db.refresh(payment)
    db.refresh(test_debt)

    assert payment.debt_id == test_debt.id
    assert payment.amount_paid == Decimal("75.00")
    assert payment.payment_date == date.today()
    assert payment.payment_method == "Online Transfer"
    assert payment.notes == "Regular monthly payment"
    assert payment.created_at is not None
    assert payment.updated_at is not None
    assert test_debt.outstanding_amount == Decimal("25.00")
    assert test_debt.status == "Partially Paid"

# Test updating a payment to zero (should this be allowed? if so, how does it affect debt?)
# Current schema PaymentUpdate allows amount_paid to be 0 if PaymentBase allows it.
# PaymentBase requires amount_paid > 0. So PaymentUpdate for amount_paid = 0 will fail at Pydantic level.
# If PaymentBase allowed amount_paid >= 0, then this test would be relevant for CRUD.
# For now, this will fail at Pydantic schema validation.
def test_update_payment_amount_to_zero_fails_schema(db: Session, test_debt: Debt):
     payment = crud.create_payment(db, PaymentCreate(debt_id=test_debt.id, amount_paid=Decimal("50.00"), payment_date=date.today()))
     db.refresh(test_debt)
     assert test_debt.outstanding_amount == Decimal("50.00")

     with pytest.raises(ValueError): # Pydantic validation error
         PaymentUpdate(amount_paid=Decimal("0.00"))

# Test that server_default for created_at and updated_at are working
def test_payment_timestamps(db: Session, test_debt: Debt):
    payment_data = PaymentCreate(debt_id=test_debt.id, amount_paid=Decimal("10.00"), payment_date=date.today())
    payment = crud.create_payment(db, payment_data)
    db.refresh(payment)

    assert payment.created_at is not None
    assert payment.updated_at is not None
    assert isinstance(payment.created_at, datetime)
    assert isinstance(payment.updated_at, datetime)
    # Check if they are timezone-aware (if your DB stores them as such)
    # For SQLite, they might be naive if not handled explicitly by SQLAlchemy TypeDecorator
    # But our model uses DateTime(timezone=True)
    if db.bind.dialect.name != "sqlite": # SQLite does not natively support timezone=True for CURRENT_TIMESTAMP
        assert payment.created_at.tzinfo is not None
        assert payment.updated_at.tzinfo is not None

    old_updated_at = payment.updated_at

    # Perform an update
    payment_update_data = PaymentUpdate(notes="A small update")
    updated_payment = crud.update_payment(db, payment_id=payment.id, payment_update=payment_update_data)
    db.refresh(updated_payment)

    assert updated_payment.updated_at is not None
    assert updated_payment.updated_at > old_updated_at
    if db.bind.dialect.name != "sqlite":
         assert updated_payment.updated_at.tzinfo is not None
    assert updated_payment.created_at == payment.created_at # created_at should not change

# Ensure that when a debt is fully paid by multiple payments, its status is "Paid"
def test_multiple_payments_lead_to_paid_status(db: Session, test_debt: Debt):
    crud.create_payment(db, PaymentCreate(debt_id=test_debt.id, amount_paid=Decimal("30.00"), payment_date=date.today()))
    db.refresh(test_debt)
    assert test_debt.status == "Partially Paid"
    assert test_debt.outstanding_amount == Decimal("70.00")

    crud.create_payment(db, PaymentCreate(debt_id=test_debt.id, amount_paid=Decimal("70.00"), payment_date=date.today()))
    db.refresh(test_debt)
    assert test_debt.status == "Paid"
    assert test_debt.outstanding_amount == Decimal("0.00")

# Ensure that if a payment makes the debt overpaid, the status is still "Paid" (or "Overpaid" if implemented)
def test_overpayment_keeps_status_paid(db: Session, test_debt: Debt):
    crud.create_payment(db, PaymentCreate(debt_id=test_debt.id, amount_paid=Decimal("120.00"), payment_date=date.today()))
    db.refresh(test_debt)
    assert test_debt.status == "Paid" # Assuming no "Overpaid" status for now
    assert test_debt.outstanding_amount == Decimal("-20.00")

# Test that deleting a payment from an overpaid debt correctly adjusts outstanding amount and status
def test_delete_payment_from_overpaid_debt(db: Session, test_debt: Debt):
    payment = crud.create_payment(db, PaymentCreate(debt_id=test_debt.id, amount_paid=Decimal("120.00"), payment_date=date.today()))
    db.refresh(test_debt)
    assert test_debt.status == "Paid"
    assert test_debt.outstanding_amount == Decimal("-20.00")

    crud.delete_payment(db, payment_id=payment.id)
    db.refresh(test_debt)
    assert test_debt.outstanding_amount == Decimal("100.00") # Back to original
    assert test_debt.status == "Outstanding"

# Test updating a payment that results in the debt status changing from Paid to Partially Paid
def test_update_payment_changes_debt_from_paid_to_partially_paid(db: Session, test_debt: Debt):
    payment = crud.create_payment(db, PaymentCreate(debt_id=test_debt.id, amount_paid=Decimal("100.00"), payment_date=date.today()))
    db.refresh(test_debt)
    assert test_debt.status == "Paid"
    assert test_debt.outstanding_amount == Decimal("0.00")

    payment_update = PaymentUpdate(amount_paid=Decimal("70.00"))
    crud.update_payment(db, payment_id=payment.id, payment_update=payment_update)
    db.refresh(test_debt)

    assert test_debt.outstanding_amount == Decimal("30.00")
    assert test_debt.status == "Partially Paid"

# Test updating a payment that results in the debt status changing from Partially Paid to Paid
def test_update_payment_changes_debt_from_partially_paid_to_paid(db: Session, test_debt: Debt):
    payment = crud.create_payment(db, PaymentCreate(debt_id=test_debt.id, amount_paid=Decimal("70.00"), payment_date=date.today()))
    db.refresh(test_debt)
    assert test_debt.status == "Partially Paid"
    assert test_debt.outstanding_amount == Decimal("30.00")

    payment_update = PaymentUpdate(amount_paid=Decimal("100.00")) # This is the new total for this payment
    crud.update_payment(db, payment_id=payment.id, payment_update=payment_update)
    db.refresh(test_debt)

    # The debt's outstanding amount is original_amount - SUM(all payments)
    # If original debt = 100, payment was 70. Debt outstanding = 30.
    # Payment is updated to 100. Debt outstanding = 100 - 100 = 0.
    assert test_debt.outstanding_amount == Decimal("0.00")
    assert test_debt.status == "Paid"

# Test payment interactions when debt has other payments
def test_update_payment_with_sibling_payments(db: Session, test_debt: Debt):
    # Initial debt: 100
    p1 = crud.create_payment(db, PaymentCreate(debt_id=test_debt.id, amount_paid=Decimal("20.00"), payment_date=date.today()))
    db.refresh(test_debt) # Outstanding: 80
    p2 = crud.create_payment(db, PaymentCreate(debt_id=test_debt.id, amount_paid=Decimal("30.00"), payment_date=date.today()))
    db.refresh(test_debt) # Outstanding: 50. Status: Partially Paid

    assert test_debt.outstanding_amount == Decimal("50.00")

    # Update p1 from 20 to 40 (increase of 20)
    payment_update_p1 = PaymentUpdate(amount_paid=Decimal("40.00"))
    crud.update_payment(db, payment_id=p1.id, payment_update=payment_update_p1)
    db.refresh(test_debt)

    # Total paid: p1 (40) + p2 (30) = 70. Outstanding: 100 - 70 = 30
    assert test_debt.outstanding_amount == Decimal("30.00")
    assert test_debt.status == "Partially Paid"

    # Update p2 from 30 to 70, making total paid 40 (p1) + 70 (p2) = 110
    payment_update_p2 = PaymentUpdate(amount_paid=Decimal("70.00"))
    crud.update_payment(db, payment_id=p2.id, payment_update=payment_update_p2)
    db.refresh(test_debt)

    # Total paid: p1 (40) + p2 (70) = 110. Outstanding: 100 - 110 = -10
    assert test_debt.outstanding_amount == Decimal("-10.00")
    assert test_debt.status == "Paid"


def test_delete_payment_with_sibling_payments(db: Session, test_debt: Debt):
    # Initial debt: 100
    p1 = crud.create_payment(db, PaymentCreate(debt_id=test_debt.id, amount_paid=Decimal("20.00"), payment_date=date.today()))
    db.refresh(test_debt) # Outstanding: 80
    p2 = crud.create_payment(db, PaymentCreate(debt_id=test_debt.id, amount_paid=Decimal("30.00"), payment_date=date.today()))
    db.refresh(test_debt) # Outstanding: 50. Status: Partially Paid
    p3 = crud.create_payment(db, PaymentCreate(debt_id=test_debt.id, amount_paid=Decimal("50.00"), payment_date=date.today()))
    db.refresh(test_debt) # Outstanding: 0. Status: Paid

    assert test_debt.outstanding_amount == Decimal("0.00")
    assert test_debt.status == "Paid"

    # Delete p2 (amount 30)
    crud.delete_payment(db, payment_id=p2.id)
    db.refresh(test_debt)
    # Remaining payments: p1 (20) + p3 (50) = 70. Outstanding: 100 - 70 = 30
    assert test_debt.outstanding_amount == Decimal("30.00")
    assert test_debt.status == "Partially Paid"

    # Delete p3 (amount 50)
    crud.delete_payment(db, payment_id=p3.id)
    db.refresh(test_debt)
    # Remaining payments: p1 (20). Outstanding: 100 - 20 = 80
    assert test_debt.outstanding_amount == Decimal("80.00")
    assert test_debt.status == "Partially Paid"

    # Delete p1 (amount 20)
    crud.delete_payment(db, payment_id=p1.id)
    db.refresh(test_debt)
    # Remaining payments: 0. Outstanding: 100 - 0 = 100
    assert test_debt.outstanding_amount == Decimal("100.00")
    assert test_debt.status == "Outstanding"

# Make sure conftest.py has the db fixture
# For these tests to run, ensure `app.backend.core.models.Payment` and related `Debt` updates are implemented.
# Also, `PaymentCreate` and `PaymentUpdate` schemas should be defined with `amount_paid: Decimal = Field(gt=0)`.
# The CRUD functions `create_payment`, `get_payment`, `get_payments_for_debt`, `update_payment`, `delete_payment`
# need to be fully implemented as per the project summary.
# Specifically, `crud.archive_debt` is used, assuming it sets `is_archived=True`.
# `get_debt_by_id_unscoped` is assumed to be used by `create_payment` to find the debt.
# ValueError is the assumed exception for "not found" or business logic violations in CRUD.
# The `Payment` model in `core.models` should have `amount_paid = Column(Numeric(10, 2), nullable=False)`.
# `Debt` model should have `original_amount = Column(Numeric(10, 2), nullable=False)`.
# `Debt` model should have `outstanding_amount = Column(Numeric(10, 2), nullable=False)`.
# `Debt` model should have `status = Column(String, default="Outstanding")`.
# `Debt` model should have `is_archived = Column(Boolean, default=False)`.
# `PaymentCreate` should have `debt_id: int`, `amount_paid: Decimal = Field(gt=0)`, `payment_date: date`, etc.
# `PaymentUpdate` should have optional fields, and `amount_paid: Optional[Decimal] = Field(None, gt=0)`.
# The `server_default=func.now()` or `server_default=sa.text('(CURRENT_TIMESTAMP)')` for `created_at` and `updated_at`.
# `DateTime(timezone=True)` for timestamp columns.
# The exact error messages like "Debt not found" or "Payment not found" depend on CRUD implementation.
# The logic for updating debt status ("Outstanding", "Partially Paid", "Paid") must be in CRUD.
# `crud.update_debt_status_based_on_payments` (or similar logic within payment CRUDs) is essential.

# A fixture for an already paid debt might be useful
@pytest.fixture
def paid_test_debt(db: Session, test_debt: Debt):
    crud.create_payment(db, PaymentCreate(debt_id=test_debt.id, amount_paid=Decimal("100.00"), payment_date=date.today()))
    db.refresh(test_debt)
    assert test_debt.status == "Paid"
    return test_debt

def test_create_payment_on_already_paid_debt_records_overpayment(db: Session, paid_test_debt: Debt):
    assert paid_test_debt.outstanding_amount == Decimal("0.00")

    overpayment = PaymentCreate(debt_id=paid_test_debt.id, amount_paid=Decimal("20.00"), payment_date=date.today())
    payment = crud.create_payment(db, overpayment)
    db.refresh(paid_test_debt)
    db.refresh(payment)

    assert payment.amount_paid == Decimal("20.00")
    assert paid_test_debt.outstanding_amount == Decimal("-20.00") # 0 - 20
    assert paid_test_debt.status == "Paid" # Or "Overpaid"

    # Check total paid for the debt
    payments = crud.get_payments_for_debt(db, debt_id=paid_test_debt.id)
    total_paid_sum = sum(p.amount_paid for p in payments)
    assert total_paid_sum == Decimal("120.00")

def test_update_payment_on_paid_debt_adjusts_overpayment(db: Session, paid_test_debt: Debt):
    # paid_test_debt already has one payment of 100.00. Outstanding is 0.00
    initial_payment = crud.get_payments_for_debt(db, debt_id=paid_test_debt.id)[0]

    # Update initial payment from 100 to 130
    crud.update_payment(db, payment_id=initial_payment.id, payment_update=PaymentUpdate(amount_paid=Decimal("130.00")))
    db.refresh(paid_test_debt)

    assert paid_test_debt.outstanding_amount == Decimal("-30.00") # 100 (original) - 130 (new total payment)
    assert paid_test_debt.status == "Paid"

    # Update initial payment from 130 to 80
    crud.update_payment(db, payment_id=initial_payment.id, payment_update=PaymentUpdate(amount_paid=Decimal("80.00")))
    db.refresh(paid_test_debt)

    assert paid_test_debt.outstanding_amount == Decimal("20.00") # 100 (original) - 80 (new total payment)
    assert paid_test_debt.status == "Partially Paid"

# Test that payment_date is correctly stored and retrieved
def test_payment_date_storage_retrieval(db: Session, test_debt: Debt):
    test_date = date(2023, 7, 15)
    payment_data = PaymentCreate(debt_id=test_debt.id, amount_paid=Decimal("10.00"), payment_date=test_date)
    payment = crud.create_payment(db, payment_data)
    db.refresh(payment)

    retrieved_payment = crud.get_payment(db, payment.id)
    assert retrieved_payment.payment_date == test_date

# Test that payment_method and notes are correctly stored and retrieved (optional fields)
def test_payment_metadata_storage_retrieval(db: Session, test_debt: Debt):
    test_method = "Test Method"
    test_notes = "These are some test notes."
    payment_data_full = PaymentCreate(
        debt_id=test_debt.id,
        amount_paid=Decimal("10.00"),
        payment_date=date.today(),
        payment_method=test_method,
        notes=test_notes
    )
    payment_full = crud.create_payment(db, payment_data_full)
    db.refresh(payment_full)

    retrieved_payment_full = crud.get_payment(db, payment_full.id)
    assert retrieved_payment_full.payment_method == test_method
    assert retrieved_payment_full.notes == test_notes

    payment_data_minimal = PaymentCreate(
        debt_id=test_debt.id,
        amount_paid=Decimal("10.00"),
        payment_date=date.today()
    )
    payment_minimal = crud.create_payment(db, payment_data_minimal)
    db.refresh(payment_minimal)

    retrieved_payment_minimal = crud.get_payment(db, payment_minimal.id)
    assert retrieved_payment_minimal.payment_method is None
    assert retrieved_payment_minimal.notes is None

# Test updating payment method and notes to None
def test_update_payment_metadata_to_none(db: Session, test_debt: Debt):
    payment = crud.create_payment(db, PaymentCreate(
        debt_id=test_debt.id,
        amount_paid=Decimal("10.00"),
        payment_date=date.today(),
        payment_method="Initial Method",
        notes="Initial notes"
    ))
    db.refresh(payment)

    update_schema = PaymentUpdate(payment_method=None, notes=None)
    updated_payment = crud.update_payment(db, payment_id=payment.id, payment_update=update_schema)
    db.refresh(updated_payment)

    assert updated_payment.payment_method is None
    assert updated_payment.notes is None
    assert updated_payment.amount_paid == Decimal("10.00") # Ensure amount unchanged

# Test that updating only one metadata field leaves the other unchanged
def test_update_payment_partial_metadata(db: Session, test_debt: Debt):
    initial_method = "Initial Method"
    initial_notes = "Initial notes"
    payment = crud.create_payment(db, PaymentCreate(
        debt_id=test_debt.id,
        amount_paid=Decimal("10.00"),
        payment_date=date.today(),
        payment_method=initial_method,
        notes=initial_notes
    ))
    db.refresh(payment)

    new_notes = "Updated notes, method should remain same"
    update_schema_notes = PaymentUpdate(notes=new_notes)
    updated_payment_notes = crud.update_payment(db, payment_id=payment.id, payment_update=update_schema_notes)
    db.refresh(updated_payment_notes)

    assert updated_payment_notes.payment_method == initial_method
    assert updated_payment_notes.notes == new_notes

    # Reset for next part of test
    db.expire(updated_payment_notes) # force reload if accessed
    payment_reloaded = crud.get_payment(db, payment.id)


    new_method = "Updated method, notes should revert to initial_notes (or current if stateful)"
    # To be accurate, notes should be what they became in previous step if we reuse updated_payment_notes
    # Let's use the reloaded payment as base for clarity

    update_schema_method = PaymentUpdate(payment_method=new_method)
    updated_payment_method = crud.update_payment(db, payment_id=payment_reloaded.id, payment_update=update_schema_method)
    db.refresh(updated_payment_method)

    assert updated_payment_method.payment_method == new_method
    assert updated_payment_method.notes == new_notes # Notes from previous update should persist
    assert updated_payment_method.amount_paid == Decimal("10.00")

# Final verification of debt state after a sequence of operations
def test_debt_state_after_complex_payment_ops(db: Session, test_debt: Debt):
    # Debt: 100 outstanding
    p1 = crud.create_payment(db, PaymentCreate(debt_id=test_debt.id, amount_paid=Decimal("50.00"), payment_date=date.today())) # Debt: 50 outstanding, Partially Paid
    db.refresh(test_debt)
    assert test_debt.outstanding_amount == Decimal("50.00")
    assert test_debt.status == "Partially Paid"

    p2 = crud.create_payment(db, PaymentCreate(debt_id=test_debt.id, amount_paid=Decimal("60.00"), payment_date=date.today())) # Debt: -10 outstanding, Paid
    db.refresh(test_debt)
    assert test_debt.outstanding_amount == Decimal("-10.00")
    assert test_debt.status == "Paid"

    # Update p1 from 50 to 30 (reduces total paid by 20)
    crud.update_payment(db, payment_id=p1.id, payment_update=PaymentUpdate(amount_paid=Decimal("30.00")))
    db.refresh(test_debt) # Total paid: 30 (p1) + 60 (p2) = 90. Debt: 10 outstanding, Partially Paid
    assert test_debt.outstanding_amount == Decimal("10.00")
    assert test_debt.status == "Partially Paid"

    # Delete p2 (amount 60)
    crud.delete_payment(db, payment_id=p2.id)
    db.refresh(test_debt) # Total paid: 30 (p1). Debt: 70 outstanding, Partially Paid
    assert test_debt.outstanding_amount == Decimal("70.00")
    assert test_debt.status == "Partially Paid"

    # Pay it off again
    p3 = crud.create_payment(db, PaymentCreate(debt_id=test_debt.id, amount_paid=Decimal("70.00"), payment_date=date.today())) # Debt: 0 outstanding, Paid
    db.refresh(test_debt) # Total paid: 30 (p1) + 70 (p3) = 100.
    assert test_debt.outstanding_amount == Decimal("0.00")
    assert test_debt.status == "Paid"This is a very thorough set of CRUD tests for payments. I've covered:
*   Creating payments and their effect on debt status (Partial, Paid, Overpaid).
*   Preventing payment creation on archived or non-existent debts.
*   Schema validation for negative payment amounts (though this is Pydantic's role primarily).
*   Getting individual payments and listing payments for a debt.
*   Updating payment amounts and observing the correct adjustments to debt outstanding amount and status, including scenarios like paid to partial, partial to paid, and adjustments with overpayments.
*   Updating non-amount fields of a payment (metadata like date, method, notes) without affecting debt financials.
*   Error handling for updating non-existent payments or payments on archived debts.
*   Deleting payments and ensuring debt outstanding amount and status are correctly restored/recalculated, including scenarios with multiple payments.
*   Error handling for deleting non-existent payments or payments on archived debts.
*   Timestamp (`created_at`, `updated_at`) behavior.
*   Complex sequences of operations to ensure final debt state is correct.

The fixtures for user, business, customer, and debt are defined locally for now as requested. It's assumed that the `db` fixture is provided by `conftest.py` and that the necessary CRUD functions and SQLAlchemy models/Pydantic schemas (Payment, Debt, PaymentCreate, PaymentUpdate) are implemented as described in the project summary and implied by these tests.

The next step is to create the router tests.

**Step 2: Create `tests/backend_tests/routers/test_payments_router.py`**
