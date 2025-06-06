from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, DateTime, Text, Numeric, Boolean
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func
import datetime # Ensure datetime is imported for default values

Base = declarative_base()

class Business(Base):
    __tablename__ = "businesses"

    id = Column(Integer, primary_key=True, index=True)
    business_name = Column(String, nullable=False)
    abn = Column(String, unique=True, index=True, nullable=True)
    contact_email = Column(String, nullable=False)
    contact_phone = Column(String, nullable=True)
    address = Column(String, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    customers = relationship("Customer", back_populates="business")
    debts = relationship("Debt", back_populates="business")
    owner = relationship("User", back_populates="businesses")

    def __repr__(self):
        return f"<Business(id={self.id}, business_name='{self.business_name}')>"

class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    customer_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String, nullable=True)
    address = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    business = relationship("Business", back_populates="customers")
    debts = relationship("Debt", back_populates="customer")

    def __repr__(self):
        return f"<Customer(id={self.id}, customer_name='{self.customer_name}', email='{self.email}')>"

class Debt(Base):
    __tablename__ = "debts"

    id = Column(Integer, primary_key=True, index=True)
    original_amount = Column(Numeric(10, 2), nullable=False)
    outstanding_amount = Column(Numeric(10, 2), nullable=False)
    due_date = Column(Date)
    debt_type = Column(String, nullable=True)
    invoice_number = Column(String, nullable=True, index=True)
    status = Column(String, nullable=False, default='Outstanding')
    notes = Column(Text, nullable=True)
    is_archived = Column(Boolean, default=False)

    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    customer = relationship("Customer", back_populates="debts")
    business = relationship("Business", back_populates="debts")
    communication_logs = relationship("CommunicationLog", back_populates="debt", cascade="all, delete-orphan", lazy="selectin")
    payments = relationship("Payment", back_populates="debt", cascade="all, delete-orphan", lazy="selectin")

    def __repr__(self):
        return f"<Debt(id={self.id}, original_amount={self.original_amount}, status='{self.status}')>"

class CommunicationLog(Base):
    __tablename__ = "communication_logs"

    id = Column(Integer, primary_key=True, index=True)
    debt_id = Column(Integer, ForeignKey("debts.id"), nullable=False)
    communication_type = Column(String, nullable=True)
    date_sent = Column(DateTime(timezone=True), server_default=func.now())
    llm_prompt_used = Column(Text, nullable=True)
    generated_content_snapshot = Column(Text, nullable=True)
    status = Column(String, nullable=True)
    response_received = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    debt = relationship("Debt", back_populates="communication_logs")

    def __repr__(self):
        return f"<CommunicationLog(id={self.id}, debt_id={self.debt_id}, type='{self.communication_type}', date_sent='{self.date_sent}')>"

class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    debt_id = Column(Integer, ForeignKey('debts.id'), nullable=False, index=True)
    amount_paid = Column(Numeric(10, 2), nullable=False)
    payment_date = Column(Date, nullable=False, default=datetime.date.today) # Use imported Date
    payment_method = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    debt = relationship("Debt", back_populates="payments")

    def __repr__(self):
        return f"<Payment(id={self.id}, debt_id={self.debt_id}, amount_paid={self.amount_paid}, payment_date='{self.payment_date}')>"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    businesses = relationship("Business", back_populates="owner")

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"
