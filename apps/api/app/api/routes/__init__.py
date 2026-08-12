from fastapi import APIRouter

from app.api.routes.accounts import router as accounts_router
from app.api.routes.clients import router as clients_router

api_router = APIRouter()
api_router.include_router(clients_router)
api_router.include_router(accounts_router)
