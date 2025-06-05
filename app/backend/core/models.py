from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, DateTime, Text, Numeric, Boolean
from sqlalchemy.orm import relationship, declarative_base # Updated import
from sqlalchemy.sql import func

Base = declarative_base()

class Business(Base):
    __tablename__ = "businesses"

    id = Column(Integer, primary_key=True, index=True)
    business_name = Column(String, nullable=False)
    abn = Column(String, unique=True, index=True, nullable=True)
    contact_email = Column(String, nullable=False)
    contact_phone = Column(String, nullable=True)
    address = Column(String, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False) # Link to User

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationship: A business can have multiple customers
    customers = relationship("Customer", back_populates="business")
    # Relationship: A business can have multiple debts (directly or indirectly through customers)
    debts = relationship("Debt", back_populates="business")
    # Relationship: A business belongs to a user
    owner = relationship("User", back_populates="businesses")

    def __repr__(self):
        return f"<Business(id={self.id}, business_name='{self.business_name}')>"

class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    customer_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String)
    address = Column(String, nullable=False)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationship: A customer belongs to a business
    business = relationship("Business", back_populates="customers")
    # Relationship: A customer can have multiple debts
    debts = relationship("Debt", back_populates="customer")

    def __repr__(self):
        return f"<Customer(id={self.id}, customer_name='{self.customer_name}', email='{self.email}')>"

class Debt(Base):
    __tablename__ = "debts"

    id = Column(Integer, primary_key=True, index=True)
    original_amount = Column(Numeric(10, 2), nullable=False)
    outstanding_amount = Column(Numeric(10, 2), nullable=False)
    due_date = Column(Date)
    debt_type = Column(String) # e.g., 'Invoice', 'Loan', 'Service Fee'
    invoice_number = Column(String, nullable=True, index=True)
    status = Column(String, nullable=False, default='Outstanding') # e.g., 'Outstanding', 'Paid', 'Overdue', 'Disputed'
    notes = Column(Text, nullable=True)

    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationship: A debt belongs to a customer
    customer = relationship("Customer", back_populates="debts")
    # Relationship: A debt belongs to a business
    business = relationship("Business", back_populates="debts")
    # Relationship: A debt can have multiple communication logs
    communication_logs = relationship("CommunicationLog", back_populates="debt")

    def __repr__(self):
        return f"<Debt(id={self.id}, original_amount={self.original_amount}, status='{self.status}')>"

class CommunicationLog(Base):
    __tablename__ = "communication_logs"

    id = Column(Integer, primary_key=True, index=True)
    debt_id = Column(Integer, ForeignKey("debts.id"), nullable=False)
    communication_type = Column(String) # e.g., 'Email', 'SMS', 'Call', 'Letter'
    date_sent = Column(DateTime(timezone=True), server_default=func.now())
    llm_prompt_used = Column(Text, nullable=True)
    generated_content_snapshot = Column(Text, nullable=True) # Store the exact message sent
    status = Column(String) # e.g., 'Sent', 'Delivered', 'Failed', 'Opened', 'Responded'
    response_received = Column(Text, nullable=True) # Store any response content

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship: A communication log belongs to a debt
    debt = relationship("Debt", back_populates="communication_logs")

    def __repr__(self):
        return f"<CommunicationLog(id={self.id}, debt_id={self.debt_id}, type='{self.communication_type}', date_sent='{self.date_sent}')>"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationship: A user can own multiple businesses
    businesses = relationship("Business", back_populates="owner")

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"

# Example of how to create the tables (not to be run directly here, but for context)
# from sqlalchemy import create_engine
# DATABASE_URL = "sqlite:///./test.db" # Or your actual database URL
# engine = create_engine(DATABASE_URL)
# Base.metadata.create_all(bind=engine)
