import os
import sqlite3
import time
import math
import hashlib
import re
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
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
# COMPLAINT PROTECTION
# --------------------------------------------------

COOLDOWN_SECONDS = 30
DUPLICATE_WINDOW_SECONDS = 24 * 60 * 60


def create_submission_history_table():
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS complaint_submission_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id TEXT NOT NULL,
                description_hash TEXT NOT NULL,
                submitted_at REAL NOT NULL,
                ticket_id INTEGER NOT NULL
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_submission_client_time
            ON complaint_submission_history (client_id, submitted_at)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_submission_duplicate
            ON complaint_submission_history (client_id, description_hash, submitted_at)
        """)


create_submission_history_table()


def client_identifier(request: Request) -> str:
    # The IP visible to FastAPI is an approximation of client identity.
    # Do not trust arbitrary X-Forwarded-For headers supplied by visitors.
    return request.client.host if request.client else "unknown"


def description_fingerprint(description: str) -> str:
    normalized = re.sub(r"\s+", " ", description).strip().casefold()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def enforce_complaint_rules(conn, client_id: str, fingerprint: str, now: float):
    last = conn.execute(
        """SELECT submitted_at FROM complaint_submission_history
           WHERE client_id = ? ORDER BY submitted_at DESC LIMIT 1""",
        (client_id,)
    ).fetchone()

    if last is not None:
        elapsed = now - last[0]
        if elapsed < COOLDOWN_SECONDS:
            remaining = max(1, math.ceil(COOLDOWN_SECONDS - elapsed))
            raise HTTPException(
                status_code=429,
                detail=f"Please wait {remaining} seconds before submitting another complaint.",
                headers={"Retry-After": str(remaining)}
            )

    existing = conn.execute(
        """SELECT ticket_id FROM complaint_submission_history
           WHERE client_id = ? AND description_hash = ? AND submitted_at >= ?
           ORDER BY submitted_at DESC LIMIT 1""",
        (client_id, fingerprint, now - DUPLICATE_WINDOW_SECONDS)
    ).fetchone()
    if existing is not None:
        raise HTTPException(
            status_code=409,
            detail=f"Duplicate complaint already registered as ticket {existing[0]} within the last 24 hours."
        )


def precheck_complaint(request: Request, description: str):
    # Fast check before calling Gemini, to reduce unnecessary AI usage.
    # The same check runs inside a write transaction when saving.
    with sqlite3.connect(DB_NAME, timeout=10) as conn:
        enforce_complaint_rules(
            conn,
            client_identifier(request),
            description_fingerprint(description),
            time.time()
        )


# --------------------------------------------------
# 4. SAVE COMPLAINT TO DATABASE
# --------------------------------------------------

def save_complaint(
    description,
    category="General",
    location="Not specified",
    *,    
    request: Request,
    original_description: str
):
    client_id = client_identifier(request)
    fingerprint = description_fingerprint(original_description)

    # Transaction protects against simultaneous requests creating tickets.
    with sqlite3.connect(DB_NAME, timeout=10) as conn:
        conn.execute("BEGIN IMMEDIATE")
        now = time.time()
        enforce_complaint_rules(conn, client_id, fingerprint, now)

        cursor = conn.execute(
            """INSERT INTO complaints
               (description, category, location, status)
               VALUES (?, ?, ?, ?)""",
            (description, category, location, "Open")
        )
        ticket_id = cursor.lastrowid
        conn.execute(
            """INSERT INTO complaint_submission_history
               (client_id, description_hash, submitted_at, ticket_id)
               VALUES (?, ?, ?, ?)""",
            (client_id, fingerprint, now, ticket_id)
        )

    return {
        "ticket_id": ticket_id,
        "description": description,
        "category": category,
        "location": location,
        "status": "Open",
        "message": f"Complaint registered successfully. Ticket number {ticket_id}."
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
def create_complaint(complaint: Complaint, request: Request):
    precheck_complaint(request, complaint.description)
    return save_complaint(
        description=complaint.description.strip(),
        request=request,
        original_description=complaint.description
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
def ai_complaint(complaint: Complaint, request: Request):

    precheck_complaint(request, complaint.description)

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
        ),
        request=request,
        original_description=complaint.description
    )

from datetime import datetime
from pydantic import BaseModel

class Reminder(BaseModel):
    task: str = Field(min_length=1, max_length=500)
    due_at: datetime


def create_reminders_table():
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS reminders (
                reminder_id INTEGER PRIMARY KEY AUTOINCREMENT,
                task TEXT NOT NULL,
                due_at TEXT NOT NULL,
                status TEXT DEFAULT 'Pending'
            )
        """)


create_reminders_table()


@app.post("/reminders")
def create_reminder(reminder: Reminder):
    task = reminder.task.strip()

    if not task:
        raise HTTPException(
            status_code=422,
            detail="Reminder task cannot be empty"
        )

    if reminder.due_at.tzinfo is None:
        raise HTTPException(
            status_code=422,
            detail="Date and time must include a timezone"
        )

    if reminder.due_at.timestamp() <= datetime.now().timestamp():
        raise HTTPException(
            status_code=422,
            detail="Reminder must be scheduled in the future"
        )

    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.execute(
            """
            INSERT INTO reminders (task, due_at)
            VALUES (?, ?)
            """,
            (task, reminder.due_at.isoformat())
        )

        reminder_id = cursor.lastrowid

    return {
        "reminder_id": reminder_id,
        "task": task,
        "due_at": reminder.due_at.isoformat(),
        "status": "Pending",
        "message": "Reminder saved successfully"
    }


@app.get("/reminders")
def get_reminders():
    with sqlite3.connect(DB_NAME) as conn:
        conn.row_factory = sqlite3.Row

        rows = conn.execute(
            """
            SELECT * FROM reminders
            ORDER BY due_at ASC
            """
        ).fetchall()

    return [dict(row) for row in rows]

from datetime import timedelta, timezone
from pydantic import BaseModel

IST = timezone(timedelta(hours=5, minutes=30))


class VoiceReminderRequest(BaseModel):
    text: str = Field(min_length=3, max_length=1000)


class ReminderAnalysis(BaseModel):
    task: str
    due_at: str


@app.post("/ai-reminder")
def create_ai_reminder(request: VoiceReminderRequest):

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="Gemini API key missing"
        )

    current_time = datetime.now(IST)

    prompt = f"""
    You are an AI reminder assistant.

    Current date and time in India:
    {current_time.isoformat()}

    Extract a reminder from this voice command:

    {request.text}

    Return:
    task: The task the user wants to remember.
    due_at: The scheduled date and time in ISO 8601
            format with India timezone +05:30.

    Interpret relative dates such as tomorrow and Friday
    using the current date.

    Do not invent a time if the user does not specify one.
    If the scheduled time is missing or ambiguous,
    return an empty string for due_at.
    """

    client = genai.Client(api_key=api_key)

    analysis = None

    for model in [
        "gemini-3.8-flash",
        "gemini-3.5-flash-lite"
    ]:
        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=ReminderAnalysis
                )
            )

            if response.parsed is not None:
                analysis = ReminderAnalysis.model_validate(
                    response.parsed
                )
            elif response.text:
                analysis = ReminderAnalysis.model_validate_json(
                    response.text
                )

            if analysis is not None:
                break

        except Exception as error:
            print("Reminder AI error:", str(error))

    if analysis is None:
        raise HTTPException(
            status_code=502,
            detail="AI reminder processing failed"
        )

    if not analysis.task.strip() or not analysis.due_at.strip():
        raise HTTPException(
            status_code=422,
            detail="Please specify a task, date and time"
        )

    try:
        due_date = datetime.fromisoformat(analysis.due_at)
    except ValueError:
        raise HTTPException(
            status_code=422,
            detail="AI returned an invalid reminder date"
        )

    if due_date.tzinfo is None:
        raise HTTPException(
            status_code=422,
            detail="Reminder must include a timezone"
        )

    if due_date <= datetime.now(IST):
        raise HTTPException(
            status_code=422,
            detail="Reminder date must be in the future"
        )

    saved = create_reminder(
        Reminder(
            task=analysis.task.strip(),
            due_at=due_date
        )
    )

    saved["message"] = (
        f"Reminder saved for {analysis.task.strip()}"
    )

    return saved
