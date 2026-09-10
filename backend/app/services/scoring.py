from app.models import (
    RuleConfig,
    Telematics
)


SIGNALS = [
    "coolant_temp_variance",
    "oil_pressure_dips",
    "battery_voltage_sag",
    "dtc_recurrence_rate",
    "harsh_braking_frequency",
    "overload_duty_share",
    "high_rpm_dwell_time",
    "short_trip_ratio",
    "idle_time_pct",
]


def normalize_signal(
    signal_name,
    value
):
    """
    Convert signals into approximately 0-1 range.
    """

    if signal_name == "oil_pressure_dips":

        return min(
            value / 10,
            1.0
        )

    return min(
        max(float(value), 0.0),
        1.0
    )


def calculate_risk_tier(
    probability
):

    if probability >= 70:
        return "Red"

    if probability >= 40:
        return "Amber"

    return "Green"


def calculate_vehicle_score(
    telematics_record,
    rules
):

    raw_score = 0.0

    contributions = []

    total_weight = sum(
        rule.correlation_weight
        for rule in rules
        if rule.included
    )

    if total_weight == 0:
        return {
            "failure_probability": 0.0,
            "risk_tier": "Green",
            "top_signals": []
        }

    for rule in rules:

        if not rule.included:
            continue

        signal_name = rule.signal

        raw_value = getattr(
            telematics_record,
            signal_name
        )

        normalized_value = normalize_signal(
            signal_name,
            raw_value
        )

        normalized_weight = (
            rule.correlation_weight
            / total_weight
        )

        contribution = (
            normalized_value
            * normalized_weight
        )

        raw_score += contribution

        contributions.append(
            {
                "signal": signal_name,
                "value": float(raw_value),
                "weight": float(
                    normalized_weight
                ),
                "contribution": float(
                    contribution
                )
            }
        )

    failure_probability = round(
        raw_score * 100,
        2
    )

    failure_probability = min(
        max(
            failure_probability,
            0.0
        ),
        100.0
    )

    risk_tier = calculate_risk_tier(
        failure_probability
    )

    contributions.sort(
        key=lambda item: item[
            "contribution"
        ],
        reverse=True
    )

    return {
        "failure_probability":
            failure_probability,

        "risk_tier":
            risk_tier,

        "top_signals":
            contributions[:3]
    }


def get_latest_telematics(
    db
):

    latest_dates = (
        db.query(
            Telematics.vin,
        )
    )

    records = []

    vins = (
        db.query(Telematics.vin)
        .distinct()
        .all()
    )

    for vin_tuple in vins:

        vin = vin_tuple[0]

        latest = (
            db.query(Telematics)
            .filter(
                Telematics.vin == vin
            )
            .order_by(
                Telematics.week_start_date.desc()
            )
            .first()
        )

        if latest:
            records.append(latest)

    return records


def score_fleet_for_part(
    db,
    part_code
):

    rules = (
        db.query(RuleConfig)
        .filter(
            RuleConfig.part_code
            == part_code
        )
        .all()
    )

    if not rules:
        return []

    telematics_records = (
        get_latest_telematics(
            db
        )
    )

    results = []

    for record in telematics_records:

        score = calculate_vehicle_score(
            record,
            rules
        )

        results.append(
            {
                "vin": record.vin,

                "part_code":
                    part_code,

                "week_start_date":
                    record.week_start_date,

                "failure_probability":
                    score[
                        "failure_probability"
                    ],

                "risk_tier":
                    score[
                        "risk_tier"
                    ],

                "top_signals":
                    score[
                        "top_signals"
                    ]
            }
        )

    results.sort(
        key=lambda item:
            item[
                "failure_probability"
            ],
        reverse=True
    )

    return results


def score_vehicle_history(
    db,
    vin,
    part_code,
    weeks=8
):

    rules = (
        db.query(RuleConfig)
        .filter(
            RuleConfig.part_code == part_code
        )
        .all()
    )

    if not rules:
        return None

    records = (
        db.query(Telematics)
        .filter(
            Telematics.vin == vin
        )
        .order_by(
            Telematics.week_start_date.desc()
        )
        .limit(weeks)
        .all()
    )

    if not records:
        return None

    # Restore chronological order
    records = list(
        reversed(records)
    )

    trend = []

    latest_result = None

    for record in records:

        score = calculate_vehicle_score(
            record,
            rules
        )

        trend.append(
            {
                "week_start_date":
                    record.week_start_date,

                "failure_probability":
                    score[
                        "failure_probability"
                    ],

                "risk_tier":
                    score[
                        "risk_tier"
                    ]
            }
        )

        latest_result = {
            "vin":
                vin,

            "part_code":
                part_code,

            "week_start_date":
                record.week_start_date,

            "failure_probability":
                score[
                    "failure_probability"
                ],

            "risk_tier":
                score[
                    "risk_tier"
                ],

            "top_signals":
                score[
                    "top_signals"
                ],

            "current_signals": {
                "coolant_temp_variance":
                    record.coolant_temp_variance,

                "oil_pressure_dips":
                    record.oil_pressure_dips,

                "battery_voltage_sag":
                    record.battery_voltage_sag,

                "dtc_recurrence_rate":
                    record.dtc_recurrence_rate,

                "harsh_braking_frequency":
                    record.harsh_braking_frequency,

                "overload_duty_share":
                    record.overload_duty_share,

                "high_rpm_dwell_time":
                    record.high_rpm_dwell_time,

                "short_trip_ratio":
                    record.short_trip_ratio,

                "idle_time_pct":
                    record.idle_time_pct
            }
        }

    latest_result["probability_trend"] = trend

    return latest_result