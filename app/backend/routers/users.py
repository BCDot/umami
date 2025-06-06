from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.backend.core import crud, models, schemas
from app.backend.db.session import get_db
from app.backend.auth.security import get_current_active_user

router = APIRouter(
    # Prefix /api/v1/users will be added in main.py
    tags=["Users"],
)

@router.put("/me", response_model=schemas.User)
async def update_current_user_endpoint(
    user_update: schemas.UserUpdate,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update current user's profile information (e.g., email, password, is_active).
    Username changes are typically handled separately or disallowed due to being an identifier.
    If username is part of UserUpdate and meant to be updatable, ensure appropriate checks (e.g., uniqueness).
    """
    # Prevent username changes via this endpoint if username is part of UserUpdate and set
    if user_update.username is not None and user_update.username != current_user.username:
        # Or, if allowing username changes, add uniqueness check for the new username:
        # existing_user = crud.get_user_by_username(db, username=user_update.username)
        # if existing_user and existing_user.id != current_user.id:
        #     raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already taken.")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username change not allowed via this endpoint.")

    updated_user = crud.update_user(db, user_id=current_user.id, user_update=user_update)
    if not updated_user:
        # This should not happen if current_user is valid, but as a safeguard:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found for update.")
    return updated_user

@router.delete("/me", response_model=schemas.User)
async def deactivate_current_user_endpoint(
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Deactivate current user's account (soft delete by setting is_active=False).
    """
    deactivated_user = crud.delete_user(db, user_id=current_user.id) # crud.delete_user performs soft delete
    if not deactivated_user:
        # This should not happen if current_user is valid
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found for deactivation.")
    return deactivated_user

# Example: Get current user's info (already in auth_endpoints.py as /users/me, could be moved here)
# @router.get("/me", response_model=schemas.User)
# async def read_current_user_me(current_user: models.User = Depends(get_current_active_user)):
#     """Fetch the current authenticated active user."""
#     return current_user
