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

# --- Database Configuration ---
import os
#SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app_main.db")
# Using a simpler default for now if .env is not used, adjust as needed.
# Ensure the path is relative to where the app runs or use an absolute path.
# For SQLite, the path will be relative to the project root if running from there.
DATABASE_URL_FROM_ENV = os.getenv("DATABASE_URL")
if DATABASE_URL_FROM_ENV:
    SQLALCHEMY_DATABASE_URL = DATABASE_URL_FROM_ENV
else:
    # Default to a local SQLite DB file in the 'app' directory if DATABASE_URL is not set
    # This helps with initial setup without requiring .env immediately.
    # In production, DATABASE_URL should ALWAYS be set.
    # For SQLite, it's sqlite:///./your_db_file.db
    # The ./ means relative to the current working directory when the app starts.
    # If main.py is in /app, then ./app_main.db would be /app/app_main.db
    # Let's make it relative to project root /app for consistency with alembic.ini's example.
    SQLALCHEMY_DATABASE_URL = "sqlite:///./app_main.db"
    print(f"WARNING: DATABASE_URL environment variable not set. Using default SQLite DB: {SQLALCHEMY_DATABASE_URL}")


# --- Other Configurations ---
# DEBUG_MODE = os.getenv("DEBUG_MODE", "False").lower() == "true"
