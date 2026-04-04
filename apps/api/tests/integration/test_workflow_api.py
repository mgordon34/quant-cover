from fastapi.testclient import TestClient


def test_user_strategy_and_backtest_workflow(client: TestClient) -> None:
    user_response = client.post(
        "/users",
        json={"email": "Matt@Example.com", "display_name": "Matt"},
    )
    assert user_response.status_code == 201
    user = user_response.json()
    assert user["email"] == "matt@example.com"

    strategy_response = client.post(
        "/strategies",
        json={
            "user_id": user["id"],
            "name": "Simple pace filter",
            "description": "Initial test strategy",
            "configuration": {"min_edge": 0.03},
        },
    )
    assert strategy_response.status_code == 201
    strategy = strategy_response.json()

    strategies_response = client.get("/strategies", params={"user_id": user["id"]})
    assert strategies_response.status_code == 200
    assert [item["id"] for item in strategies_response.json()] == [strategy["id"]]

    run_response = client.post(
        "/backtest-runs",
        json={
            "user_id": user["id"],
            "strategy_id": strategy["id"],
            "dataset_version": "nba-2024-regular-season-v1",
            "parameters": {"start_date": "2024-10-22", "end_date": "2025-04-13"},
        },
    )
    assert run_response.status_code == 201
    run = run_response.json()
    assert run["status"] == "queued"

    runs_response = client.get("/backtest-runs", params={"user_id": user["id"]})
    assert runs_response.status_code == 200
    assert [item["id"] for item in runs_response.json()] == [run["id"]]

    get_run_response = client.get(f"/backtest-runs/{run['id']}")
    assert get_run_response.status_code == 200
    assert get_run_response.json()["strategy_id"] == strategy["id"]


def test_create_strategy_returns_not_found_for_missing_user(client: TestClient) -> None:
    response = client.post(
        "/strategies",
        json={
            "user_id": 999,
            "name": "Simple pace filter",
            "description": None,
            "configuration": {},
        },
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "User not found"}
