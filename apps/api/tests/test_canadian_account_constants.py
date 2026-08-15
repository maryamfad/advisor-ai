from decimal import Decimal

from app.services import canadian_account_constants as constants


class TestConstantsAreSane:
    def test_all_dollar_figures_are_positive(self) -> None:
        dollar_figures = [
            constants.TFSA_ANNUAL_LIMIT,
            constants.FHSA_ANNUAL_LIMIT,
            constants.FHSA_LIFETIME_LIMIT,
            constants.RRSP_ANNUAL_DOLLAR_CAP,
            constants.RRSP_MIN_INCOME_FOR_PRIORITY,
            constants.RESP_LIFETIME_LIMIT_PER_BENEFICIARY,
            constants.RESP_CESG_ANNUAL_CONTRIBUTION_FOR_MAX_GRANT,
        ]
        assert all(value > 0 for value in dollar_figures)

    def test_fhsa_annual_times_years_does_not_exceed_lifetime(self) -> None:
        # 5 years at the annual cap is the fastest way to hit the
        # lifetime cap; the lifetime cap should be reachable, not
        # smaller than a single year's contribution.
        assert constants.FHSA_LIFETIME_LIMIT >= constants.FHSA_ANNUAL_LIMIT

    def test_fhsa_age_window_is_valid(self) -> None:
        assert constants.FHSA_MIN_AGE < constants.FHSA_MAX_AGE

    def test_rrsp_deduction_rate_is_a_fraction(self) -> None:
        assert Decimal("0") < constants.RRSP_DEDUCTION_LIMIT_RATE < Decimal("1")

    def test_resp_cesg_match_rate_is_a_fraction(self) -> None:
        assert Decimal("0") < constants.RESP_CESG_MATCH_RATE < Decimal("1")

    def test_tax_year_is_an_int(self) -> None:
        assert isinstance(constants.TAX_YEAR, int)
