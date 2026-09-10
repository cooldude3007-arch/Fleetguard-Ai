from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)

from sqlalchemy.orm import Session

from app.database import SessionLocal

from app.services.rul import (
    estimate_rul
)


router = APIRouter(
    prefix="/rul",
    tags=["RUL"]
)


def get_db():

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()


@router.get(
    "/{vin}/{part_code}"
)
def get_rul(
    vin: str,
    part_code: str,
    db: Session = Depends(get_db)
):

    result = estimate_rul(
        db,
        vin,
        part_code
    )

    if not result:

        raise HTTPException(
            status_code=404,
            detail=(
                "Vehicle, part, telematics, "
                "or scoring rule not found"
            )
        )

    return result