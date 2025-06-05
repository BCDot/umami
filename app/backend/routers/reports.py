from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict
from decimal import Decimal

from app.backend.core import schemas, models # Added models for current_user type hint
from app.backend.core import reports as report_functions
from app.backend.db.session import get_db
from app.backend.auth.security import get_current_active_user # For authorization

router = APIRouter(
    prefix="/reports",
    tags=["Reports"],
)

def _check_business_ownership(current_user: models.User, requested_business_id: int):
    """Helper to check if the requested business_id is owned by the current user."""
    if not any(business.id == requested_business_id for business in current_user.businesses):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access reports for this business."
        )

@router.get("/summary/{business_id}", response_model=schemas.ReportSummarySchema)
async def get_reports_summary(
    business_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Retrieve a summary report for a given business, including total outstanding debt,
    count of overdue accounts, and average overdue days.
    User must own the business.
    """
    _check_business_ownership(current_user, business_id)

    if not db:
        # This case should ideally not be hit if get_db provides a session or raises an error.
        # If it does, it's an internal server issue.
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database not configured")

    total_outstanding = report_functions.get_total_outstanding_debt(db, business_id=business_id)
    overdue_count = report_functions.get_overdue_accounts_count(db, business_id=business_id)
    avg_days = report_functions.get_average_overdue_days(db, business_id=business_id)

    return schemas.ReportSummarySchema(
        total_outstanding_debt=total_outstanding,
        overdue_accounts_count=overdue_count,
        average_overdue_days=avg_days
    )

@router.get("/debt-status-breakdown/{business_id}", response_model=schemas.DebtStatusReportSchema)
async def get_debt_status_breakdown_report(
    business_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Retrieve a report breaking down debts by their status (e.g., Outstanding, Paid, Overdue)
    including count and total amount for each status. User must own the business.
    """
    _check_business_ownership(current_user, business_id)

    if not db:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database not configured")

    status_summary_data = report_functions.get_debt_status_summary(db, business_id=business_id)

    # Convert the list of dicts from reports.py to List[DebtStatusItemSchema]
    status_breakdown_items = [
        schemas.DebtStatusItemSchema(**item) for item in status_summary_data
    ]

    return schemas.DebtStatusReportSchema(status_breakdown=status_breakdown_items)
