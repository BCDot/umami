from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone # Added timezone for utcnow comparison

from app.backend.core import crud, models, schemas
from app.backend.auth.security import get_current_active_user
from app.backend.llm.letter_generator import generate_letter_content
from app.backend.db.session import get_db # Updated import

router = APIRouter(
    prefix="/actions",
    tags=["Actions"],
)

def get_authorized_business_id(current_user: models.User) -> int:
    """Helper to get the user's first business ID or raise error if none."""
    if not current_user.businesses:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User has no associated businesses."
        )
    return current_user.businesses[0].id

@router.post("/debts/{debt_id}/generate-letter-preview", response_model=schemas.PlainTextResponse)
async def generate_letter_preview_endpoint(
    debt_id: int,
    letter_request: schemas.LetterGenerationRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Generates a preview of a collection letter for a specific debt.
    The user must own the business associated with the debt.
    """
    if not db:
        # If DB is not available (placeholder), and LLM_API_KEY is also not set,
        # we can return a more specific placeholder or the LLM's own error message.
        # For now, rely on generate_letter_content to handle API key issues.
        # If LLM also fails due to no key, it will return its error message.
        print(f"[ACTIONS_ROUTER_PLACEHOLDER] DB not configured. Proceeding with letter generation which might use mock/error data.")
        # Fallback to allow LLM call even if DB isn't there (it will use placeholders)
        # This is for structural testing; real app would require DB.
        # We need dummy data for business, customer, debt if db is None.
        business_data_dict = {"business_name": "Placeholder Business Inc."}
        customer_data_dict = {"customer_name": "Placeholder Customer"}
        # Simplified debt_data for placeholder scenario without DB
        debt_data_dict = {
            "outstanding_amount": "100.00", # Example
            "due_date": "2023-01-01",       # Example
            "invoice_number": "INV-PLACEHOLDER",
            "is_potentially_statute_barred": False # Default
        }
        # Attempt to call generate_letter_content with placeholder data
        generated_text = generate_letter_content(
            debt_data=debt_data_dict,
            letter_type=letter_request.letter_type,
            business_data=business_data_dict,
            customer_data=customer_data_dict,
            state=letter_request.state
        )
        return schemas.PlainTextResponse(content=generated_text)


    authorized_business_id = get_authorized_business_id(current_user)
    db_debt = crud.get_debt(db, debt_id=debt_id, business_id=authorized_business_id)

    if not db_debt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Debt not found or not authorized for this user."
        )

    # Prepare data for the letter generator
    # Ensure all fields accessed here are loaded on db_debt, db_debt.customer, db_debt.business
    # May need to check for None if relationships are nullable or data is incomplete.
    if not db_debt.customer:
         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer data not found for this debt.")
    if not db_debt.business: # Should always exist if authorized_business_id worked, but good check
         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Business data not found for this debt.")


    debt_data_dict = {
        "outstanding_amount": str(db_debt.outstanding_amount), # Convert Decimal to string
        "due_date": db_debt.due_date.isoformat() if db_debt.due_date else "N/A",
        "invoice_number": db_debt.invoice_number or "N/A",
        # Simplified statute-barred check
        "is_potentially_statute_barred": (datetime.now(timezone.utc).date() - db_debt.due_date).days > (6 * 365) if db_debt.due_date else False,
        # Add any other debt fields needed by the prompt
    }
    customer_data_dict = {
        "customer_name": db_debt.customer.customer_name,
        "address": db_debt.customer.address, # Assuming address is needed by LLM
        # Add any other customer fields
    }
    business_data_dict = {
        "business_name": db_debt.business.business_name,
        "abn": db_debt.business.abn or "N/A", # Assuming ABN is needed
        # Add any other business fields
    }

    generated_text = generate_letter_content(
        debt_data=debt_data_dict,
        letter_type=letter_request.letter_type,
        business_data=business_data_dict,
        customer_data=customer_data_dict,
        state=letter_request.state
    )

    # Before returning, check if the generated text indicates an error from the LLM
    if generated_text.startswith("Error generating letter:"):
        # Specific known errors can be handled with different status codes if needed
        if "LLM API key not configured" in generated_text:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=generated_text)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=generated_text)

    return schemas.PlainTextResponse(content=generated_text)


@router.post("/debts/{debt_id}/generate-email-content", response_model=schemas.EmailContentResponse)
async def generate_email_content_endpoint(
    debt_id: int,
    letter_request: schemas.LetterGenerationRequest, # Reusing this for letter_type and state
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Generates email subject and body content for a specific debt.
    The user must own the business associated with the debt.
    """
    db_debt = crud.get_debt_by_id_for_user(db, debt_id=debt_id, user_id=current_user.id)

    if not db_debt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Debt not found or not authorized for this user."
        )

    if not db_debt.customer or not db_debt.customer.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Customer email not found for this debt."
        )
    recipient_email = db_debt.customer.email

    # Prepare data for the letter/email content generator
    if not db_debt.business: # Should be guaranteed by get_debt_by_id_for_user if correctly implemented
         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Business data not found for this debt unexpectedly.")

    debt_data_dict = {
        "outstanding_amount": str(db_debt.outstanding_amount),
        "due_date": db_debt.due_date.isoformat() if db_debt.due_date else "N/A",
        "invoice_number": db_debt.invoice_number or str(db_debt.id), # Fallback to debt_id if no invoice number
        "is_potentially_statute_barred": (datetime.now(timezone.utc).date() - db_debt.due_date).days > (6 * 365) if db_debt.due_date else False,
        # Add other relevant debt fields
        "original_amount": str(db_debt.original_amount),
        "status": db_debt.status,
        "debt_type": db_debt.debt_type or "Outstanding Account",
        "service_description": getattr(db_debt, 'service_description', None) or db_debt.debt_type or "services rendered", # Assuming service_description exists or fallback
    }
    customer_data_dict = {
        "customer_name": db_debt.customer.customer_name,
        "address": db_debt.customer.address,
        "email": db_debt.customer.email,
        # Add other relevant customer fields
    }
    business_data_dict = {
        "business_name": db_debt.business.business_name,
        "abn": db_debt.business.abn or "N/A",
        "contact_email": db_debt.business.contact_email,
        "contact_phone": db_debt.business.contact_phone or "N/A",
        "address": db_debt.business.address or "N/A",
        # Add other relevant business fields
    }

    email_body = generate_letter_content(
        debt_data=debt_data_dict,
        letter_type=letter_request.letter_type, # Re-using letter_type for email tone/content
        business_data=business_data_dict,
        customer_data=customer_data_dict,
        state=letter_request.state
    )

    if email_body.startswith("Error generating letter:"):
        if "LLM API key not configured" in email_body:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=email_body)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=email_body)

    subject = f"Regarding Your Account with {db_debt.business.business_name} - Ref: {db_debt.invoice_number or db_debt.id}"

    return schemas.EmailContentResponse(
        recipient_email=recipient_email,
        subject=subject,
        body=email_body
    )
