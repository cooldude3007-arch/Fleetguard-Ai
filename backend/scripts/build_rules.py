import sys
from pathlib import Path

sys.path.append(
    str(Path(__file__).resolve().parents[1])
)

import pandas as pd

from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from app.database import SessionLocal
from app.models import (
    Failure,
    Part,
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


def load_data(db):

    telematics = pd.read_sql(
        db.query(Telematics).statement,
        db.bind
    )

    failures = pd.read_sql(
        db.query(Failure).statement,
        db.bind
    )

    parts = pd.read_sql(
        db.query(Part).statement,
        db.bind
    )

    return telematics, failures, parts


def build_target(
    telematics,
    failures,
    part_code,
    prediction_window_weeks=8
):

    dataset = telematics.copy()

    part_failures = failures[
        failures["part_code"] == part_code
    ].copy()

    dataset["week_start_date"] = pd.to_datetime(
        dataset["week_start_date"]
    )

    part_failures["failure_date"] = pd.to_datetime(
        part_failures["failure_date"]
    )

    dataset["failure"] = 0

    for idx, row in dataset.iterrows():

        window_end = (
            row["week_start_date"]
            + pd.Timedelta(
                weeks=prediction_window_weeks
            )
        )

        matches = part_failures[
            (part_failures["vin"] == row["vin"])
            &
            (
                part_failures["failure_date"]
                > row["week_start_date"]
            )
            &
            (
                part_failures["failure_date"]
                <= window_end
            )
        ]

        if not matches.empty:
            dataset.at[idx, "failure"] = 1

    return dataset


def build_rule(
    telematics,
    failures,
    part_code
):

    dataset = build_target(
        telematics,
        failures,
        part_code
    )

    X = dataset[SIGNALS]
    y = dataset["failure"]

    pipeline = Pipeline(
        [
            (
                "scaler",
                StandardScaler()
            ),
            (
                "model",
                LogisticRegression(
                    max_iter=1000,
                    class_weight="balanced"
                )
            )
        ]
    )

    pipeline.fit(X, y)

    coefficients = (
        pipeline.named_steps["model"]
        .coef_[0]
    )

    result = pd.DataFrame(
        {
            "signal": SIGNALS,
            "coefficient": coefficients
        }
    )

    # Positive coefficients represent
    # positive risk contributions.
    result["positive_coefficient"] = (
        result["coefficient"].clip(lower=0)
    )

    total = result[
        "positive_coefficient"
    ].sum()

    if total > 0:
        result["weight"] = (
            result["positive_coefficient"]
            / total
        )
    else:
        result["weight"] = 0.0

    return result


def save_rule(
    db,
    part_code,
    rule
):

    # Remove previous rule for this part.
    db.query(
        RuleConfig
    ).filter(
        RuleConfig.part_code == part_code
    ).delete()

    for _, row in rule.iterrows():

        config = RuleConfig(
            part_code=part_code,
            signal=row["signal"],
            correlation_weight=float(
                row["weight"]
            ),
            included=(
                row["coefficient"] > 0
            )
        )

        db.add(config)

    db.commit()


def main():

    db = SessionLocal()

    try:

        telematics, failures, parts = (
            load_data(db)
        )

        for _, part in parts.iterrows():

            part_code = part["part_code"]
            part_name = part["part_name"]

            print(
                "\nBuilding rule for "
                f"{part_name}..."
            )

            rule = build_rule(
                telematics,
                failures,
                part_code
            )

            save_rule(
                db,
                part_code,
                rule
            )

            print(
                rule[
                    [
                        "signal",
                        "coefficient",
                        "weight"
                    ]
                ]
                .sort_values(
                    "weight",
                    ascending=False
                )
                .to_string(index=False)
            )

        print(
            "\nRules saved successfully."
        )

    finally:
        db.close()


if __name__ == "__main__":
    main()