from fastapi.testclient import TestClient


def test_healthcheck_returns_service_and_database_status(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "quant-cover-api",
        "database": "ok",
    }
