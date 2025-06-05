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
*   **Frontend:** (Basic HTML templates and JavaScript for now, can be expanded to a JS framework like React/Vue)
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
Create a `.env` file in the project root directory. It is good practice to create an `.env.example` file in your project root that lists all necessary environment variables with placeholder or example values. Users can then copy this to `.env` and fill in their actual secrets.

**Example `.env.example` structure:**
```ini
# --- Database Configuration ---
# Choose one DATABASE_URL format depending on your database:
# For PostgreSQL (recommended for production):
DATABASE_URL="postgresql+psycopg2://user:password@host:port/dbname"
# For SQLite (simple local file, good for development & testing if app/main.py is at project root):
# DATABASE_URL="sqlite:///./app_main.db"

# --- LLM API Key ---
# If this key is not set or is invalid, LLM letter generation will use placeholders or fail.
LLM_API_KEY="your_openai_api_key_here_or_leave_blank_to_skip_llm_calls"

# --- JWT Authentication Settings ---
# Generate a strong, random string for SECRET_KEY (e.g., using `openssl rand -hex 32`)
SECRET_KEY="your_very_strong_random_secret_key_for_jwt"
ALGORITHM="HS256" # Should match the algorithm used in app/backend/auth/security.py
ACCESS_TOKEN_EXPIRE_MINUTES=30 # Lifetime for access tokens in minutes
```

**Key Environment Variables to Configure in your `.env` file:**
*   `DATABASE_URL`: **Required.** The connection string for your database (e.g., PostgreSQL, SQLite). This is used by `app/config.py` to set up the database connection via `app/backend/db/session.py`.
*   `LLM_API_KEY`: Your API key for the chosen Large Language Model provider (e.g., OpenAI). Letter generation will fail or use placeholders if not set.
*   `SECRET_KEY`: **Required.** A strong, random secret key for JWT token generation.
*   `ALGORITHM`: The algorithm used for JWT (e.g., `HS256`), defined in `app/backend/auth/security.py`.
*   `ACCESS_TOKEN_EXPIRE_MINUTES`: Lifetime for access tokens, also defined in `app/backend/auth/security.py`.

**Note:** The application (`app/config.py`) attempts to load these from environment variables. For variables like `LLM_API_KEY`, `SECRET_KEY`, `ALGORITHM`, and `ACCESS_TOKEN_EXPIRE_MINUTES`, ensure they are correctly set in your environment or `.env` file for full functionality and security.

### 3.6. Database Setup
This project uses SQLAlchemy as the ORM and Alembic for managing database migrations. Database session management for the FastAPI application is handled by the `get_db` dependency defined in `app/backend/db/session.py`, which is utilized by API routers. This same dependency is overridden during testing to ensure a consistent and isolated test database environment.

1.  **Ensure `DATABASE_URL` is configured**: Set the `DATABASE_URL` in your `.env` file as described in the Environment Variables section. This URL is read by `app/config.py` and used by `app/backend/db/session.py` to create the SQLAlchemy engine.
2.  **Create the Database (if needed)**: For database systems like PostgreSQL, you must manually create the database instance itself before Alembic can manage its schema. For SQLite, the database file specified in `DATABASE_URL` (e.g., `./app_main.db`) will be created automatically in the project root if it doesn't exist when migrations are run or the app connects.
    ```sql
    -- Example for PostgreSQL:
    -- CREATE DATABASE your_database_name;
    ```
3.  **Run Database Migrations**: Apply all pending database migrations to set up or update your database schema to the latest version. The `alembic.ini` file at the project root is configured to find the migration scripts located in `app/backend/db/migrations/`.
    ```bash
    # Ensure your virtual environment is active and you are in the project root
    python -m alembic -c alembic.ini upgrade head
    ```

### 3.7. Running the Application
Ensure the database is created (if necessary for your chosen DB system) and migrations are applied using the command above before running the application for the first time.

The application is run using Uvicorn, an ASGI server. The main FastAPI application instance, named `app`, is defined in `app/main.py`.
```bash
# Run from the project root directory:
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
*   `app.main:app`: Points to the `app` instance of `FastAPI` located within the `/app/main.py` file.
*   `--reload`: Enables auto-reload for development, so the server restarts on code changes.
*   `--host 0.0.0.0`: Makes the server accessible from your local network.
*   `--port 8000`: Specifies the port to run on.

You should then be able to access the API root at `http://localhost:8000/` or `http://127.0.0.1:8000/`, and API endpoints under `/api/v1/` (e.g., `http://localhost:8000/api/v1/auth/token`).

## 4. Backend Architecture Overview

The backend code is primarily located within the `app/` directory, with core logic in `app/backend/`:

*   **`app/main.py`**: The main FastAPI application entry point, where the app is initialized and routers are included.
*   **`app/config.py`**: Handles application configuration, including loading settings from environment variables.
*   **`app/backend/core/`**: Contains core business logic:
    *   `models.py`: SQLAlchemy database models (schema definition).
    *   `schemas.py`: Pydantic schemas for API data validation and serialization.
    *   `crud.py`: CRUD (Create, Read, Update, Delete) database operations.
    *   `reports.py`: Functions for generating report data from the database.
*   **`app/backend/db/`**: Database-specific modules:
    *   `session.py`: Defines the SQLAlchemy engine, `SessionLocal`, and the `get_db` dependency for FastAPI.
    *   `migrations/`: Contains Alembic migration scripts, `env.py` for Alembic runtime configuration. (Note: `alembic.ini` is at the project root).
*   **`app/backend/llm/`**: Modules for Large Language Model interactions.
    *   `letter_generator.py`: Logic for constructing prompts and calling LLM APIs to generate letter content.
*   **`app/backend/auth/`**: Authentication and authorization components.
    *   `security.py`: Password hashing, JWT token creation/verification, and `get_current_user` dependency.
    *   `endpoints.py`: API endpoints for user registration and login (`/auth/token`).
*   **`app/backend/routers/`**: FastAPI routers for different API resource groups.
    *   `actions.py`: Endpoints for specific actions like letter generation.
    *   `businesses.py`: Endpoints for managing business entities.
    *   `communications.py`: Endpoints for communication logs.
    *   `reports.py`: Endpoints for accessing aggregated report data.

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
*   Frontend interface development (e.g., using React, Vue, or enhancing server-side templates).
*   More sophisticated error handling, logging, and background task management.
*   Deployment scripts and configurations (e.g., Docker).
*   Refinement of LLM prompts and integration.
*   User management features (e.g., roles, permissions).
*   Multi-tenancy considerations for businesses if required.
