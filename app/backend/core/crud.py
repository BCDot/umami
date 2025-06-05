from sqlalchemy.orm import Session
from typing import List, Optional

from . import models
from . import schemas

# ---- Business CRUD Functions ----

def create_business(db: Session, business: schemas.BusinessCreate) -> models.Business:
    """
    Create a new business.
    """
    # user_id is part of business schema (business.user_id)
    db_business = models.Business(**business.model_dump(exclude_unset=True)) # dict to model_dump
    db.add(db_business)
    db.commit()
    db.refresh(db_business)
    return db_business

def get_business(db: Session, business_id: int, user_id: int) -> Optional[models.Business]:
    """
    Get a single business by its ID, ensuring it belongs to the user.
    """
    return db.query(models.Business).filter(models.Business.id == business_id, models.Business.user_id == user_id).first()

def get_all_businesses(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[models.Business]:
    """
    Get all businesses for a specific user.
    """
    return db.query(models.Business).filter(models.Business.user_id == user_id).offset(skip).limit(limit).all()

def update_business(db: Session, business_id: int, business_update: schemas.BusinessUpdate, user_id: int) -> Optional[models.Business]:
    """
    Update an existing business, ensuring it belongs to the user.
    """
    db_business = db.query(models.Business).filter(models.Business.id == business_id, models.Business.user_id == user_id).first()
    if db_business:
        update_data = business_update.model_dump(exclude_unset=True) # dict to model_dump
        for key, value in update_data.items():
            setattr(db_business, key, value)
        db.commit()
        db.refresh(db_business)
    return db_business

def delete_business(db: Session, business_id: int, user_id: int) -> Optional[models.Business]:
    """
    Delete a business, ensuring it belongs to the user.
    Returns the deleted business object or None if not found/not authorized.
    """
    db_business = db.query(models.Business).filter(models.Business.id == business_id, models.Business.user_id == user_id).first()
    if db_business:
        db.delete(db_business)
        db.commit()
        return db_business # Return the object that was deleted
    return None

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

def get_customer_by_id_unscoped(db: Session, customer_id: int) -> Optional[models.Customer]:
    """Gets a customer by ID without business ownership check. For router use before auth check."""
    return db.query(models.Customer).filter(models.Customer.id == customer_id).first()

def get_customer_by_id_for_user(db: Session, customer_id: int, user_id: int) -> Optional[models.Customer]:
    """
    Fetches a customer by ID only if they belong to a business owned by the specified user_id.
    """
    return db.query(models.Customer)\
        .join(models.Business, models.Customer.business_id == models.Business.id)\
        .filter(models.Customer.id == customer_id, models.Business.user_id == user_id)\
        .first()

def create_customer(db: Session, customer: schemas.CustomerCreate) -> models.Customer:
    """
    Create a new customer for a business.
    """
    # business_id is part of customer schema (customer.business_id)
    db_customer = models.Customer(**customer.model_dump(exclude_unset=True)) # dict to model_dump
    db.add(db_customer)
    db.commit()
    db.refresh(db_customer)
    return db_customer

def get_customer(db: Session, customer_id: int, business_id: int) -> Optional[models.Customer]:
    """
    Get a single customer by their ID, ensuring they belong to the specified business.
    """
    return db.query(models.Customer).filter(models.Customer.id == customer_id, models.Customer.business_id == business_id).first()

def get_all_customers(db: Session, business_id: int, skip: int = 0, limit: int = 100) -> List[models.Customer]:
    """
    Get all customers for a specific business.
    """
    return db.query(models.Customer).filter(models.Customer.business_id == business_id).offset(skip).limit(limit).all()

def update_customer(db: Session, customer_id: int, customer_update: schemas.CustomerUpdate, business_id: int) -> Optional[models.Customer]:
    """
    Update an existing customer, ensuring they belong to the specified business.
    """
    db_customer = db.query(models.Customer).filter(models.Customer.id == customer_id, models.Customer.business_id == business_id).first()
    if db_customer:
        update_data = customer_update.model_dump(exclude_unset=True) # dict to model_dump
        for key, value in update_data.items():
            setattr(db_customer, key, value)
        db.commit()
        db.refresh(db_customer)
    return db_customer

def archive_customer(db: Session, customer_id: int, business_id: int) -> Optional[models.Customer]:
    """
    Archive a customer (mark as is_active=False), ensuring they belong to the specified business.
    """
    db_customer = db.query(models.Customer).filter(models.Customer.id == customer_id, models.Customer.business_id == business_id).first()
    if db_customer:
        db_customer.is_active = False
        db.commit()
        db.refresh(db_customer)
    return db_customer

# ---- Debt CRUD Functions ----

def create_debt(db: Session, debt: schemas.DebtCreate) -> models.Debt: # customer_id and business_id are in debt schema
    """
    Create a new debt record. customer_id and business_id are part of debt schema.
    """
    db_debt = models.Debt(**debt.model_dump(exclude_unset=True)) # dict to model_dump
    db.add(db_debt)
    db.commit()
    db.refresh(db_debt)
    return db_debt

def get_debt(db: Session, debt_id: int, business_id: int) -> Optional[models.Debt]: # Added business_id for ownership check
    """
    Get a single debt record by its ID, ensuring it belongs to the specified business.
    """
    return db.query(models.Debt).filter(models.Debt.id == debt_id, models.Debt.business_id == business_id).first()

def get_all_debts_by_customer(db: Session, customer_id: int, business_id: int, skip: int = 0, limit: int = 100) -> List[models.Debt]:
    """
    Get all debts for a specific customer, ensuring the customer belongs to the specified business.
    """
    # First, ensure the customer belongs to the business (optional, could be handled by service layer)
    # customer = get_customer(db, customer_id, business_id)
    # if not customer:
    #     return []
    return db.query(models.Debt)\
        .filter(models.Debt.customer_id == customer_id, models.Debt.business_id == business_id)\
        .offset(skip).limit(limit).all()

def get_all_debts_by_business(db: Session, business_id: int, skip: int = 0, limit: int = 100) -> List[models.Debt]:
    """
    Get all debts for a specific business.
    """
    return db.query(models.Debt).filter(models.Debt.business_id == business_id).offset(skip).limit(limit).all()

def update_debt(db: Session, debt_id: int, debt_update: schemas.DebtUpdate, business_id: int) -> Optional[models.Debt]:
    """
    Update an existing debt record, ensuring it belongs to the specified business.
    """
    db_debt = db.query(models.Debt).filter(models.Debt.id == debt_id, models.Debt.business_id == business_id).first()
    if db_debt:
        update_data = debt_update.model_dump(exclude_unset=True) # dict to model_dump
        for key, value in update_data.items():
            setattr(db_debt, key, value)
        db.commit()
        db.refresh(db_debt)
    return db_debt

def archive_debt(db: Session, debt_id: int, business_id: int) -> Optional[models.Debt]:
    """
    Archive a debt record (mark as is_archived=True), ensuring it belongs to the specified business.
    """
    db_debt = db.query(models.Debt).filter(models.Debt.id == debt_id, models.Debt.business_id == business_id).first()
    if db_debt:
        db_debt.is_archived = True
        db.commit()
        db.refresh(db_debt)
    return db_debt

# ---- CommunicationLog CRUD Functions ----

def create_communication_log(db: Session, log: schemas.CommunicationLogCreate, debt_id: int) -> models.CommunicationLog: # debt_id is passed directly
    """Create a new communication log for a specific debt."""
    # Consider adding a check here to ensure the debt (debt_id) itself belongs to an authorized business if necessary.
    log_data = log.model_dump(exclude_unset=True) # Changed from dict()
    # Ensure the debt_id from the path parameter is used, overriding any in the schema if present.
    log_data['debt_id'] = debt_id

    db_log = models.CommunicationLog(**log_data)
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
        update_data = log_update.model_dump(exclude_unset=True) # Changed from dict()
        for key, value in update_data.items():
            setattr(db_log, key, value)
        db.commit()
        db.refresh(db_log)
    return db_log
