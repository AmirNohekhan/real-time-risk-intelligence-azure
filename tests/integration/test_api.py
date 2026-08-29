from pathlib import Path

from fastapi.testclient import TestClient

from risk_platform.data.synthetic import generate_dataset
from risk_platform.inference.api import app
from risk_platform.inference.service import RiskScorer
from risk_platform.training import train


def test_end_to_end_scoring_contract(tmp_path: Path) -> None:
    app.state.scorer = RiskScorer(train(generate_dataset(700), tmp_path / "model.joblib"))
    payload = {
        "entity_id": "integration",
        "amount": 250,
        "account_age_days": 90,
        "historical_event_count_30d": 40,
        "historical_avg_amount": 70,
        "events_1h": 2,
        "events_24h": 10,
        "is_new_device": False,
        "is_new_location": False,
        "recent_failure_rate": 0.05,
        "historical_risk_count": 0,
        "country_code": "US",
    }
    with TestClient(app) as client:
        app.state.scorer = RiskScorer(train(generate_dataset(700), tmp_path / "model2.joblib"))
        response = client.post("/v1/score", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["recommended_action"] in {"APPROVE", "REVIEW", "BLOCK"}
    assert 0 <= body["final_risk_score"] <= 1
    assert body["reason_codes"]
