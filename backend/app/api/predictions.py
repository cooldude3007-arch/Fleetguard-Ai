from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Part

from app.services.scoring import (
    score_fleet_for_part,
    score_vehicle_history
)


router = APIRouter(
    prefix="/predictions",
    tags=["Predictions"]
)


def get_db():

    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


@router.get("/{part_code}")
def get_predictions(
    part_code: str,
    db: Session = Depends(get_db)
):

    part = (
        db.query(Part)
        .filter(
            Part.part_code
            == part_code
        )
        .first()
    )

    if not part:

        raise HTTPException(
            status_code=404,
            detail="Part not found"
        )

    results = score_fleet_for_part(
        db,
        part_code
    )

    if not results:

        raise HTTPException(
            status_code=404,
            detail=(
                "No scoring rule found "
                "for this part"
            )
        )

    return {
        "part_code":
            part.part_code,

        "part_name":
            part.part_name,

        "vehicle_count":
            len(results),

        "predictions":
            results
    }

@router.get(
    "/{vin}/{part_code}"
)
def get_vehicle_prediction(
    vin: str,
    part_code: str,
    db: Session = Depends(get_db)
):

    part = (
        db.query(Part)
        .filter(
            Part.part_code == part_code
        )
        .first()
    )

    if not part:

        raise HTTPException(
            status_code=404,
            detail="Part not found"
        )

    result = score_vehicle_history(
        db,
        vin,
        part_code,
        weeks=8
    )

    if not result:

        raise HTTPException(
            status_code=404,
            detail=(
                "Vehicle, telematics, "
                "or scoring rule not found"
            )
        )

    return {
        "part_name":
            part.part_name,

        **result
    }