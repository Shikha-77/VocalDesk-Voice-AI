
import os
import sqlite3
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from google import genai
from google.genai import types


# --------------------------------------------------
# 1. PROJECT CONFIGURATION
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR / ".env", override=True)

DB_NAME = BASE_DIR / "complaints.db"
MODEL_NAME = "gemini-3.8-flash"

app = FastAPI(title="VocalDesk AI")


# --------------------------------------------------
# 2. DATA MODELS
# --------------------------------------------------

class Complaint(BaseModel):
    description: str = Field(
        min_length=3,
        max_length=2000
    )


class AIAnalysis(BaseModel):
    description: str
    category: Literal[
        "Electrical",
        "Internet",
        "Cleaning",
        "Plumbing",
        "Furniture",
        "General"
    ]
    location: str


# --------------------------------------------------
# 3. DATABASE SETUP
# --------------------------------------------------

def create_database():
    with sqlite3.connect(DB_NAME) as conn:

        conn.execute("""
            CREATE TABLE IF NOT EXISTS complaints (
                ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT NOT NULL,
                status TEXT DEFAULT 'Open',
                category TEXT DEFAULT 'General',
                location TEXT DEFAULT 'Not specified'
            )
        """)

        columns = [
            row[1]
            for row in conn.execute(
                "PRAGMA table_info(complaints)"
            ).fetchall()
        ]

        if "category" not in columns:
            conn.execute("""
                ALTER TABLE complaints
                ADD COLUMN category TEXT DEFAULT 'General'
            """)

        if "location" not in columns:
            conn.execute("""
                ALTER TABLE complaints
                ADD COLUMN location TEXT DEFAULT 'Not specified'
            """)


create_database()


# --------------------------------------------------
# 4. SAVE COMPLAINT TO DATABASE
# --------------------------------------------------

def save_complaint(
    description,
    category="General",
    location="Not specified"
):
    with sqlite3.connect(DB_NAME) as conn:

        cursor = conn.execute(
            """
            INSERT INTO complaints
            (description, category, location, status)
            VALUES (?, ?, ?, ?)
            """,
            (
                description,
                category,
                location,
                "Open"
            )
        )

        ticket_id = cursor.lastrowid

    return {
        "ticket_id": ticket_id,
        "description": description,
        "category": category,
        "location": location,
        "status": "Open",
        "message": (
            f"Complaint registered successfully. "
            f"Ticket number {ticket_id}."
        )
    }


# --------------------------------------------------
# 5. FRONTEND WEBSITE
# --------------------------------------------------

@app.get("/")
def home():
    return FileResponse(BASE_DIR / "index.html")


# --------------------------------------------------
# 6. HEALTH CHECK
# --------------------------------------------------

@app.get("/health")
def health():
    return {
        "status": "running",
        "application": "VocalDesk AI",
        "gemini_key_loaded": bool(
            os.getenv("GEMINI_API_KEY")
        )
    }


# --------------------------------------------------
# 7. REGISTER NORMAL COMPLAINT
# --------------------------------------------------

@app.post("/complaint")
def create_complaint(complaint: Complaint):
    return save_complaint(
        description=complaint.description
    )


# --------------------------------------------------
# 8. VIEW ALL COMPLAINTS
# --------------------------------------------------

@app.get("/complaints")
def get_complaints():
    with sqlite3.connect(DB_NAME) as conn:

        conn.row_factory = sqlite3.Row

        rows = conn.execute(
            """
            SELECT * FROM complaints
            ORDER BY ticket_id DESC
            """
        ).fetchall()

    return [dict(row) for row in rows]


# --------------------------------------------------
# 9. VIEW COMPLAINT BY TICKET ID
# --------------------------------------------------

@app.get("/complaint/{ticket_id}")
def get_complaint(ticket_id: int):

    with sqlite3.connect(DB_NAME) as conn:

        conn.row_factory = sqlite3.Row

        row = conn.execute(
            """
            SELECT * FROM complaints
            WHERE ticket_id = ?
            """,
            (ticket_id,)
        ).fetchone()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Complaint not found"
        )

    return dict(row)


# --------------------------------------------------
# 10. GEMINI AI COMPLAINT ANALYSIS
# --------------------------------------------------


@app.post("/ai-complaint")
def ai_complaint(complaint: Complaint):

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="Gemini API key missing"
        )

    client = genai.Client(api_key=api_key)

    prompt = f"""
    You are a campus complaint assistant.

    Analyze this complaint and extract:
    - description: Short summary
    - category: Electrical, Internet, Cleaning,
      Plumbing, Furniture, or General
    - location: Location mentioned by student

    If location is missing use "Not specified".
    Do not invent information.

    Student complaint: {complaint.description}
    """

    models = [
        "gemini-3.8-flash",
        "gemini-3.5-flash-lite"
    ]

    analysis = None

    for model_name in models:
        try:
            print("Trying AI model:", model_name)

            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=AIAnalysis
                )
            )

            if response.parsed is not None:
                analysis = AIAnalysis.model_validate(
                    response.parsed
                )
            elif response.text:
                analysis = AIAnalysis.model_validate_json(
                    response.text
                )
            else:
                raise ValueError("Empty AI response")

            print("AI success:", model_name)
            break

        except Exception as error:
            print(
                "AI model failed:",
                model_name,
                str(error)
            )

    if analysis is None:
        raise HTTPException(
            status_code=503,
            detail=(
                "Both Gemini models are unavailable. "
                "Please use normal complaint registration."
            )
        )

    return save_complaint(
        description=(
            analysis.description.strip()
            or complaint.description
        ),
        category=analysis.category,
        location=(
            analysis.location.strip()
            or "Not specified"
        )
    )
