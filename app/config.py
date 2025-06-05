# Application-wide configurations

# Application-wide configurations

# --- LLM API Key ---
# IMPORTANT: Set your actual OpenAI API key here or (preferably) via an environment variable.
# If this key is not set or is invalid, the LLM letter generation will fail.
# For local development, you can set it directly. For production, use environment variables.
# Example using environment variable (requires python-dotenv and os module):
# import os
# from dotenv import load_dotenv
# load_dotenv()
# LLM_API_KEY = os.getenv("OPENAI_API_KEY", "")
LLM_API_KEY = "" # SET YOUR KEY HERE OR VIA ENVIRONMENT VARIABLE (e.g., OPENAI_API_KEY)

# --- Other Configurations ---
# Example: Database URL (also preferably from environment variables)
# DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./default.db")
# DEBUG_MODE = os.getenv("DEBUG_MODE", "False").lower() == "true"
