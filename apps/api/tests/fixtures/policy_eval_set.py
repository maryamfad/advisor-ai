"""A small labeled set of (policy document, question) pairs for
test_retrieval_evals.py's hit-rate check. Test-only data, not a DB
table -- same spirit as test_ai_agent_evals.py's scripted sequences:
this proves the ingestion/search *pipeline* (chunking, metadata
storage, client-scoped similarity search) retrieves the right
document for an obviously-relevant question, not that any particular
embedding model has good semantic judgement.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class PolicyEvalCase:
    filename: str
    document_text: str
    questions: list[str]


POLICY_EVAL_SET: list[PolicyEvalCase] = [
    PolicyEvalCase(
        filename="term_life_policy.txt",
        document_text=(
            "This term life insurance policy provides a death benefit "
            "of $500,000 for a 20 year term. Premiums are level for "
            "the full term and the policy has no cash surrender value."
        ),
        questions=[
            "What is the death benefit on this term life policy?",
            "Does this term life policy have a surrender value?",
        ],
    ),
    PolicyEvalCase(
        filename="whole_life_policy.txt",
        document_text=(
            "This whole life insurance policy builds cash surrender "
            "value over time and includes a $250,000 permanent death "
            "benefit. Dividends may be used to purchase paid-up "
            "additions."
        ),
        questions=[
            "How does the cash surrender value grow on this whole life policy?",
            "Can dividends buy paid-up additions on this whole life policy?",
        ],
    ),
    PolicyEvalCase(
        filename="disability_insurance_policy.txt",
        document_text=(
            "This disability insurance policy pays a monthly benefit "
            "if the insured cannot work due to illness or injury. It "
            "includes an own-occupation definition for the first 24 "
            "months and a waiver of premium rider."
        ),
        questions=[
            "What is the own-occupation period on this disability policy?",
            "Is there a waiver of premium rider on this disability policy?",
        ],
    ),
    PolicyEvalCase(
        filename="critical_illness_policy.txt",
        document_text=(
            "This critical illness policy pays a lump sum of $100,000 "
            "upon diagnosis of a covered condition such as cancer, "
            "heart attack, or stroke. Coverage ends at age 75."
        ),
        questions=[
            "What conditions does this critical illness policy cover?",
            "At what age does coverage end on this critical illness policy?",
        ],
    ),
    PolicyEvalCase(
        filename="annuity_contract.txt",
        document_text=(
            "This deferred annuity contract guarantees a minimum "
            "interest rate during the accumulation phase and offers "
            "a lifetime income option with a 10-year guarantee period "
            "once annuitized."
        ),
        questions=[
            "What income option does this annuity contract offer?",
            "What is the guarantee period once this annuity is annuitized?",
        ],
    ),
    PolicyEvalCase(
        filename="long_term_care_policy.txt",
        document_text=(
            "This long-term care insurance policy reimburses eligible "
            "nursing home and home care expenses up to a daily "
            "benefit maximum, with a 90-day elimination period before "
            "benefits begin."
        ),
        questions=[
            "What is the elimination period on this long-term care policy?",
            "What kind of care expenses does this long-term care policy reimburse?",
        ],
    ),
]
