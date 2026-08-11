from app.models.advisor import Advisor


def test_advisor_table_name() -> None:
    assert Advisor.__tablename__ == "advisors"
