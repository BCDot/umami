# Project Title: AI-Powered Debt Collection Assistant

## 1. Project Overview

This project is an AI-powered web application designed to assist businesses with the debt collection process. It aims to automate communication, manage customer and debt information, and provide tools for generating legally compliant collection letters. The system will leverage Large Language Models (LLMs) to help draft personalized and effective communication.

## 2. Tech Stack

*   **Backend:**
    *   **Language:** Python 3.10+
    *   **Framework:** FastAPI (for building RESTful APIs)
    *   **ORM:** SQLAlchemy (for database interaction)
    *   **Data Validation:** Pydantic (for request/response data validation and settings management)
    *   **Authentication:** JWT (JSON Web Tokens) with Passlib (for password hashing) and Python-JOSE (for JWT creation/verification)
    *   **LLM Integration:** Placeholder for libraries like OpenAI, Langchain, etc.
*   **Database:** PostgreSQL (production recommendation), SQLite (development/testing)
*   **Frontend:** (Basic HTML templates for now, can be expanded to a JS framework like React/Vue)
    *   HTML5, CSS3
    *   Jinja2 for templating (if using FastAPI's default templating)
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
git clone <your-repository-url>
cd <project-directory-name>
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
Create a `.env` file in the project root directory by copying from a `.env_example` (if provided) or by creating it manually. This file will store sensitive configuration.
Key environment variables include:

*   `DATABASE_URL`: The connection string for your database.
    *   Example for PostgreSQL: `postgresql://user:password@host:port/database_name`
    *   Example for SQLite (local file): `sqlite:///./your_database.db`
*   `LLM_API_KEY`: Your API key for the chosen Large Language Model provider.
*   `SECRET_KEY`: A secret key for JWT token generation (should be long, random, and kept private).
*   `ALGORITHM`: The algorithm used for JWT, e.g., `HS256`.
*   `ACCESS_TOKEN_EXPIRE_MINUTES`: Lifetime for access tokens, e.g., `30`.

**Note:** For development, some of these might have default placeholders in `app/config.py` or other config files, but should always be set via environment variables in production.

### 3.6. Running Database Migrations (If Applicable)
If using a tool like Alembic for database migrations (not explicitly set up yet, but good practice):
```bash
# alembic upgrade head # (Example command)
```
For now, SQLAlchemy's `Base.metadata.create_all()` is used in testing, which creates tables based on models. A similar script might be needed for development/production setup if not using Alembic.

### 3.7. Running the Application
The application is expected to be run using Uvicorn, a fast ASGI server.
```bash
# Assuming your FastAPI app instance is named 'app' in 'app/main.py' (not created yet)
# Adjust the path 'app.main:app' as necessary.
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
The `--reload` flag is useful for development as it automatically reloads the server when code changes.

## 4. Backend Architecture Overview

The backend code is primarily located within the `app/backend/` directory and is structured as follows:

*   **`app/backend/core/`**: Contains core business logic, including:
    *   `models.py`: SQLAlchemy database models.
    *   `schemas.py`: Pydantic schemas for data validation and serialization.
    *   `crud.py`: CRUD (Create, Read, Update, Delete) operations for database models.
    *   `reports.py`: Functions for generating report data.
*   **`app/backend/llm/`**: Houses modules related to Large Language Model interactions.
    *   `letter_generator.py`: Functions for generating letter content using LLMs.
*   **`app/backend/auth/`**: Contains authentication and authorization logic.
    *   `security.py`: Password hashing, JWT token creation, and verification utilities.
    *   `endpoints.py`: API endpoints related to authentication (login, registration).
*   **`app/backend/routers/`**: Includes FastAPI routers for different API resource groups.
    *   `communications.py`: API endpoints for managing communication logs.
    *   `reports.py`: API endpoints for accessing reports.
    *   (Other routers for users, businesses, customers, debts would be added here).
*   **`app/config.py`**: (At `app/` level) Application configuration settings, potentially loading from environment variables.

## 5. Testing

Tests are located in the `tests/backend_tests/` directory. To run the tests:

1.  Ensure you have installed all development dependencies (including `pytest` and `pytest-cov`) from `requirements.txt`.
2.  Navigate to the project root directory.
3.  Run Pytest:
    ```bash
    python -m pytest -v tests/backend_tests/
    ```
    Or, for a coverage report:
    ```bash
    pytest --cov=app tests/backend_tests/
    # To generate an HTML coverage report:
    # pytest --cov=app --cov-report=html tests/backend_tests/
    # open htmlcov/index.html
    ```

## 6. Next Steps / Future Enhancements (Placeholder)
*   Full implementation of CRUD operations.
*   Development of a main FastAPI application file (`app/main.py`).
*   Integration with a real LLM API.
*   Frontend interface development.
*   Comprehensive error handling and logging.
*   Database migration setup (e.g., Alembic).
