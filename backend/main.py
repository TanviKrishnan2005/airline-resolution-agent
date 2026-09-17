from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agent import process_message, get_action_log

import json
from pathlib import Path


# =========================================================
# PATHS
# =========================================================

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"


# =========================================================
# CREATE APP
# =========================================================

app = FastAPI(
    title="Airline Resolution Agent",
    description="Customer-facing airline disruption resolution agent",
    version="1.0.0"
)


# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# REQUEST MODEL
# =========================================================

class ChatRequest(BaseModel):
    customer: str
    message: str


# =========================================================
# ROOT
# =========================================================

@app.get("/")
def root():
    return {
        "message": "Airline Resolution Agent API is running"
    }


# =========================================================
# CUSTOMERS
# =========================================================

@app.get("/customers")
def get_customers():

    with open(
        DATA_DIR / "customers.json",
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)


# =========================================================
# BOOKINGS
# =========================================================

@app.get("/bookings")
def get_bookings():

    with open(
        DATA_DIR / "bookings.json",
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)


# =========================================================
# CHAT
# =========================================================

@app.post("/chat")
def chat(request: ChatRequest):

    result = process_message(
        request.message,
        request.customer
    )

    return result


# =========================================================
# ACTIONS
# =========================================================

@app.get("/actions")
def get_actions(pnr: str | None = None):

    actions = get_action_log()

    # -----------------------------------------------------
    # If a PNR is provided, return only that customer's
    # actions.
    # -----------------------------------------------------

    if pnr:

        actions = [
            action
            for action in actions
            if action.get("pnr") == pnr
        ]

    return {
        "actions": actions
    }