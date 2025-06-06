from __future__ import annotations # Enables postponed evaluation of type annotations
from pydantic import BaseModel, ConfigDict, model_validator
from typing import Optional, List, Any
from datetime import date, datetime
from decimal import Decimal

# ---- CommunicationLog Schemas ----
class CommunicationLogBase(BaseModel):
    communication_type: Optional[str] = None
    llm_prompt_used: Optional[str] = None
    generated_content_snapshot: Optional[str] = None
    status: Optional[str] = None
    response_received: Optional[str] = None
    debt_id: int # This is required for creation via CommunicationLogCreate

class CommunicationLogCreate(CommunicationLogBase):
    pass

class CommunicationLogUpdate(BaseModel): # Does not inherit CommunicationLogBase to make all fields truly optional for update
    communication_type: Optional[str] = None
    llm_prompt_used: Optional[str] = None
    generated_content_snapshot: Optional[str] = None
    status: Optional[str] = None
    response_received: Optional[str] = None
    # date_sent could be updatable too if needed:
    # date_sent: Optional[datetime] = None

class CommunicationLog(CommunicationLogBase): # This is the response model, inherits debt_id
    id: int
    date_sent: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# ---- Debt Schemas ----
class DebtBase(BaseModel):
    original_amount: Decimal
    outstanding_amount: Decimal
    due_date: Optional[date] = None
    debt_type: Optional[str] = None
    invoice_number: Optional[str] = None
    status: str = 'Outstanding'
    notes: Optional[str] = None
    is_archived: Optional[bool] = False # New field
    customer_id: int
    business_id: int

    @model_validator(mode='after')
    def check_amounts(cls, values: Any) -> Any: # Changed values to Any, or specific model type
        # If 'values' is the model instance itself for Pydantic v2 'after' mode
        original_amount = getattr(values, 'original_amount', None)
        outstanding_amount = getattr(values, 'outstanding_amount', None)

        if original_amount is not None and outstanding_amount is not None:
            if outstanding_amount > original_amount:
                raise ValueError('Outstanding amount cannot be greater than original amount.')
        return values

class DebtCreate(DebtBase):
    pass

class DebtUpdate(BaseModel):
    original_amount: Optional[Decimal] = None
    outstanding_amount: Optional[Decimal] = None
    due_date: Optional[date] = None
    debt_type: Optional[str] = None
    invoice_number: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    is_archived: Optional[bool] = None

    @model_validator(mode='after')
    def check_amounts_update(cls, values: Any) -> Any:
        # For DebtUpdate, fields are optional. Only validate if both are provided and not None.
        original_amount = getattr(values, 'original_amount', None)
        outstanding_amount = getattr(values, 'outstanding_amount', None)

        if original_amount is not None and outstanding_amount is not None:
            if outstanding_amount > original_amount:
                raise ValueError('Outstanding amount cannot be greater than original amount.')
        return values

class Debt(DebtBase):
    id: int
    created_at: datetime
    updated_at: datetime
    is_archived: bool # Ensure it's part of the response model
    communication_logs: List[CommunicationLog] = []

    model_config = ConfigDict(from_attributes=True)

# ---- Customer Schemas ----
class CustomerBase(BaseModel):
    customer_name: str
    email: str
    phone: Optional[str] = None
    address: str
    is_active: Optional[bool] = True # New field
    business_id: int

class CustomerCreate(CustomerBase):
    pass

class CustomerUpdate(BaseModel):
    customer_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    is_active: Optional[bool] = None # New field for updates

class Customer(CustomerBase):
    id: int
    created_at: datetime
    updated_at: datetime
    is_active: bool # Ensure it's part of the response model
    debts: List[Debt] = []
    # business: Optional[Business] = None

    model_config = ConfigDict(from_attributes=True)

# ---- Business Schemas ----
class BusinessBase(BaseModel):
    business_name: str
    abn: Optional[str] = None
    contact_email: str
    contact_phone: Optional[str] = None
    address: Optional[str] = None
    user_id: int

class BusinessCreate(BusinessBase):
    pass

class BusinessUpdate(BaseModel):
    business_name: Optional[str] = None
    abn: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    address: Optional[str] = None

class Business(BusinessBase):
    id: int
    created_at: datetime
    updated_at: datetime
    customers: List[Customer] = []
    debts: List[Debt] = []
    owner: Optional[User] = None # Represent the user who owns this business

    model_config = ConfigDict(from_attributes=True)

# ---- User Schemas ----
class UserBase(BaseModel):
    username: str
    email: str
    is_active: Optional[bool] = True

class UserCreate(UserBase):
    password: str # Password for creation, will be hashed by CRUD

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None # To allow password updates

class User(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime
    businesses: List[Business] = [] # List of businesses owned by the user

    model_config = ConfigDict(from_attributes=True)

# Update forward references for nested schemas after all models are defined
# Pydantic V2 uses model_rebuild()
Business.model_rebuild()
User.model_rebuild() # User also has a List[Business]
Customer.model_rebuild()
Debt.model_rebuild()
CommunicationLog.model_rebuild()


# ---- Token Schemas for Authentication ----
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
    scopes: List[str] = []

# ---- Letter Generation Schemas ----
class LetterGenerationRequest(BaseModel):
    letter_type: str
    state: str # For state-specific legal context, e.g., "NSW", "VIC"

class PlainTextResponse(BaseModel):
    content: str

# ---- Reporting Schemas ----
class ReportSummarySchema(BaseModel):
    total_outstanding_debt: Decimal
    overdue_accounts_count: int
    average_overdue_days: float

class DebtStatusItemSchema(BaseModel):
    status: str
    count: int
    total_amount: Decimal

class DebtStatusReportSchema(BaseModel):
    status_breakdown: List[DebtStatusItemSchema]
