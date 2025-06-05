from typing import Dict, Any
import openai # Import the OpenAI library
from app.config import LLM_API_KEY # Import the API key

# Configure the OpenAI API key
# This should be done once, ideally when the application starts.
# However, for this module structure, we'll set it here.
# Ensure LLM_API_KEY is set in app/config.py or via environment variables loaded into app.config
if LLM_API_KEY:
    openai.api_key = LLM_API_KEY
else:
    print("WARNING: LLM_API_KEY is not set in app.config. OpenAI calls will fail.")
    # Potentially raise an error or use a mock client if in a test environment without a key.

DEFAULT_LLM_MODEL = "gpt-3.5-turbo" # Or "gpt-4" if available and preferred

def generate_letter_content(
    debt_data: Dict[str, Any],
    letter_type: str,
    business_data: Dict[str, Any],
    customer_data: Dict[str, Any],
    state: str  # State for legal considerations, e.g., "NSW", "VIC"
) -> str:
    """
    Generates letter content using the OpenAI API based on debt, business, customer data,
    letter type, and state-specific legal considerations.

    Args:
        debt_data: Dictionary containing details of the debt.
                   Expected keys: 'outstanding_amount', 'due_date',
                                  'invoice_number' (optional),
                                  'is_potentially_statute_barred' (optional bool).
        letter_type: String indicating the type of letter (e.g., "initial_reminder", "formal_demand_letter").
        business_data: Dictionary containing details of the creditor business.
                       Expected keys: 'business_name'.
        customer_data: Dictionary containing details of the debtor customer.
                       Expected keys: 'customer_name'.
        state: The Australian state or territory for legal context.

    Returns:
        A string containing the generated letter content, or an error message string.
    """

    if not openai.api_key:
        return "Error generating letter: LLM API key not configured."

    # 1. Construct the prompt for the LLM
    system_message = f"""
    You are a helpful assistant tasked with drafting debt collection letters for a business.
    The letter should be professional, empathetic yet firm, and compliant with Australian regulations,
    specifically for the jurisdiction of {state}.
    The business collecting the debt is '{business_data.get('business_name', 'Our Company')}'.
    The customer's name is '{customer_data.get('customer_name', 'Valued Customer')}'.
    The outstanding amount is ${debt_data.get('outstanding_amount', 'the outstanding amount')}.
    The due date for this amount was {debt_data.get('due_date', 'a past date')}.
    """
    if debt_data.get('invoice_number'):
        system_message += f" This relates to invoice number {debt_data.get('invoice_number')}."

    user_prompt_instructions = [
        f"Draft a '{letter_type}' letter.",
        "The tone should be appropriate for this type of letter.",
        "Clearly state the outstanding amount and the original due date.",
        "Urge the customer to make a payment or contact us to discuss payment options.",
        "Provide contact details (use placeholders like [Your Company Phone] and [Your Company Email]).",
        "Include a reference to the National Debt Helpline (1800 007 007) and the Moneysmart website (moneysmart.gov.au) as resources for financial counseling."
    ]

    if state == 'QLD':
        user_prompt_instructions.append(
            "Also, include the following statement: 'As we are collecting this debt ourselves, please note that under Queensland regulations, we will only contact you via mail, email, or phone.'"
        )

    if debt_data.get('is_potentially_statute_barred', False):
        user_prompt_instructions.append(
            "Important: Include a sentence advising the customer that the debt may be statute-barred and they should seek independent legal advice regarding their rights and obligations."
        )

    user_message_content = "\n".join(user_prompt_instructions)

    messages = [
        {"role": "system", "content": system_message.strip()},
        {"role": "user", "content": user_message_content.strip()}
    ]

    print(f"Sending request to OpenAI with messages (excluding API key):\n{messages}")

    # 2. LLM API call
    try:
        # For newer versions of openai library (>=1.0.0), client usage is preferred:
        # from openai import OpenAI
        # client = OpenAI(api_key=LLM_API_KEY) # Or reuse a global client
        # response = client.chat.completions.create(
        # model=DEFAULT_LLM_MODEL,
        # messages=messages
        # )
        # generated_text = response.choices[0].message.content.strip()

        # Using the legacy-style call if openai library version is < 1.0.0
        # This might require openai.api_key to be set globally, which we did.
        response = openai.ChatCompletion.create(
            model=DEFAULT_LLM_MODEL,
            messages=messages
        )
        generated_text = response.choices[0].message['content'].strip()

        print(f"Received response from OpenAI: {generated_text[:200]}...")
        return generated_text

    except openai.APIError as e: # More specific error for API issues
        print(f"OpenAI API Error: {e}")
        return f"Error generating letter: Could not connect to LLM service. Details: {e}"
    except Exception as e: # Catch other potential errors
        print(f"An unexpected error occurred during LLM call: {e}")
        return f"Error generating letter: An unexpected error occurred. Details: {e}"
