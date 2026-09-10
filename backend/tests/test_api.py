from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_home():

    response = client.get("/")

    assert response.status_code == 200

    data = response.json()

    assert "message" in data


def test_parts():

    response = client.get("/parts")

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)

    assert len(data) > 0

    first_part = data[0]

    assert "part_code" in first_part
    assert "part_name" in first_part
    assert "design_life_km" in first_part


def test_alternator_rule():

    response = client.get(
        "/rules/ELC-0152"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["part_code"] == "ELC-0152"

    assert "signals" in data

    assert len(data["signals"]) > 0


def test_invalid_part_rule():

    response = client.get(
        "/rules/INVALID"
    )

    assert response.status_code == 404


def test_alternator_predictions():

    response = client.get(
        "/predictions/ELC-0152"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["part_code"] == "ELC-0152"

    assert "predictions" in data

    assert len(data["predictions"]) > 0

    prediction = data[
        "predictions"
    ][0]

    assert "vin" in prediction

    assert (
        "failure_probability"
        in prediction
    )

    assert "risk_tier" in prediction

    assert "top_signals" in prediction