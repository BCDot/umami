import pytest
from app.backend.llm.letter_generator import generate_letter_content
from typing import Dict

def test_generate_letter_content_runs():
    """
    Test that generate_letter_content runs without error and returns the
    expected placeholder string. This is a basic smoke test.
    """
    debt_data: Dict = {"amount": "100.50", "due_date": "2023-01-01", "invoice_number": "INV001"}
    business_data: Dict = {"name": "Test Business Ltd", "abn": "12345678901"}
    customer_data: Dict = {"name": "Test Customer", "address": "123 Test St, Testville"}
    letter_type: str = "initial_reminder"
    state: str = "NSW"

    expected_start_of_placeholder = f"Generated '{letter_type}' letter content based on the provided data for jurisdiction '{state}'."

    # Call the function
    generated_content = generate_letter_content(
        debt_data=debt_data,
        letter_type=letter_type,
        business_data=business_data,
        customer_data=customer_data,
        state=state
    )

    assert isinstance(generated_content, str)
    assert expected_start_of_placeholder in generated_content
    assert "[This is placeholder content. LLM integration is pending.]" in generated_content

    # More sophisticated testing would be needed in a real scenario, for example:
    # - Mocking the LLM API call if it were implemented.
    # - Validating that the constructed prompt contains the correct information
    #   from debt_data, business_data, etc.
    # - If different letter types produce structurally different placeholders,
    #   test those variations.
    # - Testing for edge cases or missing data if the function handles them.
    print(f"Test Output for {letter_type}:\n{generated_content}")


def test_generate_letter_content_different_type():
    """
    Test with a different letter type to ensure basic string construction works.
    """
    debt_data: Dict = {"amount": "250.00", "due_date": "2023-02-15"}
    business_data: Dict = {"name": "Another Creditor Inc."}
    customer_data: Dict = {"name": "Jane Debtor"}
    letter_type: str = "formal_demand_letter"
    state: str = "VIC" # Different state

    expected_start_of_placeholder = f"Generated '{letter_type}' letter content based on the provided data for jurisdiction '{state}'."

    generated_content = generate_letter_content(debt_data, letter_type, business_data, customer_data, state)

    assert isinstance(generated_content, str)
    assert expected_start_of_placeholder in generated_content
    assert "[This is placeholder content. LLM integration is pending.]" in generated_content
    print(f"Test Output for {letter_type}:\n{generated_content}")
