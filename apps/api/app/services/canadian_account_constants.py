"""Simplified Canadian registered-account figures for a given tax year.

These are deliberately rounded, rule-of-thumb figures, NOT a precise
per-individual CRA contribution-room calculation (which would need
prior years' unused room, notices of assessment, and other data this
app does not track). Review and update this file at the start of each
tax year; nothing in app/services/financial_advice.py should need to
change when these numbers change -- that separation is the point of
keeping them in their own module.
"""

from decimal import Decimal

TAX_YEAR = 2026

# TFSA -- flat annual dollar limit, indexed to inflation and announced
# by the CRA each fall. No age-eligibility ceiling (just 18+).
TFSA_ANNUAL_LIMIT = Decimal("7000")

# FHSA -- annual and lifetime dollar caps, plus the age window
# participation room exists in (opens at 18, closes the year the
# holder turns 71).
FHSA_ANNUAL_LIMIT = Decimal("8000")
FHSA_LIFETIME_LIMIT = Decimal("40000")
FHSA_MIN_AGE = 18
FHSA_MAX_AGE = 71

# RRSP -- deduction room accrues at this rate against prior year's
# earned income, capped at an annual dollar maximum announced yearly.
# RRSP_MIN_INCOME_FOR_PRIORITY is a rule-of-thumb income threshold
# above which the tax deduction is judged valuable enough to rank RRSP
# ahead of TFSA in the account-priority ordering.
RRSP_DEDUCTION_LIMIT_RATE = Decimal("0.18")
RRSP_ANNUAL_DOLLAR_CAP = Decimal("32490")
RRSP_MIN_INCOME_FOR_PRIORITY = Decimal("60000")

# RESP -- no annual cap, but a per-beneficiary lifetime contribution
# limit; the CESG grant matches contributions at this rate up to the
# stated annual contribution (i.e. contributing this much per
# beneficiary per year captures the full available grant).
RESP_LIFETIME_LIMIT_PER_BENEFICIARY = Decimal("50000")
RESP_CESG_MATCH_RATE = Decimal("0.20")
RESP_CESG_ANNUAL_CONTRIBUTION_FOR_MAX_GRANT = Decimal("2500")
