from app.models import Part

from app.services.scoring import (
    score_fleet_for_part,
    score_vehicle_history
)

from app.services.rul import (
    estimate_rul
)


def get_red_vehicles(
    db,
    part_code
):
    """
    Return Red-tier vehicles for a part.
    """

    predictions = score_fleet_for_part(
        db,
        part_code
    )

    results = [
        item
        for item in predictions
        if item["risk_tier"] == "Red"
    ]

    return results[:20]


def get_vehicle_prediction(
    db,
    vin,
    part_code
):
    """
    Get detailed prediction for one VIN/part.
    """

    return score_vehicle_history(
        db,
        vin,
        part_code,
        weeks=8
    )


def get_vehicle_rul(
    db,
    vin,
    part_code
):
    """
    Get RUL estimate for one VIN/part.
    """

    return estimate_rul(
        db,
        vin,
        part_code
    )


def get_high_risk_vehicles(
    db,
    part_code,
    limit=10
):
    """
    Get highest-risk vehicles for a part.
    """

    predictions = score_fleet_for_part(
        db,
        part_code
    )

    return predictions[:limit]


def get_parts(db):

    parts = db.query(
        Part
    ).all()

    return [
        {
            "part_code": part.part_code,
            "part_name": part.part_name,
            "category": part.category,
            "design_life_km":
                part.design_life_km
        }
        for part in parts
    ]


def find_part(
    db,
    part_name
):

    parts = db.query(
        Part
    ).all()

    part_name = (
        part_name
        .strip()
        .lower()
    )

    for part in parts:

        if (
            part.part_name.lower()
            == part_name
        ):

            return {
                "part_code":
                    part.part_code,

                "part_name":
                    part.part_name,

                "category":
                    part.category
            }

    return None