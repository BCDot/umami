from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.backend.core import crud, models, schemas
from app.backend.db.session import get_db
from app.backend.auth.security import get_current_active_user

router = APIRouter(
    # Prefix /api/v1/debts will be added in main.py
    tags=["Debts"],
)

# Helper function for business ownership verification (copied from customers.py or make it common)
def _verify_business_ownership_for_debt_router(db: Session, current_user: models.User, business_id: int):
    """Verifies that the current user owns the specified business for debt operations."""
    business = crud.get_business(db, business_id=business_id, user_id=current_user.id)
    if not business:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Business not found or not authorized for this user."
        )
    return business # Return business if found and authorized

def _verify_customer_and_business_ownership(db: Session, current_user: models.User, business_id: int, customer_id: int):
    """
    Verifies that the current user owns the business, and the customer belongs to that business.
    Returns the customer object if valid, otherwise raises HTTPException.
    """
    business = crud.get_business(db, business_id=business_id, user_id=current_user.id)
    if not business:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Business not found or not authorized.")

    customer = crud.get_customer(db, customer_id=customer_id, business_id=business_id)
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found for this business.")
    return customer


@router.post("/", response_model=schemas.Debt, status_code=status.HTTP_201_CREATED)
async def create_debt_endpoint(
    debt: schemas.DebtCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Create a new debt.
    The `business_id` in the payload must be owned by the current user,
    and the `customer_id` must belong to that `business_id`.
    """
    _verify_customer_and_business_ownership(db, current_user, debt.business_id, debt.customer_id)
    return crud.create_debt(db=db, debt=debt)

@router.get("/", response_model=List[schemas.Debt])
async def list_debts_endpoint(
    business_id: Optional[int] = Query(None, description="Filter debts by business ID."),
    customer_id: Optional[int] = Query(None, description="Filter debts by customer ID (requires business_id if used for auth)."),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    List debts.
    - If `business_id` is provided, lists all debts for that business (user must own it).
    - If `customer_id` is provided, lists all debts for that customer (customer must belong to a business owned by the user).
    - One of `business_id` or `customer_id` must be provided.
    """
    if business_id:
        # Verify user owns this business_id
        _verify_business_ownership_for_debt_router(db, current_user, business_id)
        # business = crud.get_business(db, business_id=business_id, user_id=current_user.id)
        # if not business: # This check is now in the helper above
        #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Business not found or not authorized.")
        return crud.get_all_debts_by_business(db=db, business_id=business_id, skip=skip, limit=limit)
    elif customer_id:
        # Verify customer belongs to one of current_user's businesses
        # Fetch customer first (unscoped by business initially for this check)
        db_customer = crud.get_customer_by_id_unscoped(db, customer_id=customer_id)
        if not db_customer:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found.")

        # Now check if this customer's business is owned by the current user
        business_of_customer = crud.get_business(db, business_id=db_customer.business_id, user_id=current_user.id)
        if not business_of_customer:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view debts for this customer.")

        # Now it's safe to list debts for this customer, as they belong to an authorized business
        return crud.get_all_debts_by_customer(db=db, customer_id=customer_id, business_id=db_customer.business_id, skip=skip, limit=limit)
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Either business_id or customer_id query parameter is required.")


@router.get("/{debt_id}", response_model=schemas.Debt)
async def read_debt_endpoint(
    debt_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Get a specific debt by its ID.
    The debt must belong to a business owned by the current user.
    """
    db_debt = crud.get_debt_by_id_for_user(db, debt_id=debt_id, user_id=current_user.id)
    if db_debt is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Debt not found or not authorized.")
    return db_debt

@router.put("/{debt_id}", response_model=schemas.Debt)
async def update_debt_endpoint(
    debt_id: int,
    debt_in: schemas.DebtUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Update a debt's details.
    The debt must belong to a business owned by the current user.
    """
    db_debt = crud.get_debt_by_id_for_user(db, debt_id=debt_id, user_id=current_user.id)
    if db_debt is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Debt not found or not authorized for update.")

    # Ensure customer_id and business_id are not changed via this endpoint
    update_data = debt_in.model_dump(exclude_unset=True)
    if "customer_id" in update_data and update_data["customer_id"] != db_debt.customer_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot change customer association of the debt.")
    if "business_id" in update_data and update_data["business_id"] != db_debt.business_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot change business association of the debt.")

    return crud.update_debt(db=db, debt_id=debt_id, debt_update=debt_in, business_id=db_debt.business_id)

@router.delete("/{debt_id}", response_model=schemas.Debt)
async def archive_debt_endpoint(
    debt_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Archive a debt (mark as is_archived=True).
    The debt must belong to a business owned by the current user.
    """
    db_debt = crud.get_debt_by_id_for_user(db, debt_id=debt_id, user_id=current_user.id)
    if db_debt is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Debt not found or not authorized for archival.")

    archived_debt = crud.archive_debt(db=db, debt_id=debt_id, business_id=db_debt.business_id)
    if not archived_debt: # Should not happen if above checks pass
         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to archive debt.")
    return archived_debt
