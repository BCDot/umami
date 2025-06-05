from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.backend.core import crud, models, schemas # Added models import
from app.backend.auth.security import get_current_active_user # For protecting endpoints
from app.backend.db.session import get_db # Updated import


router = APIRouter(
    prefix="/communications",
    tags=["Communication Logs"],
)

def get_authorized_business_id(current_user: models.User) -> int:
    """Helper to get the user's first business ID or raise error."""
    if not current_user.businesses:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User has no associated businesses."
        )
    return current_user.businesses[0].id

@router.post("/debt/{debt_id}", response_model=schemas.CommunicationLog)
async def create_log_for_debt(
    debt_id: int,
    log: schemas.CommunicationLogCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Create a new communication log for a specific debt, ensuring user owns the business associated with the debt.
    """
    if not db:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database not configured")

    authorized_business_id = get_authorized_business_id(current_user)
    db_debt = crud.get_debt(db, debt_id=debt_id, business_id=authorized_business_id)
    if not db_debt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Debt not found or not authorized for this user.")

    # Ensure the log's debt_id from schema matches path, or rely on path debt_id
    if log.debt_id != debt_id:
        # This could be an error, or one could prioritize the path variable.
        # For now, let's assume the schema's debt_id should align or be ignored if path is source of truth.
        # The crud.create_communication_log uses the debt_id parameter passed to it.
        print(f"Warning: Log schema debt_id ({log.debt_id}) differs from path debt_id ({debt_id}). Using path debt_id.")

    created_log = crud.create_communication_log(db=db, log=log, debt_id=debt_id)
    return created_log

@router.get("/debt/{debt_id}", response_model=List[schemas.CommunicationLog])
async def read_debt_communication_logs(
    debt_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Retrieve all communication logs for a specific debt, ensuring user owns the business.
    """
    if not db:
        return []

    authorized_business_id = get_authorized_business_id(current_user)
    db_debt = crud.get_debt(db, debt_id=debt_id, business_id=authorized_business_id)
    if not db_debt:
        # If debt not found/authorized, no logs should be accessible for it by this user
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Debt not found or not authorized for this user, cannot retrieve logs.")
        # Alternatively, return empty list if preferred: return []

    logs = crud.get_communication_logs_for_debt(db=db, debt_id=debt_id, skip=skip, limit=limit)
    return logs


@router.put("/{log_id}", response_model=schemas.CommunicationLog)
async def update_existing_communication_log(
    log_id: int,
    log_update: schemas.CommunicationLogUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Update an existing communication log, ensuring user owns the associated debt's business.
    """
    if not db:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database not configured")

    db_log = crud.get_communication_log(db, log_id=log_id)
    if not db_log:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Communication log with ID {log_id} not found.")

    authorized_business_id = get_authorized_business_id(current_user)
    db_debt = crud.get_debt(db, debt_id=db_log.debt_id, business_id=authorized_business_id)
    if not db_debt:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this communication log."
        )

    # Ensure log_update does not try to change debt_id if it's part of the schema
    if hasattr(log_update, 'debt_id') and log_update.debt_id is not None and log_update.debt_id != db_log.debt_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot change the debt association of a communication log.")

    updated_log = crud.update_communication_log(db=db, log_id=log_id, log_update=log_update)
    # crud.update_communication_log already handles the case where db_log might be None again, but we checked.
    return updated_log


@router.get("/{log_id}", response_model=schemas.CommunicationLog)
async def read_communication_log(
    log_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Retrieve a specific communication log by its ID, ensuring user owns the associated debt's business.
    """
    if not db:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database not configured")

    db_log = crud.get_communication_log(db, log_id=log_id)
    if db_log is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Communication log with ID {log_id} not found.")

    authorized_business_id = get_authorized_business_id(current_user)
    db_debt = crud.get_debt(db, debt_id=db_log.debt_id, business_id=authorized_business_id)
    if not db_debt:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this communication log."
        )
    return db_log
