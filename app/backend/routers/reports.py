from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict # Added Dict for consistency
from decimal import Decimal

from app.backend.core import schemas # Schemas for request/response
from app.backend.core import reports as report_functions # Report generation functions
# from app.dependencies import get_db # Replace with your actual get_db dependency path

# Placeholder for get_db dependency - replace with your actual DB session provider
def get_db():
    print("[REPORTS_ROUTER_PLACEHOLDER] get_db() called, returning None for now.")
    yield None # CRUD/reporting operations will not work without a real DB session.

router = APIRouter(
    prefix="/reports",
    tags=["Reports"],
)

@router.get("/summary/{business_id}", response_model=schemas.ReportSummarySchema)
async def get_reports_summary(business_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a summary report for a given business, including total outstanding debt,
    count of overdue accounts, and average overdue days.
    """
    if not db:
        # Simulate data if DB is not available due to placeholder
        print(f"[REPORTS_ROUTER_PLACEHOLDER] DB not configured for business_id: {business_id}. Returning dummy summary.")
        return schemas.ReportSummarySchema(
            total_outstanding_debt=Decimal("12345.67"),
            overdue_accounts_count=15,
            average_overdue_days=45.2
        )

    total_outstanding = report_functions.get_total_outstanding_debt(db, business_id=business_id)
    overdue_count = report_functions.get_overdue_accounts_count(db, business_id=business_id)
    avg_days = report_functions.get_average_overdue_days(db, business_id=business_id)

    return schemas.ReportSummarySchema(
        total_outstanding_debt=total_outstanding,
        overdue_accounts_count=overdue_count,
        average_overdue_days=avg_days
    )

@router.get("/debt-status-breakdown/{business_id}", response_model=schemas.DebtStatusReportSchema)
async def get_debt_status_breakdown_report(business_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a report breaking down debts by their status (e.g., Outstanding, Paid, Overdue)
    including count and total amount for each status.
    """
    if not db:
        # Simulate data if DB is not available
        print(f"[REPORTS_ROUTER_PLACEHOLDER] DB not configured for business_id: {business_id}. Returning dummy status breakdown.")
        dummy_breakdown = [
            schemas.DebtStatusItemSchema(status="Outstanding", count=10, total_amount=Decimal("8000.00")),
            schemas.DebtStatusItemSchema(status="Overdue", count=5, total_amount=Decimal("4345.67")),
            schemas.DebtStatusItemSchema(status="Paid", count=50, total_amount=Decimal("25000.00")),
        ]
        return schemas.DebtStatusReportSchema(status_breakdown=dummy_breakdown)

    status_summary_data = report_functions.get_debt_status_summary(db, business_id=business_id)

    # Convert the list of dicts from reports.py to List[DebtStatusItemSchema]
    status_breakdown_items = [
        schemas.DebtStatusItemSchema(**item) for item in status_summary_data
    ]

    return schemas.DebtStatusReportSchema(status_breakdown=status_breakdown_items)
