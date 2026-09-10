from datetime import date

from app.models import (
    Part,
    Vehicle,
    Telematics,
    RuleConfig,
    Failure
)

from app.services.scoring import (
    calculate_vehicle_score
)


def estimate_rul(
    db,
    vin,
    part_code
):
    """
    Estimate Remaining Useful Life (RUL)
    using:

    1. Part design life
    2. Mileage since latest replacement
    3. Failure probability / degradation
    """

    # --------------------------------------------------------
    # Vehicle
    # --------------------------------------------------------

    vehicle = (
        db.query(Vehicle)
        .filter(
            Vehicle.vin == vin
        )
        .first()
    )

    if not vehicle:
        return None

    # --------------------------------------------------------
    # Part
    # --------------------------------------------------------

    part = (
        db.query(Part)
        .filter(
            Part.part_code == part_code
        )
        .first()
    )

    if not part:
        return None

    # --------------------------------------------------------
    # Latest telematics
    # --------------------------------------------------------

    latest_telematics = (
        db.query(Telematics)
        .filter(
            Telematics.vin == vin
        )
        .order_by(
            Telematics.week_start_date.desc()
        )
        .first()
    )

    if not latest_telematics:
        return None

    # --------------------------------------------------------
    # Scoring rule
    # --------------------------------------------------------

    rules = (
        db.query(RuleConfig)
        .filter(
            RuleConfig.part_code == part_code
        )
        .all()
    )

    if not rules:
        return None

    # --------------------------------------------------------
    # Failure probability
    # --------------------------------------------------------

    score = calculate_vehicle_score(
        latest_telematics,
        rules
    )

    failure_probability = (
        score["failure_probability"]
    )

    risk_tier = (
        score["risk_tier"]
    )

    risk_factor = (
        failure_probability / 100
    )

    # --------------------------------------------------------
    # Current vehicle mileage
    # --------------------------------------------------------

    current_vehicle_km = (
        vehicle.total_km_driven
    )

    # --------------------------------------------------------
    # Find latest replacement
    # --------------------------------------------------------

    last_replacement = (
        db.query(Failure)
        .filter(
            Failure.vin == vin,
            Failure.part_code == part_code,
            Failure.replaced == True
        )
        .order_by(
            Failure.failure_date.desc()
        )
        .first()
    )

    # --------------------------------------------------------
    # Calculate current PART mileage
    # --------------------------------------------------------

    if last_replacement:

        installed_at_km = (
            last_replacement
            .odometer_at_failure
        )

        current_part_km = (
            current_vehicle_km
            - installed_at_km
        )

        # Protect against inconsistent synthetic data
        current_part_km = max(
            current_part_km,
            0
        )

        replacement_status = (
            "Previously replaced"
        )

    else:

        installed_at_km = 0

        current_part_km = (
            current_vehicle_km
        )

        replacement_status = (
            "Original component"
        )

    # --------------------------------------------------------
    # Basic RUL
    # --------------------------------------------------------

    design_life = (
        part.design_life_km
    )

    basic_rul = (
        design_life
        - current_part_km
    )

    basic_rul = max(
        basic_rul,
        0
    )

    # --------------------------------------------------------
    # Degradation adjustment
    #
    # Higher failure probability reduces RUL.
    # --------------------------------------------------------

    degradation_multiplier = (
        1.0
        - (
            risk_factor
            * 0.70
        )
    )

    adjusted_rul = (
        basic_rul
        * degradation_multiplier
    )

    adjusted_rul = max(
        adjusted_rul,
        0
    )

    # --------------------------------------------------------
    # Average daily vehicle usage
    # --------------------------------------------------------

    vehicle_age_days = (
        date.today()
        - vehicle.registration_date
    ).days

    if vehicle_age_days > 0:

        average_daily_km = (
            current_vehicle_km
            / vehicle_age_days
        )

    else:

        average_daily_km = 100

    average_daily_km = max(
        average_daily_km,
        20
    )

    # --------------------------------------------------------
    # RUL days
    # --------------------------------------------------------

    rul_days = (
        adjusted_rul
        / average_daily_km
    )

    # --------------------------------------------------------
    # Service recommendation
    # --------------------------------------------------------

    if adjusted_rul <= 0:

        estimated_window = (
            "Service immediately"
        )

    elif risk_tier == "Red":

        estimated_window = (
            "Service within 7 days"
        )

    elif risk_tier == "Amber":

        estimated_window = (
            "Service within 30 days"
        )

    else:

        estimated_window = (
            "Continue monitoring"
        )

    # --------------------------------------------------------
    # Response
    # --------------------------------------------------------

    return {

        "vin":
            vin,

        "part_code":
            part_code,

        "part_name":
            part.part_name,

        "design_life_km":
            design_life,

        "current_vehicle_km":
            current_vehicle_km,

        "installed_at_km":
            installed_at_km,

        "current_part_km":
            current_part_km,

        "replacement_status":
            replacement_status,

        "failure_probability":
            failure_probability,

        "risk_tier":
            risk_tier,

        "rul_km":
            round(
                adjusted_rul,
                0
            ),

        "rul_days":
            round(
                rul_days,
                0
            ),

        "average_daily_km":
            round(
                average_daily_km,
                1
            ),

        "estimated_window":
            estimated_window
    }