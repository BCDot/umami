from contextlib import asynccontextmanager # For lifespan events
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.backend.auth.endpoints import router as auth_router
from app.backend.routers.businesses import router as businesses_router
from app.backend.routers.customers import router as customers_router
from app.backend.routers.debts import router as debts_router # New router
from app.backend.routers.communications import router as comms_router
from app.backend.routers.actions import router as actions_router
from app.backend.routers.reports import router as reports_router

# Placeholder for startup/shutdown events
async def startup_event():
    print("Application startup...")
    # Example: You could initialize DB connections or load ML models here
    # from app.backend.db.session import engine # If you need engine directly
    # from app.backend.core.models import Base
    # Base.metadata.create_all(bind=engine) # Not recommended if using Alembic for prod

async def shutdown_event():
    print("Application shutdown...")
    # Example: Clean up resources, close DB connections if not managed by session middleware

app = FastAPI(
    title="Debt Collection Assistant API",
    description="API for managing debt collection processes, customers, communications, and generating reports.",
    version="0.1.0",
    lifespan=lifespan # Use lifespan context manager
)

# CORS Middleware
origins = [
    "*", # Allows all origins. For production, restrict this to your frontend's domain(s).
    # "http://localhost",
    # "http://localhost:3000", # If your frontend runs on port 3000
    # "https://your-frontend-domain.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Allows all methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"], # Allows all headers
)

# Include all the routers
API_V1_PREFIX = "/api/v1"

# Routers that have their own prefix (e.g., /auth, /businesses)
app.include_router(auth_router, prefix=API_V1_PREFIX)
app.include_router(businesses_router, prefix=API_V1_PREFIX) # Re-add businesses_router
app.include_router(customers_router, prefix=f"{API_V1_PREFIX}/customers") # Tags are in router
app.include_router(debts_router, prefix=f"{API_V1_PREFIX}/debts")     # Tags are in router
app.include_router(comms_router, prefix=API_V1_PREFIX)
app.include_router(actions_router, prefix=API_V1_PREFIX)
app.include_router(reports_router, prefix=API_V1_PREFIX)

# Customer router has no internal prefix, so we define its full path here.
# This also means its tag "Customers" from the router itself will be used.
app.include_router(customers_router, prefix=f"{API_V1_PREFIX}/customers")


@app.get("/", tags=["Root"])
async def read_root():
    """
    Root endpoint providing a welcome message.
    """
    return {"message": "Welcome to Debt Collection Assistant API"}

# Static files serving
# This will serve files from 'app/frontend/' directory under '/static' path.
# e.g., /static/css/style.css will map to app/frontend/css/style.css
# This matches how url_for('static', path='css/style.css') would work if 'static' is the mount name.
app.mount("/static", StaticFiles(directory="app/frontend"), name="static")

# Note on HTML serving:
# For serving HTML files from app/frontend/templates, you would typically define
# specific GET routes that return HTMLResponse, often using Jinja2Templates.
# Example (not part of this subtask, but for context):
# from fastapi.responses import HTMLResponse
# from fastapi.templating import Jinja2Templates
# templates = Jinja2Templates(directory="app/frontend/templates")
# @app.get("/some-page", response_class=HTMLResponse)
# async def get_some_page(request: Request):
#     return templates.TemplateResponse("some_page.html", {"request": request})
