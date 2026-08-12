from app.models.account import Account
from app.models.budget import Budget
from app.models.document import Document
from app.models.financial_goal import FinancialGoal
from app.models.insurance_policy import InsurancePolicy
from app.models.task import Task
from app.models.transaction import Transaction


def test_account_table_name() -> None:
    assert Account.__tablename__ == "accounts"


def test_transaction_table_name() -> None:
    assert Transaction.__tablename__ == "transactions"


def test_financial_goal_table_name() -> None:
    assert FinancialGoal.__tablename__ == "financial_goals"


def test_budget_table_name() -> None:
    assert Budget.__tablename__ == "budgets"


def test_insurance_policy_table_name() -> None:
    assert InsurancePolicy.__tablename__ == "insurance_policies"


def test_document_table_name() -> None:
    assert Document.__tablename__ == "documents"


def test_task_table_name() -> None:
    assert Task.__tablename__ == "tasks"


def test_account_transaction_relationship() -> None:
    assert "transactions" in Account.__mapper__.relationships
    assert "account" in Transaction.__mapper__.relationships


def test_client_relationships_registered() -> None:
    from app.models.client import Client

    relationship_names = set(Client.__mapper__.relationships.keys())
    assert relationship_names == {
        "advisor",
        "accounts",
        "financial_goals",
        "budgets",
        "insurance_policies",
        "documents",
        "tasks",
    }
