# Project Setup, Running, and Accessing Instructions

This guide will walk you through setting up the project environment, running the application, and accessing its frontend.

## 1. Navigate to Project Directory

After cloning the repository, open your terminal or command prompt. Use the `cd` command to navigate into the project's root directory.

```bash
cd path/to/your/project-directory
```

Replace `path/to/your/project-directory` with the actual path to the cloned repository on your system.

## 2. Create and Activate Python Virtual Environment

A virtual environment helps to isolate project-specific dependencies.

*   **Create the virtual environment:**

    *   For Linux/macOS:
        ```bash
        python3 -m venv venv
        ```
    *   For Windows:
        ```bash
        python -m venv venv
        ```

*   **Activate the virtual environment:**

    *   For Linux/macOS:
        ```bash
        source venv/bin/activate
        ```
    *   For Windows:
        ```bash
        .\venv\Scripts\activate
        ```
    You should see the name of the virtual environment (e.g., `(venv)`) appear at the beginning of your terminal prompt, indicating that the environment is active.

## 3. Install Dependencies

Ensure your virtual environment is active before proceeding.

*   **Install required packages:**

    Use the following command to install all necessary packages listed in the `requirements.txt` file:
    ```bash
    pip install -r requirements.txt
    ```

    This command will download and install the specified versions of the libraries required for this project.

## 4. Create and Configure `.env` File

Environment variables are used to configure application settings. Create a file named `.env` in the root directory of the project.

Copy the following template into your `.env` file and update the values according to your setup:

```env
# Database Connection
# For local testing with SQLite (recommended for simplicity):
DATABASE_URL=sqlite:///./app_main.db
# Example for PostgreSQL (replace with your actual credentials if you use PostgreSQL):
# DATABASE_URL=postgresql+psycopg2://user:password@host:port/dbname

# OpenAI API Key for LLM features
# Can be left blank if LLM-dependent features are not being tested.
# The application might have reduced functionality in areas requiring it.
LLM_API_KEY=your_openai_api_key_here

# Secret Key for JWT Authentication
# IMPORTANT: Use a strong, random string.
# You can generate one using:
#   - OpenSSL: openssl rand -hex 32
#   - Python: import secrets; secrets.token_hex(32)
SECRET_KEY=your_strong_random_secret_key

# JWT Algorithm
ALGORITHM=HS256

# Access Token Expiration Time (in minutes)
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

**Explanation of Variables:**

*   `DATABASE_URL`: Specifies the connection string for your database.
    *   The SQLite example (`sqlite:///./app_main.db`) will create a database file named `app_main.db` in the project's root directory. This is suitable for local development and testing.
    *   If you prefer to use PostgreSQL, uncomment that line and replace `user`, `password`, `host`, `port`, and `dbname` with your PostgreSQL server details.
*   `LLM_API_KEY`: Your API key for OpenAI services. This is required for features that utilize Large Language Models. If you don't have a key or don't need these features, you can leave it blank, but be aware that some parts of the application may not function as expected.
*   `SECRET_KEY`: A crucial security component for signing JWTs (JSON Web Tokens). It **must** be a long, random, and unpredictable string. Do not use a weak or easily guessable key.
*   `ALGORITHM`: The algorithm used for JWT signing. "HS256" is a common choice.
*   `ACCESS_TOKEN_EXPIRE_MINUTES`: Defines how long an access token remains valid after being issued. The default is 30 minutes.

**Remember to replace placeholder values (like `your_openai_api_key_here` and `your_strong_random_secret_key`) with your actual information.** Do not commit your `.env` file to version control if it contains sensitive credentials. Ensure `.env` is listed in your `.gitignore` file.

## 5. Database Setup

*   **Database Creation (Conditional):**
    *   **SQLite**: If you are using SQLite (e.g., `DATABASE_URL=sqlite:///./app_main.db` in your `.env` file), the database file (`app_main.db` in this example) will typically be created automatically in the project's root directory when the application first tries to access it or when you run the database migrations. No manual database creation step is usually needed.
    *   **PostgreSQL (or other server-based databases)**: If you are using PostgreSQL or another server-based database, you must ensure the database exists before the application can connect. If it doesn't exist, you'll need to create it. For PostgreSQL, you can use a command like the following (connect to your PostgreSQL server using `psql` or a GUI tool first):
        ```sql
        CREATE DATABASE your_dbname;
        ```
        Replace `your_dbname` with the actual database name you specified in the `DATABASE_URL` in your `.env` file. Ensure the user specified in `DATABASE_URL` has the necessary permissions on this database.

*   **Run Database Migrations**:
    Once your `.env` file is configured and your database is created (if necessary), apply the database migrations. This will set up the required tables and schema.

    Ensure you are in the project's root directory and your virtual environment is activated. Then run:
    ```bash
    python -m alembic -c alembic.ini upgrade head
    ```
    This command tells Alembic (the database migration tool used in this project) to apply all pending migrations, bringing your database schema up to the latest version defined in the project's migration scripts.

## 6. Run the Backend Server

With the setup complete, you can now run the backend API server.

*   **Prerequisites**:
    *   Ensure your Python virtual environment is activated.
    *   Ensure your `.env` file is correctly configured in the project root.
    *   Ensure database migrations have been successfully applied (see step 5).

*   **Command to Run Server**:
    Navigate to the project's root directory in your terminal (if you aren't already there) and execute the following command:
    ```bash
    python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
    ```

*   **Explanation of the Command**:
    *   `python -m uvicorn`: This part invokes the Uvicorn ASGI server, which is used to run FastAPI applications.
    *   `app.main:app`: This tells Uvicorn where to find your FastAPI application instance. It means: "look in the `app` package (i.e., the `app` directory), then in the `main.py` file, and find the object named `app`."
    *   `--reload`: This flag enables auto-reload. Whenever you save changes to your Python code, Uvicorn will automatically restart the server to apply those changes. This is very helpful during development.
    *   `--host 0.0.0.0`: This makes the server listen on all available network interfaces. It means the server can be accessed not only from `localhost` (or `127.0.0.1`) on your machine but also from other devices on your local network (using your machine's local IP address) or if running inside a Docker container.
    *   `--port 8000`: This specifies that the server should listen for incoming requests on port `8000`.

*   **Expected Output**:
    If the server starts successfully, you should see output in your terminal similar to this:
    ```
    INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
    INFO:     Started reloader process [xxxxx] using statreload
    INFO:     Started server process [xxxxx]
    INFO:     Waiting for application startup.
    INFO:     Application startup complete.
    ```
    (The process IDs `[xxxxx]` will be different numbers.)

    You can then access the API documentation in your browser at `http://localhost:8000/docs` or `http://127.0.0.1:8000/docs`.

## 7. Accessing the Frontend

*   **Prerequisites**:
    *   Ensure the backend server (Uvicorn) is running as described in step 6.

*   **Accessing Frontend Pages**:
    The FastAPI application in `app/main.py` is configured to serve static files from the `app/frontend/` directory. This means all files and subdirectories within `app/frontend/` are accessible via the `/static/` URL path.

    To access the frontend pages:
    1.  Open your web browser.
    2.  Navigate to the login page using the following URL:
        ```
        http://localhost:8000/static/templates/login.html
        ```
    3.  Other HTML pages located in `app/frontend/templates/` can be accessed by changing the filename in the URL. For example, after a successful login, you might be redirected to or can manually navigate to a dashboard page like:
        ```
        http://localhost:8000/static/templates/dashboard.html
        ```

*   **Note on `url_for` and Static File Serving**:
    The HTML templates might contain instances of `url_for('static', path='...')`. This is a Jinja2 templating function often used with FastAPI to generate URLs dynamically.
    *   When these HTML files are served as static content directly via `StaticFiles`, the `url_for` parts might not be processed by FastAPI's templating engine in the same way as if they were rendered by a dedicated FastAPI route returning an `HTMLResponse`.
    *   However, standard relative links to CSS and JavaScript files (e.g., `../css/style.css`, `../js/main.js` from within an HTML file in `app/frontend/templates/`) or paths starting from the static root (e.g., `/static/css/style.css`, `/static/js/main.js`) should work correctly. The key is that any URL like `http://localhost:8000/static/...` maps to the `app/frontend/...` directory on the server. For instance, `http://localhost:8000/static/css/style.css` will serve `app/frontend/css/style.css`.

This completes the setup, running, and basic access instructions for the project.
