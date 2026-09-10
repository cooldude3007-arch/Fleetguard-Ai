import sys
from pathlib import Path

sys.path.append(
    str(Path(__file__).resolve().parents[1])
)

import pandas as pd

from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    roc_auc_score,
    confusion_matrix
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from app.database import SessionLocal
from app.models import Failure, Part, Telematics


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
            (part_failures["vin"] == row["vin"])
            &
            (part_failures["failure_date"] >
             row["week_start_date"])
            &
            (part_failures["failure_date"] <=
             future_end)
        ]

        if not matches.empty:
            dataset.at[idx, "failure"] = 1

    return dataset


def evaluate_part(
    telematics,
    failures,
    part_code,
    part_name
):

    print("\n" + "=" * 70)
    print(
        f"MODEL EVALUATION — {part_name}"
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
        f"Total samples    : {len(y)}"
    )

    print(
        f"Positive samples : {y.sum()}"
    )

    print(
        f"Negative samples : {len(y) - y.sum()}"
    )

    # --------------------------------------------------------
    # Train / test split
    # --------------------------------------------------------

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.20,
        random_state=42,
        stratify=y
    )

    # --------------------------------------------------------
    # Model
    # --------------------------------------------------------

    model = Pipeline(
        [
            (
                "scaler",
                StandardScaler()
            ),
            (
                "logistic",
                LogisticRegression(
                    max_iter=1000,
                    class_weight="balanced"
                )
            )
        ]
    )

    model.fit(
        X_train,
        y_train
    )

    # --------------------------------------------------------
    # Predictions
    # --------------------------------------------------------

    predictions = model.predict(
        X_test
    )

    probabilities = model.predict_proba(
        X_test
    )[:, 1]

    # --------------------------------------------------------
    # Metrics
    # --------------------------------------------------------

    accuracy = accuracy_score(
        y_test,
        predictions
    )

    precision = precision_score(
        y_test,
        predictions,
        zero_division=0
    )

    recall = recall_score(
        y_test,
        predictions,
        zero_division=0
    )

    auc = roc_auc_score(
        y_test,
        probabilities
    )

    matrix = confusion_matrix(
        y_test,
        predictions
    )

    print("\nModel Performance")
    print("-" * 40)

    print(
        f"Accuracy  : {accuracy:.4f}"
    )

    print(
        f"Precision : {precision:.4f}"
    )

    print(
        f"Recall    : {recall:.4f}"
    )

    print(
        f"ROC-AUC   : {auc:.4f}"
    )

    print("\nConfusion Matrix")
    print(matrix)

    # --------------------------------------------------------
    # Feature coefficients
    # --------------------------------------------------------

    coefficients = (
        model.named_steps["logistic"]
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

    total = result[
        "abs_coefficient"
    ].sum()

    result["weight"] = (
        result["abs_coefficient"]
        / total
    )

    print("\nFeature Weights")
    print("-" * 40)

    print(
        result[
            [
                "signal",
                "coefficient",
                "weight"
            ]
        ].to_string(index=False)
    )


def main():

    telematics, failures, parts = load_data()

    for _, part in parts.iterrows():

        evaluate_part(
            telematics,
            failures,
            part["part_code"],
            part["part_name"]
        )


if __name__ == "__main__":
    main()