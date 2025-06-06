import pytest
from unittest.mock import patch, MagicMock # Added MagicMock
from app.backend.llm.letter_generator import generate_letter_content
from typing import Dict, Any # Added Any

# Common sample data for tests
SAMPLE_DEBT_DATA: Dict[str, Any] = {
    "outstanding_amount": "1250.75",
    "due_date": "2023-03-15",
    "invoice_number": "INV-001",
    "is_potentially_statute_barred": False # Default
}
SAMPLE_BUSINESS_DATA: Dict[str, Any] = {
    "business_name": "Test Creditor Inc.",
    "abn": "11223344555" # Example ABN
}
SAMPLE_CUSTOMER_DATA: Dict[str, Any] = {
    "customer_name": "John Debtor",
    "address": "123 Main St, Anytown, NSW 2000" # Example address
}
DEFAULT_LETTER_TYPE = "initial_reminder"
DEFAULT_STATE = "NSW"

# Ensure openai.api_key is None or dummy for these tests as we mock the call
# This is handled by app.config.LLM_API_KEY = "" and the check in letter_generator.py
# If LLM_API_KEY is "", generate_letter_content returns an error before making an API call.
# To properly test the prompt construction, we need to ensure the API call part is reached.
# This can be done by either:
# 1. Setting a dummy openai.api_key before calling generate_letter_content in tests.
# 2. Patching the `openai.api_key` check within generate_letter_content itself for tests.
# For simplicity, we'll assume the mock of `openai.ChatCompletion.create` bypasses the key check
# if `generate_letter_content` doesn't error out before that due to the empty key from config.
# The `generate_letter_content` currently has:
#   if not openai.api_key: return "Error generating letter: LLM API key not configured."
# This means for these tests to work, we *must* patch this check or set a dummy key.

def test_prompt_structure_and_standard_inclusions():
    """Test the basic structure of the prompt and inclusion of standard data."""
    with patch('app.backend.llm.letter_generator.openai.api_key', "dummy_key_for_testing_context_mgr"), \
         patch('app.backend.llm.letter_generator.openai.ChatCompletion.create') as mock_cc_create:

        mock_response = MagicMock()
        mock_response.choices[0].message = {'content': "Mocked LLM response."}
        mock_cc_create.return_value = mock_response

        generate_letter_content(
            debt_data=SAMPLE_DEBT_DATA,
            letter_type=DEFAULT_LETTER_TYPE,
            business_data=SAMPLE_BUSINESS_DATA,
            customer_data=SAMPLE_CUSTOMER_DATA,
            state=DEFAULT_STATE
        )

        mock_cc_create.assert_called_once()
        call_args = mock_cc_create.call_args
        messages = call_args[1]['messages'] # messages is a kwarg

    assert messages[0]['role'] == 'system'
    assert SAMPLE_BUSINESS_DATA["business_name"] in messages[0]['content']
    assert SAMPLE_CUSTOMER_DATA["customer_name"] in messages[0]['content']
    assert SAMPLE_DEBT_DATA["outstanding_amount"] in messages[0]['content']
    assert SAMPLE_DEBT_DATA["due_date"] in messages[0]['content']

    assert messages[1]['role'] == 'user'
    user_prompt = messages[1]['content']
    assert DEFAULT_LETTER_TYPE in user_prompt
    assert "National Debt Helpline (1800 007 007)" in user_prompt
    assert "moneysmart.gov.au" in user_prompt


def test_prompt_qld_specific_text():
    """Test QLD-specific text is included in the prompt only for QLD."""
    with patch('app.backend.llm.letter_generator.openai.api_key', "dummy_key_for_testing_context_mgr"), \
         patch('app.backend.llm.letter_generator.openai.ChatCompletion.create') as mock_cc_create:

        mock_response = MagicMock()
        mock_response.choices[0].message = {'content': "Mocked QLD response."}
        mock_cc_create.return_value = mock_response
        qld_statement = "under Queensland regulations, we will only contact you via mail, email, or phone."

        # Test with QLD
        generate_letter_content(SAMPLE_DEBT_DATA, DEFAULT_LETTER_TYPE, SAMPLE_BUSINESS_DATA, SAMPLE_CUSTOMER_DATA, "QLD")
        mock_cc_create.assert_called_once()
        messages_qld = mock_cc_create.call_args[1]['messages']
        assert qld_statement in messages_qld[1]['content']
        mock_cc_create.reset_mock()

        # Test with VIC (non-QLD)
        generate_letter_content(SAMPLE_DEBT_DATA, DEFAULT_LETTER_TYPE, SAMPLE_BUSINESS_DATA, SAMPLE_CUSTOMER_DATA, "VIC")
        mock_cc_create.assert_called_once()
        messages_vic = mock_cc_create.call_args[1]['messages']
        assert qld_statement not in messages_vic[1]['content']


def test_prompt_statute_barred_warning():
    """Test statute-barred warning is included when relevant."""
    with patch('app.backend.llm.letter_generator.openai.api_key', "dummy_key_for_testing_context_mgr"), \
         patch('app.backend.llm.letter_generator.openai.ChatCompletion.create') as mock_cc_create:

        mock_response = MagicMock()
        mock_response.choices[0].message = {'content': "Mocked statute response."}
        mock_cc_create.return_value = mock_response
        statute_warning = "debt may be statute-barred and they should seek independent legal advice"

        # Test with statute_barred = True
        debt_data_statute = {**SAMPLE_DEBT_DATA, "is_potentially_statute_barred": True}
        generate_letter_content(debt_data_statute, DEFAULT_LETTER_TYPE, SAMPLE_BUSINESS_DATA, SAMPLE_CUSTOMER_DATA, DEFAULT_STATE)
        mock_cc_create.assert_called_once()
        messages_statute_true = mock_cc_create.call_args[1]['messages']
        assert statute_warning in messages_statute_true[1]['content']
        mock_cc_create.reset_mock()

        # Test with statute_barred = False
        debt_data_no_statute = {**SAMPLE_DEBT_DATA, "is_potentially_statute_barred": False}
        generate_letter_content(debt_data_no_statute, DEFAULT_LETTER_TYPE, SAMPLE_BUSINESS_DATA, SAMPLE_CUSTOMER_DATA, DEFAULT_STATE)
        mock_cc_create.assert_called_once()
        messages_statute_false = mock_cc_create.call_args[1]['messages']
        assert statute_warning not in messages_statute_false[1]['content']


def test_generate_letter_content_no_api_key():
    """Test that an error message is returned if OpenAI API key is not configured."""
    with patch('app.backend.llm.letter_generator.openai.api_key', ""): # Patch api_key to be empty
        result = generate_letter_content(
            SAMPLE_DEBT_DATA, DEFAULT_LETTER_TYPE, SAMPLE_BUSINESS_DATA, SAMPLE_CUSTOMER_DATA, DEFAULT_STATE
        )
    assert "Error generating letter: LLM API key not configured." in result


def test_llm_api_error_handling():
    """Test handling of OpenAI APIError."""
    with patch('app.backend.llm.letter_generator.openai.api_key', "dummy_key_for_testing_context_mgr"), \
         patch('app.backend.llm.letter_generator.openai.ChatCompletion.create') as mock_cc_create:

        from app.backend.llm.letter_generator import openai # For openai.APIError
        # For openai >= 1.0, APIError constructor is different.
        # Simple message is enough to trigger the exception type.
        # If more specific error properties (like status_code) are needed by the handler,
        # a more complex mock response object would be needed.
        mock_cc_create.side_effect = openai.APIError("Simulated API Error from OpenAI", request=MagicMock(), body=None) # type: ignore

        result = generate_letter_content(
            SAMPLE_DEBT_DATA, DEFAULT_LETTER_TYPE, SAMPLE_BUSINESS_DATA, SAMPLE_CUSTOMER_DATA, DEFAULT_STATE
        )
        assert "Error generating letter: Could not connect to LLM service." in result
        assert "Simulated API Error" in result
        mock_cc_create.assert_called_once()
