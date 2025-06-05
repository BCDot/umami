from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.backend.core import crud, models, schemas
from app.backend.db.session import get_db
from app.backend.auth.security import get_current_active_user

router = APIRouter(
    # Prefix will be /api/v1/customers, added in main.py
    tags=["Customers"],
)

def _verify_business_ownership(current_user: models.User, business_id: int, db: Session):
    """
    Helper to verify that the current user owns the specified business.
    Fetches business to confirm ownership.
    """
    business = crud.get_business(db, business_id=business_id, user_id=current_user.id)
    if not business:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Business not found or not authorized for this user."
        )
    return business


@router.post("/", response_model=schemas.Customer, status_code=status.HTTP_201_CREATED)
async def create_customer_endpoint(
    customer: schemas.CustomerCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Create a new customer. The `business_id` in the payload must belong to the current user.
    """
    _verify_business_ownership(current_user, customer.business_id, db)
    # Optional: Check for duplicate customer email within the same business
    # existing_customer = db.query(models.Customer).filter(models.Customer.email == customer.email, models.Customer.business_id == customer.business_id).first()
    # if existing_customer:
    #     raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Customer with this email already exists for this business.")
    return crud.create_customer(db=db, customer=customer) # crud.create_customer uses customer.business_id from schema

@router.get("/", response_model=List[schemas.Customer])
async def list_customers_endpoint(
    business_id: Optional[int] = Query(None, description="The ID of the business to list customers for"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    List customers. If `business_id` is provided, lists customers for that specific business (owned by user).
    """
    if business_id is None:
        # Alternative: List customers across all businesses owned by the user.
        # This would require a different CRUD function, e.g., crud.get_all_customers_for_user(user_id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The 'business_id' query parameter is required."
        )
    _verify_business_ownership(current_user, business_id, db)
    customers = crud.get_all_customers(db=db, business_id=business_id, skip=skip, limit=limit)
    return customers

@router.get("/{customer_id}", response_model=schemas.Customer)
async def read_customer_endpoint(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Get a specific customer by their ID.
    The customer must belong to a business owned by the current user.
    """
    db_customer = crud.get_customer_by_id_for_user(db, customer_id=customer_id, user_id=current_user.id)
    if db_customer is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found or not authorized.")
    return db_customer

@router.put("/{customer_id}", response_model=schemas.Customer)
async def update_customer_endpoint(
    customer_id: int,
    customer_in: schemas.CustomerUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Update a customer's details.
    The customer must belong to a business owned by the current user.
    """
    # Fetch the existing customer and verify ownership in one go using the new CRUD function.
    db_customer = crud.get_customer_by_id_for_user(db, customer_id=customer_id, user_id=current_user.id)
    if db_customer is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found or not authorized for update.")

    # business_id cannot be changed via this endpoint. It's tied to the customer's original business.
    # CustomerUpdate schema does not include business_id, so no need to check customer_in for it.
    return crud.update_customer(db=db, customer_id=customer_id, customer_update=customer_in, business_id=db_customer.business_id)


@router.delete("/{customer_id}", response_model=schemas.Customer)
async def archive_customer_endpoint(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Archive a customer (mark as inactive).
    The customer must belong to a business owned by the current user.
    """
    db_customer = crud.get_customer_by_id_for_user(db, customer_id=customer_id, user_id=current_user.id)
    if db_customer is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found or not authorized for archival.")

    archived_customer = crud.archive_customer(db=db, customer_id=customer_id, business_id=db_customer.business_id)
    if not archived_customer: # Should not happen if above checks pass
         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to archive customer.")
    return archived_customer
