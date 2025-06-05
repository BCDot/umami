from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.backend.core import crud, models, schemas
from app.backend.auth.security import get_current_active_user # For protecting endpoints
# Placeholder for get_db dependency - replace with your actual DB session provider
# This should be the same as used in other router files
def get_db():
    print("[BUSINESSES_ROUTER_PLACEHOLDER] get_db() called, returning None for now.")
    yield None # CRUD operations will not work without a real DB session.


router = APIRouter(
    prefix="/businesses",
    tags=["Businesses"],
)

@router.post("/", response_model=schemas.Business)
async def create_new_business(
    business_in: schemas.BusinessCreate, # Renamed for clarity, 'business' is a common variable name
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Create a new business for the authenticated user.
    The user_id from the token will be assigned as the business owner.
    """
    if not db:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database not configured")

    # Ensure the user_id in the payload matches the authenticated user, or simply override it.
    # Forcing current_user.id is generally safer.
    if business_in.user_id != current_user.id:
        # Option 1: Raise an error if they try to assign to someone else
        # raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot create business for another user.")
        # Option 2: Silently override with the authenticated user's ID (chosen here)
        print(f"Overriding user_id in request ({business_in.user_id}) with authenticated user_id ({current_user.id})")
        business_in.user_id = current_user.id

    # Check if business with this name already exists for this user (optional, depends on requirements)
    # existing_business = db.query(models.Business).filter(models.Business.business_name == business_in.business_name, models.Business.user_id == current_user.id).first()
    # if existing_business:
    #     raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Business with this name already exists for this user.")

    created_business = crud.create_business(db=db, business=business_in)
    # The CRUD function `create_business` uses business_in.user_id, which we've now set to current_user.id
    return created_business

@router.get("/{business_id}", response_model=schemas.Business)
async def read_business(
    business_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Get a specific business owned by the authenticated user.
    """
    if not db:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database not configured")

    db_business = crud.get_business(db, business_id=business_id, user_id=current_user.id)
    if db_business is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Business not found or not owned by user")
    return db_business

@router.get("/", response_model=List[schemas.Business])
async def read_businesses(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Get all businesses owned by the authenticated user.
    """
    if not db:
        return [] # Or raise error

    businesses = crud.get_all_businesses(db, user_id=current_user.id, skip=skip, limit=limit)
    return businesses

@router.put("/{business_id}", response_model=schemas.Business)
async def update_existing_business(
    business_id: int,
    business_update: schemas.BusinessUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Update a business owned by the authenticated user.
    """
    if not db:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database not configured")

    updated_business = crud.update_business(db, business_id=business_id, business_update=business_update, user_id=current_user.id)
    if updated_business is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Business not found or not owned by user for update")
    return updated_business

@router.delete("/{business_id}", response_model=schemas.Business) # Or perhaps just status code 204
async def remove_business(
    business_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Delete a business owned by the authenticated user.
    """
    if not db:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database not configured")

    deleted_business = crud.delete_business(db, business_id=business_id, user_id=current_user.id)
    if deleted_business is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Business not found or not owned by user for deletion")
    return deleted_business # Returns the deleted object as confirmation
