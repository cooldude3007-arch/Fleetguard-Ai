import sys
from pathlib import Path

sys.path.append(
    str(Path(__file__).resolve().parents[1])
)

import pandas as pd

from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

from app.database import SessionLocal
from app.models import (
    Failure,
    Part,
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


def load_data():

    db = SessionLocal()

    try:

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

    finally:
        db.close()


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

        future_end = (
            row["week_start_date"]
            + pd.Timedelta(
                weeks=prediction_window_weeks
            )
        )

        matches = part_failures[
            (
                part_failures["vin"]
                == row["vin"]
            )
            &
            (
                part_failures["failure_date"]
                > row["week_start_date"]
            )
            &
            (
                part_failures["failure_date"]
                <= future_end
            )
        ]

        if not matches.empty:

            dataset.at[idx, "failure"] = 1

    return dataset


def train_for_part(
    telematics,
    failures,
    part_code,
    part_name
):

    print("\n" + "=" * 70)
    print(
        f"TRAINING LOGISTIC REGRESSION — "
        f"{part_name}"
    )
    print("=" * 70)

    dataset = build_target(
        telematics,
        failures,
        part_code
    )

    X = dataset[SIGNALS]

    y = dataset["failure"]

    print(
        f"Positive samples: {y.sum()}"
    )

    print(
        f"Negative samples: "
        f"{len(y) - y.sum()}"
    )

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

    result["abs_coefficient"] = (
        result["coefficient"].abs()
    )

    result = result.sort_values(
        "abs_coefficient",
        ascending=False
    )

    # Normalize absolute coefficients
    total = result[
        "abs_coefficient"
    ].sum()

    result["weight"] = (
        result["abs_coefficient"]
        / total
    )

    print(
        result[
            [
                "signal",
                "coefficient",
                "weight"
            ]
        ].to_string(
            index=False
        )
    )

    return result


def main():

    telematics, failures, parts = load_data()

    for _, part in parts.iterrows():

        train_for_part(
            telematics,
            failures,
            part["part_code"],
            part["part_name"]
        )


if __name__ == "__main__":
    main()