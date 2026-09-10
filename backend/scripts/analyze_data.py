import sys
from pathlib import Path

# Allow imports from backend/app
sys.path.append(
    str(Path(__file__).resolve().parents[1])
)

import pandas as pd

from app.database import SessionLocal
from app.models import (
    Vehicle,
    Part,
    Failure,
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

        vehicles = pd.read_sql(
            db.query(Vehicle).statement,
            db.bind
        )

        parts = pd.read_sql(
            db.query(Part).statement,
            db.bind
        )

        failures = pd.read_sql(
            db.query(Failure).statement,
            db.bind
        )

        telematics = pd.read_sql(
            db.query(Telematics).statement,
            db.bind
        )

        return vehicles, parts, failures, telematics

    finally:
        db.close()


def print_dataset_summary(
    vehicles,
    parts,
    failures,
    telematics
):

    print("\n" + "=" * 60)
    print("DATASET SUMMARY")
    print("=" * 60)

    print(f"Vehicles     : {len(vehicles)}")
    print(f"Parts        : {len(parts)}")
    print(f"Failures     : {len(failures)}")
    print(f"Telematics   : {len(telematics)}")

    print("\nParts:")
    print(
        parts[
            [
                "part_code",
                "part_name",
                "category",
                "design_life_km"
            ]
        ].to_string(index=False)
    )


def create_failure_dataset(
    telematics,
    failures,
    part_code,
    prediction_window_weeks=8
):
    """
    Create a predictive dataset.

    Target:
        1 = the vehicle experienced a failure for this
            part within the following prediction window.
        0 = no such failure within the window.
    """

    dataset = telematics.copy()

    # Failures for the selected part
    part_failures = failures[
        failures["part_code"] == part_code
    ].copy()

    # Convert dates to datetime
    dataset["week_start_date"] = pd.to_datetime(
        dataset["week_start_date"]
    )

    part_failures["failure_date"] = pd.to_datetime(
        part_failures["failure_date"]
    )

    dataset["failure"] = 0

    # Check each telematics observation
    for idx, row in dataset.iterrows():

        vin = row["vin"]
        week = row["week_start_date"]

        window_end = (
            week +
            pd.Timedelta(
                weeks=prediction_window_weeks
            )
        )

        vehicle_failures = part_failures[
            part_failures["vin"] == vin
        ]

        future_failure = vehicle_failures[
            (
                vehicle_failures["failure_date"] > week
            )
            &
            (
                vehicle_failures["failure_date"] <= window_end
            )
        ]

        if not future_failure.empty:

            dataset.at[
                idx,
                "failure"
            ] = 1

    return dataset


def calculate_correlations(
    dataset,
    part_name
):

    print("\n" + "=" * 60)
    print(f"CORRELATION ANALYSIS — {part_name}")
    print("=" * 60)

    results = []

    for signal in SIGNALS:

        correlation = dataset[
            [signal, "failure"]
        ].corr().iloc[0, 1]

        results.append(
            {
                "signal": signal,
                "correlation": correlation
            }
        )

    result_df = pd.DataFrame(results)

    result_df["abs_correlation"] = (
        result_df["correlation"].abs()
    )

    result_df = result_df.sort_values(
        "abs_correlation",
        ascending=False
    )

    print(
        result_df[
            [
                "signal",
                "correlation"
            ]
        ].to_string(index=False)
    )

    return result_df


def main():

    print("\nLoading FleetGuard data...")

    (
        vehicles,
        parts,
        failures,
        telematics
    ) = load_data()

    print_dataset_summary(
        vehicles,
        parts,
        failures,
        telematics
    )

    all_results = {}

    for _, part in parts.iterrows():

        part_code = part["part_code"]
        part_name = part["part_name"]

        dataset = create_failure_dataset(
            telematics,
            failures,
            part_code
        )

        result = calculate_correlations(
            dataset,
            part_name
        )

        all_results[part_code] = result

    print("\n" + "=" * 60)
    print("ANALYSIS COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    main()