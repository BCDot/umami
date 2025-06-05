from fastapi import FastAPI
from app.backend.auth.endpoints import router as auth_router
from app.backend.routers.businesses import router as businesses_router
from app.backend.routers.customers import router as customers_router # New router
# Removed duplicate import of customers_router
from app.backend.routers.communications import router as comms_router
from app.backend.routers.actions import router as actions_router
from app.backend.routers.reports import router as reports_router

# Potentially, import your DB creation function if you want to create tables on startup
# from app.backend.db.session import create_db_and_tables # Example
# from app.backend.core.models import Base # If create_db_and_tables is in session.py and needs Base
# from app.backend.db.session import engine # If create_db_and_tables needs engine

app = FastAPI(
    title="Debt Collection Assistant API",
    description="API for managing debt collection processes, customers, communications, and generating reports.",
    version="0.1.0",
    # You can add more metadata here, like terms_of_service, contact, license_info
    # openapi_tags=... # For custom tag ordering or descriptions in docs
)

# Optional: Create tables on startup (useful for SQLite, dev environments without Alembic always)
# WARNING: In a production environment with Alembic, you typically wouldn't call create_all()
# as Alembic should handle the schema. For local dev with SQLite, it can be convenient.
# def create_tables_on_startup():
#    print("Creating database tables based on models...")
#    Base.metadata.create_all(bind=engine) # Make sure Base and engine are imported
#
# app.add_event_handler("startup", create_tables_on_startup)


# Include all the routers
# A common practice is to prefix all API routes, e.g., with /api/v1
API_V1_PREFIX = "/api/v1"

app.include_router(auth_router, prefix=API_V1_PREFIX) # Tags are defined in router itself
app.include_router(businesses_router, prefix=API_V1_PREFIX)
app.include_router(customers_router, prefix=f"{API_V1_PREFIX}/customers", tags=["Customers"]) # Add prefix here
app.include_router(comms_router, prefix=API_V1_PREFIX)
app.include_router(actions_router, prefix=API_V1_PREFIX)
app.include_router(reports_router, prefix=API_V1_PREFIX)


@app.get("/", tags=["Root"])
async def read_root():
    """
    Root endpoint providing a welcome message.
    """
    return {"message": "Welcome to Debt Collection Assistant API"}

# Example of how to run this app (from project root):
# python -m uvicorn app.main:app --reload

# If you want to add static file serving for a simple frontend (ensure correct paths)
# from fastapi.staticfiles import StaticFiles
# app.mount("/static", StaticFiles(directory="app/frontend/static"), name="static") # If static files are in app/frontend/static
# app.mount("/css", StaticFiles(directory="app/frontend/css"), name="css") # If css is directly in app/frontend/css
# app.mount("/js", StaticFiles(directory="app/frontend/js"), name="js")   # If js is directly in app/frontend/js

# For serving HTML templates, you'd typically use Jinja2Templates and define specific routes.
# from fastapi.templating import Jinja2Templates
# templates = Jinja2Templates(directory="app/frontend/templates")
# @app.get("/login-page", response_class=HTMLResponse) # Example
# async def login_page(request: Request):
#     return templates.TemplateResponse("login.html", {"request": request})

# Remember that the routers themselves define their own prefixes (e.g. /auth, /businesses).
# So the final path for an auth endpoint like /token would be /api/v1/auth/token
# If routers do NOT have internal prefixes, the prefix in include_router is the full path segment.
# My current routers DO have internal prefixes, so the include_router prefix is additive.
# E.g. actions_router has prefix="/actions", main app includes it with prefix="/api/v1" -> /api/v1/actions/...
# The customers_router has no internal prefix, so its prefix is fully defined here.
# This is a common pattern.
