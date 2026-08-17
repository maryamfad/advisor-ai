"""Read-only tools the AI assistant can call, each wrapping a DB query
(via gather_client_financial_data) plus the existing pure functions --
never a number the model invents itself.

Every tool returns strictly structured JSON (plain dict), never prose:
that's the actual guardrail. Tool output is the model's only source of
numbers; the orchestration loop's system prompt (app/services/ai_agent.py)
forbids stating a figure that didn't come from a tool result.

All tools take the already-ownership-verified `client` object, not a
raw client_id -- a conversation is always scoped to one client (see
AiConversation), so the agent has no way to ask for a different
client's data than the one its conversation belongs to. compare_funds
is the only tool with genuinely model-choosable parameters (which
funds, what date range); everything else is fixed to "this
conversation's client."

All tools are read-only. None of them create, update, or delete a
persisted record -- generate_financial_plan_preview runs the generator
without saving, deliberately not the same thing as
POST /financial-plans. Any actual write stays a deliberate advisor
action through the normal REST endpoints.
"""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.client import Client
from app.models.tracked_fund import ClientTrackedFund
from app.services.client_financial_snapshot import (
    build_financial_plan_generator_inputs,
    gather_client_financial_data,
)
from app.services.financial_plan_generator import (
    generate_action_items,
    generate_narrative_summary,
)
from app.services.fund_comparison import align_series
from app.services.fund_price_cache import get_cached_or_fetch_prices
from app.services.market_data_client import MarketDataUnavailableError, PricePoint


def get_financial_summary(db: Session, client: Client) -> dict:
    """Monthly income/expenses/cash flow, savings rate, and net worth."""
    snapshot = gather_client_financial_data(db, client)
    return {
        "monthly_income": str(snapshot.monthly_income),
        "monthly_expenses": str(snapshot.monthly_expenses),
        "monthly_cash_flow": str(snapshot.monthly_cash_flow),
        "savings_rate": str(snapshot.savings_rate),
        "net_worth": str(snapshot.net_worth),
    }


def get_insurance_recommendation(db: Session, client: Client) -> dict:
    """Term vs. permanent life insurance recommendation, with the
    estimated coverage need, existing coverage, and gap."""
    snapshot = gather_client_financial_data(db, client)
    return {
        "recommended_type": snapshot.insurance_type_recommendation.recommendation,
        "reasons": snapshot.insurance_type_recommendation.reasons,
        "estimated_coverage_need": str(snapshot.target_coverage),
        "existing_coverage": str(snapshot.existing_coverage),
        "coverage_gap": str(snapshot.coverage_gap),
    }


def get_registered_account_recommendations(db: Session, client: Client) -> dict:
    """Prioritized FHSA/RRSP/TFSA/RESP recommendations, per household
    member (client, and spouse if one is on file)."""
    snapshot = gather_client_financial_data(db, client)

    def _serialize(recommendations):
        return [
            {
                "account_type": r.account_type,
                "priority": r.priority,
                "reason": r.reason,
            }
            for r in recommendations
        ]

    return {
        "client": _serialize(snapshot.client_account_recommendations),
        "spouse": _serialize(snapshot.spouse_account_recommendations),
    }


def get_risk_tolerance(db: Session, client: Client) -> dict:
    """The client's risk-tolerance level and where it came from -- a
    completed scored questionnaire takes precedence over the FNA
    form's self-rated checkbox when both are on file."""
    snapshot = gather_client_financial_data(db, client)

    if (
        snapshot.latest_completed_questionnaire
        and snapshot.latest_completed_questionnaire.risk_tolerance
    ):
        source = "risk_questionnaire"
    elif snapshot.latest_fna and snapshot.latest_fna.risk_tolerance:
        source = "financial_needs_analysis"
    else:
        source = None

    return {"risk_tolerance": snapshot.risk_tolerance, "source": source}


def generate_financial_plan_preview(db: Session, client: Client) -> dict:
    """Previews what POST /clients/{id}/financial-plans would generate
    right now, WITHOUT persisting it -- a dry run the agent can use to
    explain the plan without creating a new versioned FinancialPlan
    row on the client's behalf."""
    snapshot = gather_client_financial_data(db, client)
    items = generate_action_items(**build_financial_plan_generator_inputs(snapshot))
    narrative = generate_narrative_summary(
        monthly_cash_flow=snapshot.monthly_cash_flow,
        savings_rate=snapshot.savings_rate,
        net_worth=snapshot.net_worth,
        action_items=items,
    )

    return {
        "narrative_summary": narrative,
        "action_items": [
            {
                "priority": item.priority,
                "category": item.category,
                "title": item.title,
                "description": item.description,
                "target_amount": (
                    str(item.target_amount) if item.target_amount is not None else None
                ),
            }
            for item in items
        ],
    }


def compare_funds(
    db: Session,
    client: Client,
    symbols: list[str],
    start_date: str,
    end_date: str,
) -> dict:
    """Normalized percent-return comparison for a set of the client's
    tracked funds over a date range. `symbols` is restricted to funds
    already selected for this client -- the agent can't trigger a
    fetch for an arbitrary new ticker against the rate-limited
    provider on its own initiative. start_date/end_date are ISO date
    strings (as an LLM tool call would send them)."""
    parsed_start = date.fromisoformat(start_date)
    parsed_end = date.fromisoformat(end_date)

    selections = list(
        db.scalars(
            select(ClientTrackedFund).where(ClientTrackedFund.client_id == client.id)
        ).all()
    )
    selected_by_symbol = {s.tracked_fund.symbol: s.tracked_fund for s in selections}

    requested = set(symbols)
    unselected = requested - selected_by_symbol.keys()

    series_by_symbol: dict[str, list[PricePoint]] = {}
    warnings: list[str] = [
        f"{symbol}: not selected for this client -- add it first."
        for symbol in unselected
    ]

    for symbol in requested - unselected:
        fund = selected_by_symbol[symbol]
        try:
            prices = get_cached_or_fetch_prices(db, fund, parsed_start, parsed_end)
        except MarketDataUnavailableError as exc:
            warnings.append(f"{symbol}: {exc}")
            continue

        if not prices:
            warnings.append(f"{symbol}: no price data available for this range.")
            continue

        series_by_symbol[symbol] = prices

    aligned = align_series(series_by_symbol)

    return {
        "symbols": list(series_by_symbol.keys()),
        "dates": [d.isoformat() for d in aligned.dates],
        "series": {
            symbol: [str(value) for value in values]
            for symbol, values in aligned.series.items()
        },
        "warnings": warnings,
    }


@dataclass(frozen=True)
class ToolDefinition:
    name: str
    description: str
    input_schema: dict
    handler: Callable[..., dict]


AI_TOOLS: list[ToolDefinition] = [
    ToolDefinition(
        name="get_financial_summary",
        description=get_financial_summary.__doc__ or "",
        input_schema={"type": "object", "properties": {}, "required": []},
        handler=get_financial_summary,
    ),
    ToolDefinition(
        name="get_insurance_recommendation",
        description=get_insurance_recommendation.__doc__ or "",
        input_schema={"type": "object", "properties": {}, "required": []},
        handler=get_insurance_recommendation,
    ),
    ToolDefinition(
        name="get_registered_account_recommendations",
        description=get_registered_account_recommendations.__doc__ or "",
        input_schema={"type": "object", "properties": {}, "required": []},
        handler=get_registered_account_recommendations,
    ),
    ToolDefinition(
        name="get_risk_tolerance",
        description=get_risk_tolerance.__doc__ or "",
        input_schema={"type": "object", "properties": {}, "required": []},
        handler=get_risk_tolerance,
    ),
    ToolDefinition(
        name="generate_financial_plan_preview",
        description=generate_financial_plan_preview.__doc__ or "",
        input_schema={"type": "object", "properties": {}, "required": []},
        handler=generate_financial_plan_preview,
    ),
    ToolDefinition(
        name="compare_funds",
        description=compare_funds.__doc__ or "",
        input_schema={
            "type": "object",
            "properties": {
                "symbols": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": (
                        "Ticker symbols to compare -- must already be "
                        "selected for this client."
                    ),
                },
                "start_date": {
                    "type": "string",
                    "description": "ISO date (YYYY-MM-DD), inclusive.",
                },
                "end_date": {
                    "type": "string",
                    "description": "ISO date (YYYY-MM-DD), inclusive.",
                },
            },
            "required": ["symbols", "start_date", "end_date"],
        },
        handler=compare_funds,
    ),
]

TOOLS_BY_NAME: dict[str, ToolDefinition] = {tool.name: tool for tool in AI_TOOLS}
