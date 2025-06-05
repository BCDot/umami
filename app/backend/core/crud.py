from sqlalchemy.orm import Session
from typing import List, Optional

from . import models
from . import schemas

# ---- Business CRUD Functions ----

def create_business(db: Session, business: schemas.BusinessCreate) -> models.Business:
    """
    Create a new business.
    """
    # Example: db_business = models.Business(**business.dict(), owner_id=user_id)
    # db.add(db_business); db.commit(); db.refresh(db_business)
    # return db_business
    pass

def get_business(db: Session, business_id: int) -> Optional[models.Business]:
    """
    Get a single business by its ID.
    # Example: return db.query(models.Business).filter(models.Business.id == business_id).first()
    """
    pass

def get_all_businesses(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[models.Business]:
    """
    Get all businesses for a specific user.
    """
    # Example: return db.query(models.Business).filter(models.Business.user_id == user_id).offset(skip).limit(limit).all()
    pass

def update_business(db: Session, business_id: int, business_update: schemas.BusinessUpdate) -> Optional[models.Business]:
    """
    Update an existing business.
    """
    pass

def delete_business(db: Session, business_id: int) -> Optional[models.Business]:
    """
    Delete a business.
    """
    # Example: db_business = get_business(db, business_id)
    # if db_business: db.delete(db_business); db.commit()
    # return db_business
    pass

# ---- User CRUD Functions ----

def create_user(db: Session, user: schemas.UserCreate) -> models.User:
    """
    Create a new user.
    The password should be hashed before storing.
    """
    from app.backend.auth.security import get_password_hash # Import here to avoid circular dependency issues at module level

    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        email=user.email,
        username=user.username,
        hashed_password=hashed_password,
        is_active=user.is_active if user.is_active is not None else True
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user(db: Session, user_id: int) -> Optional[models.User]:
    """
    Get a user by their ID.
    """
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    """
    Get a user by their email address.
    """
    return db.query(models.User).filter(models.User.email == email).first()

def get_user_by_username(db: Session, username: str) -> Optional[models.User]:
    """
    Get a user by their username.
    """
    return db.query(models.User).filter(models.User.username == username).first()

# ---- Customer CRUD Functions ----

def create_customer(db: Session, customer: schemas.CustomerCreate) -> models.Customer:
    """
    Create a new customer for a business.
    """
    # Example: db_customer = models.Customer(**customer.dict())
    # db.add(db_customer); db.commit(); db.refresh(db_customer)
    # return db_customer
    pass

def get_customer(db: Session, customer_id: int) -> Optional[models.Customer]:
    """
    Get a single customer by their ID.
    # Example: return db.query(models.Customer).filter(models.Customer.id == customer_id).first()
    """
    pass

def get_all_customers(db: Session, business_id: int, skip: int = 0, limit: int = 100) -> List[models.Customer]:
    """
    Get all customers for a specific business.
    """
    # Example: return db.query(models.Customer).filter(models.Customer.business_id == business_id).offset(skip).limit(limit).all()
    pass

def update_customer(db: Session, customer_id: int, customer_update: schemas.CustomerUpdate) -> Optional[models.Customer]:
    """
    Update an existing customer.
    """
    pass

def archive_customer(db: Session, customer_id: int) -> Optional[models.Customer]:
    """
    Archive a customer (mark as inactive).
    Placeholder: Actual implementation would set an 'is_archived' flag.
    """
    pass

# ---- Debt CRUD Functions ----

def create_debt(db: Session, debt: schemas.DebtCreate) -> models.Debt:
    """
    Create a new debt record for a customer.
    """
    # Example: db_debt = models.Debt(**debt.dict())
    # db.add(db_debt); db.commit(); db.refresh(db_debt)
    # return db_debt
    pass

def get_debt(db: Session, debt_id: int) -> Optional[models.Debt]:
    """
    Get a single debt record by its ID.
    # Example: return db.query(models.Debt).filter(models.Debt.id == debt_id).first()
    """
    pass

def get_all_debts_by_customer(db: Session, customer_id: int, skip: int = 0, limit: int = 100) -> List[models.Debt]:
    """
    Get all debts for a specific customer.
    """
    # Example: return db.query(models.Debt).filter(models.Debt.customer_id == customer_id).offset(skip).limit(limit).all()
    pass

def get_all_debts_by_business(db: Session, business_id: int, skip: int = 0, limit: int = 100) -> List[models.Debt]:
    """
    Get all debts for a specific business.
    """
    # Example: return db.query(models.Debt).filter(models.Debt.business_id == business_id).offset(skip).limit(limit).all()
    pass

def update_debt(db: Session, debt_id: int, debt_update: schemas.DebtUpdate) -> Optional[models.Debt]:
    """
    Update an existing debt record.
    """
    pass

def archive_debt(db: Session, debt_id: int) -> Optional[models.Debt]:
    """
    Archive a debt record.
    Placeholder: Actual implementation would set an 'is_archived' flag or similar.
    """
    pass

# ---- CommunicationLog CRUD Functions ----

def create_communication_log(db: Session, log: schemas.CommunicationLogCreate, debt_id: int) -> models.CommunicationLog:
    """Create a new communication log for a specific debt."""
    db_log = models.CommunicationLog(**log.dict(), debt_id=debt_id)
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log

def get_communication_log(db: Session, log_id: int) -> Optional[models.CommunicationLog]:
    """Get a communication log by ID."""
    return db.query(models.CommunicationLog).filter(models.CommunicationLog.id == log_id).first()

def get_communication_logs_for_debt(db: Session, debt_id: int, skip: int = 0, limit: int = 100) -> List[models.CommunicationLog]:
    """Get all communication logs for a specific debt."""
    return db.query(models.CommunicationLog)\
        .filter(models.CommunicationLog.debt_id == debt_id)\
        .order_by(models.CommunicationLog.date_sent.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()

def update_communication_log(db: Session, log_id: int, log_update: schemas.CommunicationLogUpdate) -> Optional[models.CommunicationLog]:
    """Update an existing communication log."""
    db_log = get_communication_log(db, log_id=log_id)
    if db_log:
        update_data = log_update.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_log, key, value)
        db.commit()
        db.refresh(db_log)
    return db_log
