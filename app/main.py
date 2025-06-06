from contextlib import asynccontextmanager # For lifespan events
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.backend.auth.endpoints import router as auth_router
from app.backend.routers.businesses import router as businesses_router
from app.backend.routers.customers import router as customers_router
from app.backend.routers.debts import router as debts_router
from app.backend.routers.users import router as users_router
from app.backend.routers.communications import router as comms_router
from app.backend.routers.actions import router as actions_router
from app.backend.routers.reports import router as reports_router

# Lifespan context manager
@asynccontextmanager
async def lifespan(app_instance: FastAPI): # Renamed 'app' to 'app_instance' to avoid conflict
    # Code to run on startup
    print("Application startup...")
    # Example: You could initialize DB connections or load ML models here
    # from app.backend.db.session import engine
    # from app.backend.core.models import Base
    # Base.metadata.create_all(bind=engine) # Not recommended if using Alembic for prod
    yield
    # Code to run on shutdown
    print("Application shutdown...")
    # Example: Clean up resources, close DB connections if not managed by session middleware

# FastAPI App Initialization
app = FastAPI(
    title="Debt Collection Assistant API",
    description="API for managing debt collection processes, customers, communications, and generating reports.",
    version="0.1.0",
    lifespan=lifespan # Use the defined lifespan context manager
)

# CORS Middleware
origins = [
    "*", # Allows all origins. For production, restrict this to your frontend's domain(s).
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all the routers
API_V1_PREFIX = "/api/v1"

app.include_router(auth_router, prefix=API_V1_PREFIX)
app.include_router(businesses_router, prefix=API_V1_PREFIX)
app.include_router(customers_router, prefix=f"{API_V1_PREFIX}/customers")
app.include_router(debts_router, prefix=f"{API_V1_PREFIX}/debts")
app.include_router(users_router, prefix=f"{API_V1_PREFIX}/users")
app.include_router(comms_router, prefix=API_V1_PREFIX)
app.include_router(actions_router, prefix=API_V1_PREFIX)
app.include_router(reports_router, prefix=API_V1_PREFIX)

@app.get("/", tags=["Root"])
async def read_root():
    """
    Root endpoint providing a welcome message.
    """
    return {"message": "Welcome to Debt Collection Assistant API"}

# Static files serving
app.mount("/static", StaticFiles(directory="app/frontend"), name="static")
