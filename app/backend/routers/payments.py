from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.backend.core import crud, models, schemas
from app.backend.db.session import get_db
from app.backend.auth.security import get_current_active_user

router = APIRouter(
    # Prefix /api/v1/payments will be added in main.py
    tags=["Payments"],
)

# Helper to check if the user is authorized for the debt (owns the business associated with the debt)
# Returns the db_debt object if authorized, otherwise raises HTTPException
async def get_authorized_debt(debt_id: int, db: Session, current_user: models.User) -> models.Debt:
    db_debt = crud.get_debt_by_id_for_user(db, debt_id=debt_id, user_id=current_user.id)
    if not db_debt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Debt not found or not authorized for this user."
        )
    return db_debt

@router.post("/", response_model=schemas.Payment, status_code=status.HTTP_201_CREATED)
async def create_payment_endpoint(
    payment_in: schemas.PaymentCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Record a new payment for a debt.
    The user must own the business associated with the `debt_id` provided in the payment data.
    """
    # Authorization: Ensure the debt exists and belongs to the user's business
    await get_authorized_debt(payment_in.debt_id, db, current_user)

    try:
        # The crud.create_payment function now takes debt_id from payment_in schema
        return crud.create_payment(db=db, payment=payment_in, debt_id=payment_in.debt_id)
    except ValueError as e: # Catch ValueErrors from CRUD (e.g., debt archived, amount non-positive)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/", response_model=List[schemas.Payment])
async def list_payments_endpoint(
    debt_id: int = Query(..., description="The ID of the debt to list payments for"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    List all payments for a specific debt.
    The user must own the business associated with the debt.
    """
    await get_authorized_debt(debt_id, db, current_user) # Authorization check
    payments = crud.get_payments_for_debt(db=db, debt_id=debt_id, skip=skip, limit=limit)
    return payments

@router.get("/{payment_id}", response_model=schemas.Payment)
async def read_payment_endpoint(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Get a specific payment by its ID.
    The payment must be associated with a debt belonging to one of the user's businesses.
    """
    db_payment = crud.get_payment(db, payment_id=payment_id)
    if not db_payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found.")

    # Authorization: check ownership of the associated debt
    await get_authorized_debt(db_payment.debt_id, db, current_user)
    return db_payment

@router.put("/{payment_id}", response_model=schemas.Payment)
async def update_payment_endpoint(
    payment_id: int,
    payment_in: schemas.PaymentUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Update a payment's details.
    The payment must be associated with a debt belonging to one of the user's businesses.
    """
    db_payment = crud.get_payment(db, payment_id=payment_id)
    if not db_payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found.")

    # Authorization: check ownership of the associated debt
    await get_authorized_debt(db_payment.debt_id, db, current_user)

    try:
        updated_payment = crud.update_payment(db=db, payment_id=payment_id, payment_update=payment_in)
        if not updated_payment: # Should be caught by initial get_payment if ID is totally wrong
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found for update.")
        return updated_payment
    except ValueError as e: # Catch ValueErrors from CRUD (e.g., debt archived, amount non-positive)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{payment_id}", response_model=schemas.Payment)
async def delete_payment_endpoint(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Delete a payment. This will also adjust the associated debt's outstanding amount.
    The payment must be associated with a debt belonging to one of the user's businesses.
    """
    db_payment = crud.get_payment(db, payment_id=payment_id)
    if not db_payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found.")

    # Authorization: check ownership of the associated debt
    await get_authorized_debt(db_payment.debt_id, db, current_user)

    try:
        deleted_payment = crud.delete_payment(db=db, payment_id=payment_id)
        if not deleted_payment: # Should be caught by initial get_payment
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found for deletion.")
        return deleted_payment # Return the deleted payment data
    except ValueError as e: # Catch ValueErrors from CRUD (e.g., debt archived)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
