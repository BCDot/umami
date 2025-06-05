# Project Title: AI-Powered Debt Collection Assistant

## 1. Project Overview

This project is an AI-powered web application designed to assist businesses with the debt collection process. It aims to automate communication, manage customer and debt information, and provide tools for generating legally compliant collection letters. The system will leverage Large Language Models (LLMs) to help draft personalized and effective communication.

## 2. Tech Stack

*   **Backend:**
    *   **Language:** Python 3.10+
    *   **Framework:** FastAPI (for building RESTful APIs)
    *   **ORM:** SQLAlchemy (for database interaction)
    *   **Database Migrations:** Alembic
    *   **Data Validation:** Pydantic (for request/response data validation and settings management)
    *   **Authentication:** JWT (JSON Web Tokens) with Passlib (for password hashing) and Python-JOSE (for JWT creation/verification)
    *   **LLM Integration:** OpenAI API (or other LLM providers)
*   **Database:** PostgreSQL (production recommendation), SQLite (development/testing)
*   **Frontend:** (Basic HTML templates for now, can be expanded to a JS framework like React/Vue)
    *   HTML5, CSS3, JavaScript
    *   Jinja2 for templating (if using FastAPI's default templating with Python backend serving HTML)
*   **Testing:**
    *   Pytest (for running tests)
    *   Pytest-Cov (for coverage reports)
*   **Environment Management:** Python-dotenv (for managing environment variables)

## 3. Setup and Installation

### 3.1. Prerequisites
*   Python 3.10 or higher
*   Pip (Python package installer)
*   Git

### 3.2. Cloning the Repository
```bash
git clone <your-repository-url> # Replace <your-repository-url> with the actual URL
cd <project-directory-name>   # Replace <project-directory-name> with the folder name
```

### 3.3. Setting up a Virtual Environment
It's highly recommended to use a virtual environment:
```bash
# For Linux/macOS
python3 -m venv venv
source venv/bin/activate

# For Windows
python -m venv venv
.\venv\Scripts\activate
```

### 3.4. Installing Dependencies
Install all required packages from `requirements.txt`:
```bash
pip install -r requirements.txt
```

### 3.5. Environment Variables
Create a `.env` file in the project root directory. You can copy from `.env.example` (you should create this file in your project root as a template for users) or create it manually. This file will store sensitive and environment-specific configurations.

**Example `.env.example` structure:**
```ini
# --- Database Configuration ---
# Choose one DATABASE_URL format depending on your database:
# For PostgreSQL (recommended for production):
DATABASE_URL="postgresql+psycopg2://user:password@host:port/dbname"
# For SQLite (simple local file, good for development & testing, ensure path is correct):
# DATABASE_URL="sqlite:///./app_main.db"

# --- LLM API Key ---
# If this key is not set or is invalid, LLM letter generation will use placeholders or fail.
LLM_API_KEY="your_openai_api_key_here_or_leave_blank_if_not_using_real_llm_calls"

# --- JWT Authentication Settings ---
# Generate a strong, random string for SECRET_KEY (e.g., using `openssl rand -hex 32`)
SECRET_KEY="your_very_strong_random_secret_key_for_jwt"
ALGORITHM="HS256" # Should match the algorithm used in auth/security.py
ACCESS_TOKEN_EXPIRE_MINUTES=30 # Lifetime for access tokens in minutes
```

**Key Environment Variables to Configure:**
*   `DATABASE_URL`: The connection string for your database.
*   `LLM_API_KEY`: Your API key for the chosen Large Language Model provider (e.g., OpenAI).
*   `SECRET_KEY`: A secret key for JWT token generation.
*   `ALGORITHM`: The algorithm used for JWT (e.g., `HS256`).
*   `ACCESS_TOKEN_EXPIRE_MINUTES`: Lifetime for access tokens.

**Note:** For development, some of these might have default placeholders (like the empty `LLM_API_KEY` in `app/config.py`), but should always be set via environment variables for security and proper functionality, especially in production. The application should be coded to prioritize environment variables over hardcoded defaults.

### 3.6. Database Setup
This project uses SQLAlchemy as the ORM and Alembic for managing database migrations.

1.  **Ensure `DATABASE_URL` is configured**: Set the `DATABASE_URL` in your `.env` file as described in the Environment Variables section.
2.  **Create the Database (if needed)**: For database systems like PostgreSQL, you need to manually create the database instance itself before Alembic can manage its schema. For SQLite, the database file will be created automatically if it doesn't exist when migrations are run or the app connects.
    ```sql
    -- Example for PostgreSQL:
    -- CREATE DATABASE your_database_name;
    ```
3.  **Run Database Migrations**: Apply all pending database migrations to set up or update your database schema to the latest version. The `alembic.ini` file at the project root is configured to find the migration scripts.
    ```bash
    # Ensure your virtual environment is active and you are in the project root
    python -m alembic -c alembic.ini upgrade head
    ```

### 3.7. Running the Application
Ensure the database is created (if necessary) and migrations are applied before running the application for the first time.

The application is run using Uvicorn, an ASGI server. The main FastAPI application instance is typically defined in `app/main.py`.
```bash
# Assuming your FastAPI app instance is named 'app' in 'app/main.py' (this file needs to be created)
# Run from the project root directory:
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
*   `app.main:app`: Points to the `app` instance of `FastAPI` within the `app/main.py` file.
*   `--reload`: Enables auto-reload for development, so the server restarts on code changes.
*   `--host 0.0.0.0`: Makes the server accessible from your local network.
*   `--port 8000`: Specifies the port to run on.

You should then be able to access the API at `http://localhost:8000` (or `http://127.0.0.1:8000`).

## 4. Backend Architecture Overview

The backend code is primarily located within the `app/backend/` directory and is structured as follows:

*   **`app/backend/core/`**: Contains core business logic:
    *   `models.py`: SQLAlchemy database models.
    *   `schemas.py`: Pydantic schemas for data validation and serialization.
    *   `crud.py`: CRUD (Create, Read, Update, Delete) operations for database models.
    *   `reports.py`: Functions for generating report data.
*   **`app/backend/db/`**: Database-related utilities.
    *   `migrations/`: Contains Alembic migration scripts and configuration (`env.py`). Note: `alembic.ini` is at the project root.
*   **`app/backend/llm/`**: Modules related to Large Language Model interactions.
    *   `letter_generator.py`: Functions for generating letter content using LLMs.
*   **`app/backend/auth/`**: Authentication and authorization logic.
    *   `security.py`: Password hashing, JWT token utilities, and dependency for current user.
    *   `endpoints.py`: API endpoints for authentication (login, registration).
*   **`app/backend/routers/`**: FastAPI routers for different API resource groups.
    *   `actions.py`: Endpoints for performing actions like generating letter previews.
    *   `businesses.py`: API endpoints for managing businesses.
    *   `communications.py`: API endpoints for managing communication logs.
    *   `reports.py`: API endpoints for accessing reports.
    *   (Other routers for users, customers, debts would be added here).
*   **`app/config.py`**: (At `app/` level) Application configuration settings, potentially loading from environment variables. It provides default values if environment variables are not set.

## 5. Testing

Tests are located in the `tests/backend_tests/` directory.

1.  Ensure you have installed all development dependencies (including `pytest` and `pytest-cov`) from `requirements.txt`.
2.  Navigate to the project root directory.
3.  Run Pytest:
    ```bash
    # Run all tests with verbose output
    python -m pytest -v tests/backend_tests/
    ```
    Or, for a coverage report:
    ```bash
    # Run tests and generate coverage report for the 'app' directory
    python -m pytest --cov=app tests/backend_tests/

    # To generate an HTML coverage report (after running with --cov):
    # coverage html
    # open htmlcov/index.html
    ```

## 6. Next Steps / Future Enhancements (Placeholder)
*   Full implementation of all CRUD operations and remaining API endpoints.
*   Development of a main FastAPI application file (`app/main.py`) to tie all routers and configurations together.
*   Frontend interface development (e.g., using React, Vue, or enhancing server-side templates).
*   More sophisticated error handling, logging, and background task management.
*   Deployment scripts and configurations (e.g., Docker).
*   Refinement of LLM prompts and integration.
