# Project Title: AI-Powered Debt Collection Assistant

## 1. Project Overview

This project is an AI-powered web application designed to assist businesses with the debt collection process. It aims to automate communication, manage customer and debt information, and provide tools for generating legally compliant collection letters. The system will leverage Large Language Models (LLMs) to help draft personalized and effective communication.

## 2. Current Project Status

The project has a functional backend API built with FastAPI, SQLAlchemy, and Pydantic, supporting:
*   User authentication (registration, login with JWT).
*   CRUD operations for Businesses, Customers, Debts, and Communication Logs with ownership checks.
*   LLM integration via OpenAI for generating letter content, including conditional logic for QLD regulations and statute-barred debt notifications.
*   Reporting endpoints for financial summaries and debt status breakdowns.
*   Database session management and Alembic migrations for database schema evolution.

The frontend consists of basic HTML templates styled with CSS, and vanilla JavaScript (`app/frontend/js/main.js`) for:
*   User authentication flow (login, logout, token storage).
*   Dynamic display of Businesses, Customers, Debts, Communication Logs, and Reports.
*   Forms for creating/editing Businesses, Customers, and Debts.
*   Interactive letter generation workflow (preview, logging sent letters).
*   Global user feedback messages and loading states.

All core backend functionalities are covered by a Pytest test suite. The application is structured with separate routers for different resources and a main FastAPI app instance.

## 3. Tech Stack

*   **Backend:**
    *   **Language:** Python 3.10+
    *   **Framework:** FastAPI
    *   **ORM:** SQLAlchemy
    *   **Database Migrations:** Alembic
    *   **Data Validation:** Pydantic
    *   **Authentication:** JWT with Passlib & Python-JOSE
    *   **LLM Integration:** OpenAI API
*   **Database:** PostgreSQL (recommended), SQLite (development/testing)
*   **Frontend:**
    *   HTML5
    *   CSS3 (`app/frontend/css/style.css`)
    *   Vanilla JavaScript (`app/frontend/js/main.js`) for DOM manipulation, API calls, and core interactivity.
*   **Testing:** Pytest, Pytest-Cov
*   **Environment Management:** Python-dotenv

## 4. Setup and Installation

### 4.1. Prerequisites
*   Python 3.10 or higher, Pip, Git

### 4.2. Cloning the Repository
```bash
git clone <your-repository-url> # Replace with the actual URL
cd <project-directory-name>
```

### 4.3. Setting up a Virtual Environment
```bash
# Linux/macOS: python3 -m venv venv && source venv/bin/activate
# Windows: python -m venv venv && .\venv\Scripts\activate
```

### 4.4. Installing Dependencies
```bash
pip install -r requirements.txt
```

### 4.5. Environment Variables
Create a `.env` file in the project root (copy from a non-existent `.env.example` which you should create based on this structure):

**Example `.env.example` structure:**
```ini
# --- Database Configuration ---
DATABASE_URL="postgresql+psycopg2://user:password@host:port/dbname"
# Or for SQLite (creates 'app_main.db' in project root if not existing):
# DATABASE_URL="sqlite:///./app_main.db"

# --- LLM API Key ---
LLM_API_KEY="your_openai_api_key_here_or_leave_blank_to_skip_llm_calls"

# --- JWT Authentication Settings ---
SECRET_KEY="generate_a_strong_random_secret_key_for_jwt"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30
```
**Key Variables:** `DATABASE_URL`, `LLM_API_KEY`, `SECRET_KEY`, `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`. Ensure these are set for full functionality. `app/config.py` loads these.

### 4.6. Database Setup
The project uses SQLAlchemy and Alembic. Database session management is handled by `app/backend/db/session.py`.
1.  **Configure `DATABASE_URL`** in your `.env` file.
2.  **Create Database (if not SQLite)**: For PostgreSQL, etc., create the database manually.
    ```sql
    -- E.g., for PostgreSQL: CREATE DATABASE your_dbname;
    ```
3.  **Run Migrations**: To create/update tables based on models in `app/backend/core/models.py`.
    ```bash
    # Ensure alembic.ini at project root correctly points to migration scripts.
    python -m alembic -c alembic.ini upgrade head
    ```

### 4.7. Running the Application
Ensure the database is set up and migrations are applied. The main FastAPI app is in `app/main.py`.
```bash
# Run from the project root:
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
*   `app.main:app`: Points to the `app` FastAPI instance in `/app/main.py`.
*   `--reload`: For development auto-reload.

### 4.8. Accessing the Frontend
After starting the backend server:
1.  Open your web browser.
2.  Navigate to an entry point HTML file. A good starting point is `app/frontend/templates/login.html`. You can open this file directly in your browser (File > Open File).
3.  The application's static files (CSS, JS) are served from the `/static` route (e.g., `/static/css/style.css`). The `app/main.py` is configured to serve the entire `app/frontend` directory as `/static`. This means `login.html` (if opened directly from `app/frontend/templates/login.html`) will correctly load assets like `../css/style.css` if the HTML paths are relative, or `/static/js/main.js` if paths in HTML are absolute to the static mount point.
    *   **Note for direct file opening:** If you open `app/frontend/templates/login.html` directly, relative paths like `../css/style.css` might not work as expected if the browser's base URL context is the `templates` folder. For development, it's common to have the backend serve the primary HTML pages (like `login.html`) through dedicated FastAPI routes that render these templates. For simplicity in this project, direct file opening is assumed for initial access, with static assets correctly linked if paths are set up for it (e.g. using `/static/...` in HTML or FastAPI serving root HTML files).
    *   The current HTML templates use `url_for('static', path='...')` which implies rendering via FastAPI. If opening HTML files directly, these paths need to be changed to relative (e.g. `../js/main.js`) or absolute (e.g. `/static/js/main.js` if the browser can resolve that relative to a conceptual root if you were serving the whole `app/frontend` directory).
    *   **Recommended access for current setup**: Access API at `http://localhost:8000/api/v1/` and interact via API client or through the HTML files opened directly, understanding that `url_for` won't work in direct file opening. The static files are served under `/static`, e.g., `http://localhost:8000/static/js/main.js`.

## 5. Frontend Details

The frontend is built using vanilla HTML, CSS, and JavaScript:
*   **HTML Templates**: Located in `app/frontend/templates/`, providing the basic structure for different views (login, dashboard, lists, forms, detail pages).
*   **CSS Styling**: A single stylesheet `app/frontend/css/style.css` provides a professional and consistent base UI for all components, including global styles, typography, layout, forms, tables, buttons, and global messages.
*   **JavaScript Interactivity**: `app/frontend/js/main.js` handles all client-side logic:
    *   **Authentication Flow**: User login (token storage in `localStorage`), logout, and authentication checks (`checkAuth()`) on page loads/actions.
    *   **API Interaction**: A generic `apiRequest` function manages calls to the backend API, including setting authorization headers and basic error handling (401/403 redirects).
    *   **Dynamic Content Rendering**: Functions like `fetchAndDisplayBusinesses`, `fetchAndDisplayCustomers`, `fetchAndDisplayDebtsForBusiness/Customer`, `fetchAndDisplayDebtDetail`, `fetchAndDisplayCommunicationLogs`, `fetchAndDisplayReportSummary`, and `fetchAndDisplayDebtStatusReport` fetch data from the API and dynamically populate the HTML content (tables, lists, detail views, dashboard metrics). This includes formatting for currency and dates.
    *   **Form Handling**: Functions like `handleBusinessFormSubmit`, `handleCustomerFormSubmit`, `handleDebtFormSubmit` manage form submissions for creating and editing entities, including button disabling during processing and user feedback via global messages.
    *   **Data Loading/Editing**: Functions like `loadBusinessForEdit`, `loadCustomerForEdit`, `loadDebtForEdit` populate forms with data for editing.
    *   **Letter Generation Workflow**: `generateLetterPreview` calls the backend to get LLM-generated letter content and displays it. `logSentLetter` then logs this communication.
    *   **User Feedback**: A global messaging system (`displayGlobalMessage`) provides users with success, error, or info messages. Loading states and error messages are also displayed in relevant content areas during data fetching.

## 6. Backend Architecture Overview
(Content from previous README, with `app/main.py`, `app/config.py`, `app/backend/db/session.py`, `app/backend/db/migrations/` confirmed)
*   **`app/main.py`**: FastAPI app entry point.
*   **`app/config.py`**: Configuration.
*   **`app/backend/core/`**: Models, schemas, CRUD, reports.
*   **`app/backend/db/`**: `session.py` (DB session management), `migrations/` (Alembic).
*   **`app/backend/llm/`**: LLM interaction.
*   **`app/backend/auth/`**: Auth logic, JWT, dependencies.
*   **`app/backend/routers/`**: API routers (actions, businesses, customers, debts, communications, reports).


## 7. Testing
(Content from previous README)
```bash
python -m pytest -v tests/backend_tests/
# For coverage:
# python -m pytest --cov=app tests/backend_tests/
# coverage html
```

## 8. Next Steps / Future Enhancements
*   **Refine Frontend**:
    *   Implement full UI rendering for all data rather than just `console.log` or partial placeholders in some areas.
    *   Develop a more robust frontend routing/navigation system if it grows beyond simple page links.
    *   Consider a modern JavaScript framework (React, Vue, Svelte) for more complex UI interactions and state management if the application scales.
    *   Comprehensive frontend testing (e.g., using Jest, Playwright, or Cypress).
*   **Backend Enhancements**:
    *   Complete implementation of any remaining CRUD functionalities or edge cases.
    *   Add more sophisticated role-based access control (RBAC).
    *   Implement background tasks for lengthy operations (e.g., bulk letter sending).
    *   Add comprehensive input validation beyond Pydantic (e.g., business rule validation).
*   **LLM Integration**:
    *   More sophisticated prompt engineering and fine-tuning.
    *   Allow user customization of letter templates/prompts.
*   **User Experience (UX/UI)**:
    *   Professional UI/UX design and implementation.
    *   Accessibility improvements.
*   **Deployment**:
    *   Containerization (Docker).
    *   CI/CD pipelines.
    *   Configuration for production environments (e.g., PostgreSQL connection pooling, Gunicorn/Uvicorn workers).
*   **Advanced Features**:
    *   Payment integration.
    *   Automated communication scheduling.
    *   Detailed analytics and reporting dashboards.
    *   Multi-user support with team features.
