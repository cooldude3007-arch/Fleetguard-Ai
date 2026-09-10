from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)

from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import SessionLocal

from app.agents.insight_agent import (
    run_insight_agent
)


router = APIRouter(
    prefix="/agent",
    tags=["Insight Agent"]
)

class ChatMessage(BaseModel):
    role: str
    text: str


class AgentQuestion(BaseModel):
    question: str
    history: Optional[List[ChatMessage]] = []

def get_db():

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()


@router.post("/query")
def query_agent(
    request: AgentQuestion,
    db: Session = Depends(get_db)
):

    question = request.question.strip()

    if not question:

        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty"
        )

    answer = run_insight_agent(
         db,
         question,
         request.history
        )

    return {
        "question": question,
        "answer": answer
    }