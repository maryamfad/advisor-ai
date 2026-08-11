from app.models.client import Client


def test_client_table_name() -> None:
    assert Client.__tablename__ == "clients"
