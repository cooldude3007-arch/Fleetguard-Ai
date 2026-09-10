from app.services.scoring import (
    calculate_risk_tier,
    normalize_signal
)


def test_green_risk():

    assert (
        calculate_risk_tier(20)
        == "Green"
    )


def test_amber_risk():

    assert (
        calculate_risk_tier(50)
        == "Amber"
    )


def test_red_risk():

    assert (
        calculate_risk_tier(80)
        == "Red"
    )


def test_normal_signal():

    assert (
        normalize_signal(
            "battery_voltage_sag",
            0.5
        )
        == 0.5
    )


def test_signal_upper_bound():

    assert (
        normalize_signal(
            "battery_voltage_sag",
            1.5
        )
        == 1.0
    )


def test_signal_lower_bound():

    assert (
        normalize_signal(
            "battery_voltage_sag",
            -0.5
        )
        == 0.0
    )


def test_oil_pressure_normalization():

    assert (
        normalize_signal(
            "oil_pressure_dips",
            5
        )
        == 0.5
    )