import sys
from pathlib import Path

# Allow imports from backend/app
sys.path.append(
    str(Path(__file__).resolve().parents[1])
)

import random
from datetime import date, timedelta

from faker import Faker

from app.database import SessionLocal, Base, engine
from app.models import (
    Vehicle,
    Part,
    Failure,
    Telematics
)


# ============================================================
# Configuration
# ============================================================

NUM_VEHICLES = 400
WEEKS = 52

START_DATE = date(2025, 1, 6)

random.seed(42)
Faker.seed(42)

fake = Faker()


# ============================================================
# Parts
# ============================================================

PARTS = [
    {
        "part_code": "ELC-0152",
        "part_name": "Alternator",
        "category": "Electrical",
        "design_life_km": 250000
    },
    {
        "part_code": "BAT-0201",
        "part_name": "Battery",
        "category": "Electrical",
        "design_life_km": 180000
    },
    {
        "part_code": "CLG-0310",
        "part_name": "Cooling Pump",
        "category": "Cooling",
        "design_life_km": 220000
    },
    {
        "part_code": "BRK-0412",
        "part_name": "Brake Assembly",
        "category": "Chassis",
        "design_life_km": 150000
    }
]


MODELS = [
    "Long-Haul Tractor",
    "Rigid Haulage",
    "Heavy Cargo Truck",
    "Medium Cargo Truck"
]


REGIONS = [
    "North",
    "South",
    "East",
    "West"
]


# ============================================================
# 1. Vehicles
# ============================================================

def generate_vehicles():

    vehicles = []

    registration_start = date(2018, 1, 1)

    for i in range(NUM_VEHICLES):

        registration_date = (
            registration_start
            + timedelta(
                days=random.randint(0, 2500)
            )
        )

        vehicle = Vehicle(
            vin=f"FG{i + 1:06d}",

            model=random.choice(
                MODELS
            ),

            region=random.choice(
                REGIONS
            ),

            registration_date=registration_date,

            total_km_driven=random.randint(
                30000,
                400000
            )
        )

        vehicles.append(vehicle)

    return vehicles


# ============================================================
# 2. Parts
# ============================================================

def generate_parts():

    return [
        Part(**part)
        for part in PARTS
    ]


# ============================================================
# 3. Telematics
# ============================================================

def generate_telematics(vehicles):

    records = []

    for vehicle in vehicles:

        # Vehicle-specific operating characteristics.
        # These remain relatively stable across the year.

        vehicle_stress = random.uniform(
            0.0,
            0.25
        )

        vehicle_usage = random.uniform(
            0.0,
            0.25
        )

        for week in range(WEEKS):

            week_date = (
                START_DATE
                + timedelta(
                    weeks=week
                )
            )

            # ------------------------------------------------
            # Base operating signals
            # ------------------------------------------------

            coolant = (
                0.20
                + vehicle_stress
                + random.uniform(
                    -0.08,
                    0.08
                )
            )

            oil_dips = max(
                0,
                int(
                    random.gauss(
                        1 + vehicle_stress * 4,
                        1
                    )
                )
            )

            battery = (
                0.20
                + vehicle_stress
                + random.uniform(
                    -0.08,
                    0.08
                )
            )

            dtc = (
                0.10
                + vehicle_stress * 0.5
                + random.uniform(
                    -0.05,
                    0.05
                )
            )

            harsh_braking = (
                0.15
                + vehicle_usage
                + random.uniform(
                    -0.08,
                    0.08
                )
            )

            overload = (
                0.15
                + vehicle_usage
                + random.uniform(
                    -0.08,
                    0.08
                )
            )

            high_rpm = (
                0.15
                + vehicle_stress
                + random.uniform(
                    -0.08,
                    0.08
                )
            )

            short_trip = (
                0.15
                + vehicle_usage * 0.5
                + random.uniform(
                    -0.08,
                    0.08
                )
            )

            idle = (
                0.15
                + vehicle_usage * 0.5
                + random.uniform(
                    -0.06,
                    0.06
                )
            )

            # ------------------------------------------------
            # Gradual fleet/vehicle aging effect
            # ------------------------------------------------

            aging = week / WEEKS

            coolant += aging * 0.10
            battery += aging * 0.08
            dtc += aging * 0.05

            # ------------------------------------------------
            # Occasional abnormal operating weeks
            # ------------------------------------------------

            if random.random() < 0.08:

                coolant += random.uniform(
                    0.15,
                    0.30
                )

                oil_dips += random.randint(
                    2,
                    5
                )

                battery += random.uniform(
                    0.15,
                    0.30
                )

                dtc += random.uniform(
                    0.15,
                    0.30
                )

            # ------------------------------------------------
            # Keep values within sensible ranges
            # ------------------------------------------------

            coolant = min(
                max(coolant, 0.0),
                1.0
            )

            battery = min(
                max(battery, 0.0),
                1.0
            )

            dtc = min(
                max(dtc, 0.0),
                1.0
            )

            harsh_braking = min(
                max(harsh_braking, 0.0),
                1.0
            )

            overload = min(
                max(overload, 0.0),
                1.0
            )

            high_rpm = min(
                max(high_rpm, 0.0),
                1.0
            )

            short_trip = min(
                max(short_trip, 0.0),
                1.0
            )

            idle = min(
                max(idle, 0.0),
                1.0
            )

            record = Telematics(

                vin=vehicle.vin,

                week_start_date=week_date,

                coolant_temp_variance=round(
                    coolant,
                    4
                ),

                oil_pressure_dips=oil_dips,

                battery_voltage_sag=round(
                    battery,
                    4
                ),

                dtc_recurrence_rate=round(
                    dtc,
                    4
                ),

                harsh_braking_frequency=round(
                    harsh_braking,
                    4
                ),

                overload_duty_share=round(
                    overload,
                    4
                ),

                high_rpm_dwell_time=round(
                    high_rpm,
                    4
                ),

                short_trip_ratio=round(
                    short_trip,
                    4
                ),

                idle_time_pct=round(
                    idle,
                    4
                )
            )

            records.append(record)

    return records


# ============================================================
# 4. Part-specific degradation
# ============================================================

def calculate_part_risk(row, part_code):

    """
    Calculate latent degradation/risk.

    IMPORTANT:
    These weights are used ONLY to create realistic
    synthetic data.

    Later, the ML model should learn the relationships
    independently.
    """

    risk = 0.0

    # --------------------------------------------------------
    # Alternator
    # --------------------------------------------------------

    if part_code == "ELC-0152":

        risk += (
            row.battery_voltage_sag
            * 0.35
        )

        risk += (
            min(
                row.oil_pressure_dips / 10,
                1.0
            )
            * 0.25
        )

        risk += (
            row.coolant_temp_variance
            * 0.20
        )

        risk += (
            row.dtc_recurrence_rate
            * 0.15
        )

        risk += (
            row.high_rpm_dwell_time
            * 0.05
        )

    # --------------------------------------------------------
    # Battery
    # --------------------------------------------------------

    elif part_code == "BAT-0201":

        risk += (
            row.battery_voltage_sag
            * 0.40
        )

        risk += (
            row.short_trip_ratio
            * 0.20
        )

        risk += (
            row.idle_time_pct
            * 0.15
        )

        risk += (
            row.dtc_recurrence_rate
            * 0.15
        )

        risk += (
            row.high_rpm_dwell_time
            * 0.10
        )

    # --------------------------------------------------------
    # Cooling Pump
    # --------------------------------------------------------

    elif part_code == "CLG-0310":

        risk += (
            row.coolant_temp_variance
            * 0.45
        )

        risk += (
            min(
                row.oil_pressure_dips / 10,
                1.0
            )
            * 0.25
        )

        risk += (
            row.high_rpm_dwell_time
            * 0.15
        )

        risk += (
            row.overload_duty_share
            * 0.15
        )

    # --------------------------------------------------------
    # Brake Assembly
    # --------------------------------------------------------

    elif part_code == "BRK-0412":

        risk += (
            row.harsh_braking_frequency
            * 0.40
        )

        risk += (
            row.overload_duty_share
            * 0.30
        )

        risk += (
            row.short_trip_ratio
            * 0.15
        )

        risk += (
            row.high_rpm_dwell_time
            * 0.15
        )

    return min(
        max(risk, 0.0),
        1.0
    )


# ============================================================
# 5. Generate failures
# ============================================================

def generate_failures(
    telematics,
    target_failures=200
):

    failures = []

    # --------------------------------------------------------
    # Build candidate failures
    # --------------------------------------------------------

    candidates = []

    for row in telematics:

        for part in PARTS:

            part_code = part["part_code"]

            risk = calculate_part_risk(
                row,
                part_code
            )

            # Non-linear probability makes high-risk
            # observations much more likely to fail.

            probability = (
                risk ** 2
            ) * 0.12

            # Small random noise
            probability += random.uniform(
                0.0,
                0.005
            )

            probability = min(
                probability,
                0.20
            )

            if random.random() < probability:

                # Failure happens 1–8 weeks after
                # the observed telematics week.

                failure_date = (
                    row.week_start_date
                    + timedelta(
                        days=random.randint(
                            1,
                            56
                        )
                    )
                )

                candidates.append(
                    {
                        "vin": row.vin,

                        "part_code": part_code,

                        "failure_date": failure_date,

                        "risk": risk,

                        "odometer": random.randint(
                            50000,
                            350000
                        )
                    }
                )

    # --------------------------------------------------------
    # Sort candidates by risk.
    #
    # This ensures that if we need to limit the number
    # of failures, we preferentially retain meaningful
    # high-risk events instead of randomly destroying
    # the relationship.
    # --------------------------------------------------------

    candidates.sort(
        key=lambda x: x["risk"],
        reverse=True
    )

    # --------------------------------------------------------
    # Limit to target number
    # --------------------------------------------------------

    selected = candidates[
        :target_failures
    ]

    # --------------------------------------------------------
    # Convert to Failure objects
    # --------------------------------------------------------

    for i, candidate in enumerate(
        selected,
        start=1
    ):

        failure = Failure(

            job_card_id=(
                f"JC{i:06d}"
            ),

            vin=candidate["vin"],

            part_code=candidate["part_code"],

            failure_date=candidate[
                "failure_date"
            ],

            odometer_at_failure=candidate[
                "odometer"
            ],

            replaced=True
        )

        failures.append(
            failure
        )

    return failures


# ============================================================
# 6. Main
# ============================================================

def main():

    db = SessionLocal()

    try:

        print("Resetting database...")

        # ----------------------------------------------------
        # Clear old data
        # ----------------------------------------------------

        Base.metadata.drop_all(
            bind=engine
        )

        Base.metadata.create_all(
            bind=engine
        )

        # ----------------------------------------------------
        # Vehicles
        # ----------------------------------------------------

        print("Generating vehicles...")

        vehicles = generate_vehicles()

        db.add_all(
            vehicles
        )

        db.commit()

        print(
            f"Vehicles created: "
            f"{len(vehicles)}"
        )

        # ----------------------------------------------------
        # Parts
        # ----------------------------------------------------

        print("Generating parts...")

        parts = generate_parts()

        db.add_all(
            parts
        )

        db.commit()

        print(
            f"Parts created: "
            f"{len(parts)}"
        )

        # ----------------------------------------------------
        # Telematics
        # ----------------------------------------------------

        print("Generating telematics...")

        telematics = generate_telematics(
            vehicles
        )

        db.add_all(
            telematics
        )

        db.commit()

        print(
            "Telematics records created: "
            f"{len(telematics)}"
        )

        # ----------------------------------------------------
        # Failures
        # ----------------------------------------------------

        print("Generating failures...")

        failures = generate_failures(
            telematics,
            target_failures=200
        )

        db.add_all(
            failures
        )

        db.commit()

        print(
            "Failure records created: "
            f"{len(failures)}"
        )

        print(
            "\nData generation completed successfully."
        )

    finally:

        db.close()


# ============================================================
# Entry point
# ============================================================

if __name__ == "__main__":
    main()