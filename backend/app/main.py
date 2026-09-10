from fastapi import FastAPI

from app.api.parts import router as parts_router
from app.api.rules import router as rules_router
from app.api.predictions import router as predictions_router
from app.api.rul import router as rul_router
from app.api.agent import router as agent_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="FleetGuard AI API",
    description=(
        "Predictive Failure Engine "
        "for Commercial Vehicles"
    ),
    version="1.0.0"
)



app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



app.include_router(
    parts_router
)

app.include_router(
    rules_router
)

app.include_router(
    predictions_router
)

app.include_router(
    rul_router
)

app.include_router(
    agent_router
)


@app.get("/")
def home():

    return {
        "message": "FleetGuard AI API is running"
    }