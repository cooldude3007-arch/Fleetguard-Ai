from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Part


router = APIRouter(
    prefix="/parts",
    tags=["Parts"]
)


def get_db():

    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


@router.get("")
def get_parts(
    db: Session = Depends(get_db)
):

    parts = db.query(Part).all()

    return [
        {
            "part_code": part.part_code,
            "part_name": part.part_name,
            "category": part.category,
            "design_life_km": part.design_life_km
        }
        for part in parts
    ]