from fastapi import APIRouter

from app.api.routes.accounts import router as accounts_router
from app.api.routes.budgets import router as budgets_router
from app.api.routes.clients import router as clients_router
from app.api.routes.debts import router as debts_router
from app.api.routes.dependents import router as dependents_router
from app.api.routes.goals import router as goals_router
from app.api.routes.income_sources import router as income_sources_router
from app.api.routes.spouse import router as spouse_router
from app.api.routes.tasks import client_tasks_router
from app.api.routes.tasks import router as tasks_router
from app.api.routes.transactions import router as transactions_router

api_router = APIRouter()
api_router.include_router(clients_router)
api_router.include_router(accounts_router)
api_router.include_router(transactions_router)
api_router.include_router(goals_router)
api_router.include_router(budgets_router)
api_router.include_router(client_tasks_router)
api_router.include_router(tasks_router)
api_router.include_router(spouse_router)
api_router.include_router(dependents_router)
api_router.include_router(income_sources_router)
api_router.include_router(debts_router)
