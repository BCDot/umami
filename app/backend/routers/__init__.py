# This file makes the 'routers' directory a Python package.
# It can also be used to aggregate routers from different files.

# from fastapi import APIRouter

# from . import communications # Example import
# from . import other_router # Example import

# api_router = APIRouter()
# api_router.include_router(communications.router, prefix="/communications", tags=["Communications"])
# api_router.include_router(other_router.router, prefix="/other", tags=["Other"])

# This setup allows app/main.py to just include api_router from this package.
# For now, individual routers will be included directly in main.py or a similar top-level app file.
