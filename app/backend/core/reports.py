from sqlalchemy.orm import Session
from sqlalchemy import func, and_, distinct, cast, Date as SQLDate # Renamed Date to avoid conflict with datetime.date
from decimal import Decimal
from typing import Dict, List, Any
from datetime import datetime, date # datetime.date for calculations

from .models import Debt, Customer # Assuming models are in the same directory or accessible path

# Status considered as not fully paid
NON_PAID_STATUSES = ["Outstanding", "Overdue", "Pending", "Disputed", "In Collection"]


def get_total_outstanding_debt(db: Session, business_id: int) -> Decimal:
    """
    Calculates the total outstanding debt for a given business.
    Considers debts that are not archived and not marked as 'Paid'.
    """
    total = db.query(func.sum(Debt.outstanding_amount))\
              .filter(
                  Debt.business_id == business_id,
                  Debt.is_archived == False,
                  Debt.status.in_(NON_PAID_STATUSES) # More robust than just Debt.status != 'Paid'
              ).scalar()
    return total or Decimal('0.00')

def get_average_overdue_days(db: Session, business_id: int) -> float:
    """
    Calculates the average number of days debts are overdue for a given business.
    Only considers active (not archived) debts that are overdue.
    """
    today = datetime.utcnow().date()

    # Fetch due dates of overdue, non-archived debts
    overdue_debts_due_dates = db.query(Debt.due_date)\
                                .filter(
                                    Debt.business_id == business_id,
                                    Debt.is_archived == False,
                                    Debt.status.in_(NON_PAID_STATUSES), # Ensure it's an active debt
                                    Debt.due_date < today # Ensure it's actually overdue
                                ).all()

    if not overdue_debts_due_dates:
        return 0.0

    total_overdue_days = 0
    count_overdue_debts = 0
    for due_date_tuple in overdue_debts_due_dates:
        due_date = due_date_tuple[0]
        if due_date: # Ensure due_date is not None
            overdue_days = (today - due_date).days
            if overdue_days > 0: # Only count if actually overdue
                total_overdue_days += overdue_days
                count_overdue_debts += 1

    if count_overdue_debts == 0:
        return 0.0

    return float(total_overdue_days) / count_overdue_debts


def get_debt_status_summary(db: Session, business_id: int) -> List[Dict[str, Any]]:
    """
    Provides a summary of debts by status (count and total outstanding amount per status)
    for a given business, excluding archived debts.
    """
    query_result = db.query(
        Debt.status,
        func.count(Debt.id).label('count'),
        func.sum(Debt.outstanding_amount).label('total_amount')
    ).filter(
        Debt.business_id == business_id,
        Debt.is_archived == False
    ).group_by(Debt.status).all()

    summary = [
        {
            'status': r.status,
            'count': r.count,
            'total_amount': r.total_amount or Decimal('0.00')
        } for r in query_result
    ]
    return summary

def get_overdue_accounts_count(db: Session, business_id: int) -> int:
    """
    Counts the number of unique customers with overdue debts for a given business.
    Considers debts that are not archived, not 'Paid', and past their due date.
    """
    today = datetime.utcnow().date()
    count = db.query(func.count(distinct(Debt.customer_id)))\
              .filter(
                  Debt.business_id == business_id,
                  Debt.is_archived == False,
                  Debt.status.in_(NON_PAID_STATUSES),
                  Debt.due_date < today # Due date is in the past
              ).scalar()
    return count or 0
