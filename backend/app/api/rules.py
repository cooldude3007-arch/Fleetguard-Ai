from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)

from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List

from app.database import SessionLocal
from app.models import (
    Part,
    RuleConfig
)

class RuleSignalUpdate(BaseModel):
    signal: str
    included: bool


class RuleUpdateRequest(BaseModel):
    signals: List[RuleSignalUpdate]


router = APIRouter(
    prefix="/rules",
    tags=["Rules"]
)


def get_db():

    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


@router.get("/{part_code}")
def get_rule(
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

    rules = (
        db.query(RuleConfig)
        .filter(
            RuleConfig.part_code == part_code
        )
        .order_by(
            RuleConfig.correlation_weight.desc()
        )
        .all()
    )

    if not rules:

        raise HTTPException(
            status_code=404,
            detail="Rule not found for this part"
        )

    return {
        "part_code": part.part_code,
        "part_name": part.part_name,
        "signals": [
            {
                "signal": rule.signal,
                "weight": rule.correlation_weight,
                "included": rule.included
            }
            for rule in rules
        ]
    }

@router.put("/{part_code}")
def update_rule(
    part_code: str,
    request: RuleUpdateRequest,
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

    rules = (
        db.query(RuleConfig)
        .filter(
            RuleConfig.part_code == part_code
        )
        .all()
    )

    if not rules:
        raise HTTPException(
            status_code=404,
            detail="Rule not found"
        )

    update_map = {
        item.signal: item.included
        for item in request.signals
    }

    for rule in rules:

        if rule.signal in update_map:

            rule.included = (
                update_map[rule.signal]
            )

    db.commit()

    return {
        "message":
            "Rule updated successfully",

        "part_code":
            part_code
    }