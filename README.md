# 🎙️ VocalDesk — AI-Powered Voice Complaint Management System

**Speak. Understand. Act. Resolve.**

VocalDesk is a full-stack Voice AI application that allows students to register campus complaints using natural speech. It combines browser-based speech recognition, Google Gemini AI, a Python FastAPI backend, and SQLite database operations to convert spoken complaints into actionable support tickets.

Built for the **Vocal Labs — Backend Developer (Core Tech) Hackathon**.

## 🌐 Live Demo

**Live Application:** https://vocaldesk-voice-ai.onrender.com/

**GitHub Repository:** https://github.com/Shikha-77/VocalDesk-Voice-AI

## 🎯 Problem Statement

Traditional campus complaint systems often require students to manually fill out forms, select categories, enter locations, and track complaint numbers.

VocalDesk simplifies this process with a voice-first interface.

Students can describe an issue naturally, while AI automatically extracts the relevant information and the backend registers a complaint.

## ✨ Key Features

- 🎤 **Voice-Based Complaint Registration:** Register campus complaints using spoken language.
- 🧠 **Gemini AI Integration:** Automatically understands complaints and extracts structured information.
- 🏷️ **Intelligent Categorization:** Classifies issues into Electrical, Internet, Cleaning, Plumbing, Furniture, and General.
- 📍 **Location Extraction:** Identifies locations mentioned in complaints.
- 🎫 **Automatic Ticket Generation:** Creates a unique ticket ID for each complaint.
- 🔊 **Voice Confirmation:** Provides spoken feedback after successful registration.
- 🔎 **Ticket Tracking:** Retrieve complaint details and status using a ticket ID.
- 📊 **Interactive Dashboard:** Displays complaint statistics, identified categories, and recent tickets.
- 💾 **Database Integration:** Saves complaint records using SQLite.
- ☁️ **Cloud Deployment:** Publicly deployed on Render.

## 🛠️ Technology Stack

| Layer           | Technology            | Purpose                               |
| --------------- | --------------------- | ------------------------------------- |
| Frontend        | HTML, CSS, JavaScript | Dashboard and user interaction        |
| Voice Input     | Web Speech API        | Speech-to-text conversion             |
| AI Processing   | Google Gemini         | Complaint analysis and classification |
| Backend         | Python, FastAPI       | API development and business logic    |
| Database        | SQLite                | Ticket storage and retrieval          |
| Voice Output    | SpeechSynthesis API   | Spoken ticket confirmation            |
| Deployment      | Render                | Public application hosting            |
| Version Control | Git and GitHub        | Source-code management                |

## ⚙️ How VocalDesk Works

```text
          Student Speaks
                |
                v
       Browser Speech Recognition
                |
                v
        Speech Converted to Text
                |
                v
       JavaScript Sends API Request
                |
                v
          FastAPI Backend
                |
                v
       Google Gemini AI Analysis
                |
                v
      Category + Location + Summary
                |
                v
        SQLite Database INSERT
                |
                v
       Unique Ticket ID Generated
                |
                v
       API Response to Frontend
                |
                v
      Dashboard + Voice Confirmation
```

### Example

**Student says:**

"The fan in classroom 205 is not working."

**AI identifies:**

- Category: Electrical
- Location: Classroom 205
- Description: Fan not working

**Backend action:** Registers the complaint in SQLite and generates a unique ticket ID.

**Voice response:** "Complaint registered successfully. Ticket number 4."

_Ticket numbers depend on existing records._

## 🔌 REST API Endpoints

| Method | Endpoint                 | Description                                        |
| ------ | ------------------------ | -------------------------------------------------- |
| GET    | `/`                      | Serve the VocalDesk dashboard                      |
| GET    | `/health`                | Check application health and API key configuration |
| POST   | `/complaint`             | Register a complaint without AI                    |
| POST   | `/ai-complaint`          | Analyze and register a complaint using Gemini      |
| GET    | `/complaints`            | Retrieve complaint records                         |
| GET    | `/complaint/{ticket_id}` | Retrieve a specific ticket                         |

### Example API Request

**POST `/ai-complaint`**

```json
{
  "description": "The Wi-Fi in Block B is not working."
}
```

**Example successful response:**

```json
{
  "ticket_id": 4,
  "description": "Wi-Fi is not working",
  "category": "Internet",
  "location": "Block B",
  "status": "Open",
  "message": "Complaint registered successfully. Ticket number 4."
}
```

## 🚀 Run Locally

### Prerequisites

- Python 3.13 or a compatible Python version
- Git
- A Gemini API key
- A modern browser with speech recognition support

### 1. Clone the repository

```bash
git clone https://github.com/Shikha-77/VocalDesk-Voice-AI.git
cd VocalDesk-Voice-AI
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Gemini

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_gemini_api_key
```

Never commit your real API key to GitHub.

### 5. Start the backend

```bash
uvicorn main:app --reload
```

### 6. Open the application

Frontend: http://127.0.0.1:8000

FastAPI documentation: http://127.0.0.1:8000/docs

## 🧪 Testing

The application supports testing of:

- Voice input and speech recognition
- AI complaint categorization
- Location extraction
- Ticket creation
- Database retrieval
- Ticket-status lookup
- Speech-based confirmation
- API error handling

### Sample Test

**Input:** "The water tap in Block A is leaking and needs urgent repair."

**Expected category:** Plumbing

**Expected location:** Block A

**Expected action:** Create a new ticket with an Open status.

## 🏗️ Backend Design

VocalDesk separates AI interpretation from database operations.

Google Gemini analyzes the complaint and returns structured information. FastAPI validates the resulting data and executes the ticket creation operation using SQLite.

The AI model does not directly execute database queries.

SQL parameters are used for inserting and retrieving complaints.

The application also supports a secondary Gemini model when the primary model request fails.

## ⚠️ Current Limitations

- SQLite storage on the Render Free instance is ephemeral; records may disappear after service restarts or redeployment.
- Speech recognition availability depends on browser support and microphone permissions.
- Gemini responses depend on external API availability and quota.
- Complaints can be created and retrieved, but there is currently no administrative workflow for resolving them.
- Similar complaints submitted separately can generate duplicate tickets.
- The current prototype does not include user authentication or role-based access control.

## 🔮 Future Improvements

- Persistent PostgreSQL database
- Secure admin authentication and role-based access control
- Complaint status updates and assignment workflow
- Duplicate complaint detection
- Multilingual voice support
- Email and SMS notifications
- Complaint prioritization and analytics
- Automated complaint routing to departments

## ☁️ Deployment

VocalDesk is deployed as a Python web service on Render.

**Build Command:**

```bash
pip install -r requirements.txt
```

**Start Command:**

```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

The Gemini API key is configured using Render environment variables.

## 🏆 Hackathon

**Event:** Vocal Labs — Round 2 Individual Hackathon

**Role:** Backend Developer (Core Tech)

**Challenge:** Build a Voice AI application that listens, understands, performs a real action, and responds.

**Solution:** VocalDesk converts spoken student complaints into structured and trackable support tickets through AI-assisted backend processing.

---

**VocalDesk — Turning Voice into Action.**
