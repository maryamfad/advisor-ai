"""Fixed, versioned risk-tolerance question catalog.

Ten multiple-choice questions, each option worth 1-5 points (min
total score 10, max 50), covering time horizon, goals, loss reaction,
income stability, emergency-fund coverage, investment experience,
liquidity needs, volatility comfort, debt load, and past behaviour in
a downturn. This is a general-purpose instrument, not a substitute for
a regulated suitability assessment where one is legally required.

Kept as plain dataclasses/strings -- no app.models import -- so the
scoring function that consumes this stays as pure and DB-free as the
rest of app/services/. Risk-tolerance level strings ("low",
"low_medium", "medium", "medium_high", "high") match
FinancialNeedsAnalysis/RiskQuestionnaire's RiskTolerance enum values
by convention, not by import.
"""

from dataclasses import dataclass

QUESTIONS_VERSION = "v1"


@dataclass(frozen=True)
class QuestionOption:
    key: str
    text: str
    points: int


@dataclass(frozen=True)
class Question:
    key: str
    text: str
    options: tuple[QuestionOption, ...]


QUESTIONS: tuple[Question, ...] = (
    Question(
        key="time_horizon",
        text=(
            "When will you need to start withdrawing a significant "
            "portion of this money?"
        ),
        options=(
            QuestionOption("lt_2_years", "Less than 2 years", 1),
            QuestionOption("2_to_5_years", "2-5 years", 2),
            QuestionOption("5_to_10_years", "5-10 years", 3),
            QuestionOption("10_to_20_years", "10-20 years", 4),
            QuestionOption("20_plus_years", "20+ years", 5),
        ),
    ),
    Question(
        key="primary_objective",
        text="Which best describes your primary objective for these investments?",
        options=(
            QuestionOption("preserve_capital", "Preserve capital", 1),
            QuestionOption("steady_income", "Generate steady income", 2),
            QuestionOption(
                "balanced_growth_income", "Balanced growth and income", 3
            ),
            QuestionOption("long_term_growth", "Long-term growth", 4),
            QuestionOption("maximum_growth", "Maximum growth", 5),
        ),
    ),
    Question(
        key="loss_reaction",
        text=(
            "If your investment portfolio dropped 20% in value over a "
            "few months, what would you do?"
        ),
        options=(
            QuestionOption("sell_everything", "Sell everything", 1),
            QuestionOption("sell_some", "Sell some", 2),
            QuestionOption("do_nothing", "Do nothing", 3),
            QuestionOption("buy_a_little_more", "Buy a little more", 4),
            QuestionOption("buy_a_lot_more", "Buy a lot more", 5),
        ),
    ),
    Question(
        key="income_stability",
        text="How stable is your current and near-future income?",
        options=(
            QuestionOption("very_unstable", "Very unstable", 1),
            QuestionOption("somewhat_unstable", "Somewhat unstable", 2),
            QuestionOption("moderately_stable", "Moderately stable", 3),
            QuestionOption("stable", "Stable", 4),
            QuestionOption("very_stable", "Very stable", 5),
        ),
    ),
    Question(
        key="emergency_fund",
        text="Do you have an emergency fund covering 3-6 months of expenses?",
        options=(
            QuestionOption("no", "No", 1),
            QuestionOption("partially", "Partially", 3),
            QuestionOption("yes_fully_funded", "Yes, fully funded", 5),
        ),
    ),
    Question(
        key="investment_experience",
        text="How would you describe your investment knowledge and experience?",
        options=(
            QuestionOption("none", "None", 1),
            QuestionOption("limited", "Limited", 2),
            QuestionOption("moderate", "Moderate", 3),
            QuestionOption("good", "Good", 4),
            QuestionOption("extensive", "Extensive", 5),
        ),
    ),
    Question(
        key="liquidity_needs",
        text=(
            "How much of your investable assets might you need within "
            "the next year, for something other than living expenses?"
        ),
        options=(
            QuestionOption("more_than_50_percent", "More than 50%", 1),
            QuestionOption("25_to_50_percent", "25-50%", 2),
            QuestionOption("10_to_25_percent", "10-25%", 3),
            QuestionOption("less_than_10_percent", "Less than 10%", 4),
            QuestionOption("none", "None", 5),
        ),
    ),
    Question(
        key="volatility_comfort",
        text="Which statement best matches your comfort with investment value swings?",
        options=(
            QuestionOption("cannot_tolerate_any_loss", "Can't tolerate any loss", 1),
            QuestionOption(
                "uncomfortable_with_much_fluctuation",
                "Uncomfortable with much fluctuation",
                2,
            ),
            QuestionOption(
                "some_swings_in_moderation", "Some swings, in moderation", 3
            ),
            QuestionOption(
                "comfortable_with_significant_swings",
                "Comfortable with significant swings",
                4,
            ),
            QuestionOption(
                "comfortable_with_large_swings",
                "Comfortable with large swings for higher potential return",
                5,
            ),
        ),
    ),
    Question(
        key="debt_load",
        text="How would you describe your current debt level relative to income?",
        options=(
            QuestionOption("high_overwhelming", "High/overwhelming", 1),
            QuestionOption("somewhat_high", "Somewhat high", 2),
            QuestionOption("moderate", "Moderate", 3),
            QuestionOption("low", "Low", 4),
            QuestionOption("low_or_none", "Low/none", 5),
        ),
    ),
    Question(
        key="past_downturn_behavior",
        text="Have you ever sold investments during a market downturn out of fear?",
        options=(
            QuestionOption(
                "sold_significant_amounts", "Yes, sold significant amounts", 1
            ),
            QuestionOption(
                "held_steady_or_bought_more", "No, held steady or bought more", 5
            ),
        ),
    ),
)

MIN_POSSIBLE_SCORE = 10
MAX_POSSIBLE_SCORE = 50

# (inclusive lower bound, risk-tolerance level) -- must stay sorted
# ascending by lower bound for the scoring function's band lookup.
SCORE_THRESHOLDS: tuple[tuple[int, str], ...] = (
    (10, "low"),
    (19, "low_medium"),
    (27, "medium"),
    (35, "medium_high"),
    (43, "high"),
)
