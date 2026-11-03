# 🎙️ VocalDesk AI

### Voice-to-Action Smart Campus Support Assistant

**Speak. Understand. Act. Respond.**

VocalDesk AI is a voice-powered campus support application that converts natural-language commands into real backend actions using Google Gemini AI, FastAPI, and SQLite.

The platform enables students to register campus complaints, track complaint tickets, and create scheduled reminders using voice commands.

**Live Application:** https://vocaldesk-voice-ai.onrender.com/

**GitHub Repository:** https://github.com/Shikha-77/VocalDesk-Voice-AI

---

## 🚀 Problem Statement

Traditional campus complaint management often involves manual forms, unclear issue categorization, and inconvenient tracking processes.

Students may also forget important academic deadlines, submissions, and scheduled activities.

VocalDesk AI addresses these problems through a unified voice-based interface that allows students to communicate naturally while the application performs real backend operations.

## ✨ Key Features

### 🎤 1. AI-Powered Voice Complaint Registration

- Register complaints through voice or text.
- Convert speech into text using the browser's Web Speech API.
- Analyze complaints using Google Gemini AI.
- Automatically identify complaint category and location.
- Generate a unique complaint ticket.
- Store registered complaints in SQLite.
- Provide spoken ticket confirmations.

**Supported Categories:** Electrical, Internet, Cleaning, Plumbing, Furniture, and General.

### 🎫 2. Complaint Tracking Dashboard

- View registered complaint tickets.
- Search complaints using ticket IDs.
- Display complaint description, category, location, and status.
- View dashboard statistics and recent complaints.

### 🛡️ 3. Complaint Rate Limiting and Duplicate Protection

- Enforce a 30-second cooldown between successful complaint submissions from the same detected client.
- Return HTTP 429 when the cooldown is active.
- Detect identical normalized complaint descriptions within a 24-hour window for the same detected client.
- Return HTTP 409 for detected duplicates.
- Use SQLite transactions to protect complaint creation.

Client identification is currently IP-based and is intended for prototype use.

### ⏰ 4. AI Voice Reminder Assistant

- Create reminders using natural-language voice commands.
- Understand relative dates such as "tomorrow" and "Friday".
- Extract reminder task, date, and time with Gemini AI.
- Save reminders in SQLite.
- Display reminders and their status.
- Speak confirmation after reminder creation.
- Show due-reminder alerts while the dashboard remains open.

**Example command:**

"Remind me to submit my assignment tomorrow at 5 PM."

### 🔊 5. Voice Responses

VocalDesk provides spoken confirmations using the browser's SpeechSynthesis API, completing the voice-to-action workflow.

---

## 🧠 How VocalDesk Works

**Voice Input → Speech Recognition → Gemini AI → FastAPI Backend → SQLite Database → Voice Response**

### Complaint Workflow

1. A student speaks or types a campus complaint.
2. Speech recognition converts the voice input into text.
3. FastAPI checks complaint restrictions.
4. Gemini AI extracts the complaint description, category, and location.
5. FastAPI creates a ticket and saves it in SQLite.
6. The dashboard displays the ticket and provides spoken confirmation.

### Reminder Workflow

1. A user speaks or types a reminder request.
2. Gemini AI identifies the task and scheduled date/time.
3. FastAPI validates the date and saves the reminder.
4. The dashboard displays the saved reminder.
5. VocalDesk speaks the confirmation.
6. While the dashboard remains open, the application can display alerts for due reminders.

---

## 🛠️ Technology Stack

| Component            | Technology              |
| -------------------- | ----------------------- |
| Frontend             | HTML5, CSS3, JavaScript |
| Backend              | Python, FastAPI         |
| AI Model Integration | Google Gemini API       |
| Speech Recognition   | Web Speech API          |
| Text-to-Speech       | SpeechSynthesis API     |
| Database             | SQLite                  |
| API Testing          | FastAPI Swagger UI      |
| Deployment           | Render                  |
| Version Control      | Git and GitHub          |

---

## 📁 Project Structure

    VocalDesk/
    ├── main.py
    ├── index.html
    ├── requirements.txt
    ├── README.md
    ├── .gitignore
    └── .env                  # Local environment variables; not committed

Additional local development files include the SQLite database and Python virtual environment.

---

## 🔌 API Endpoints

| Method | Endpoint                 | Purpose                                      |
| ------ | ------------------------ | -------------------------------------------- |
| GET    | `/`                      | Serve the dashboard                          |
| GET    | `/health`                | Check backend health                         |
| POST   | `/complaint`             | Register a standard complaint                |
| POST   | `/ai-complaint`          | Analyze and register an AI-powered complaint |
| GET    | `/complaints`            | Retrieve registered complaints               |
| GET    | `/complaint/{ticket_id}` | Retrieve a complaint by ID                   |
| POST   | `/reminders`             | Create a reminder                            |
| GET    | `/reminders`             | Retrieve saved reminders                     |
| POST   | `/ai-reminder`           | Create a reminder using Gemini AI            |

**Interactive API documentation:** `/docs`

---

## 💻 Running Locally

### Prerequisites

- Python 3.10 or later
- Google Gemini API key
- Internet connection for Gemini AI requests
- A browser supporting speech recognition

### 1. Clone the repository

    git clone https://github.com/Shikha-77/VocalDesk-Voice-AI.git
    cd VocalDesk-Voice-AI

### 2. Create and activate a virtual environment

Windows PowerShell:

    python -m venv .venv
    .\.venv\Scripts\Activate.ps1

### 3. Install dependencies

    pip install -r requirements.txt

### 4. Configure environment variables

Create a `.env` file in the project root:

    GEMINI_API_KEY=your_gemini_api_key_here

Never commit the actual API key to GitHub.

### 5. Start the backend

    uvicorn main:app --reload

### 6. Open the application

Dashboard:

http://127.0.0.1:8000/

Swagger API Documentation:

http://127.0.0.1:8000/docs

---

## ☁️ Deployment

The project is deployed using Render.

**Build Command:**

    pip install -r requirements.txt

**Start Command:**

    uvicorn main:app --host 0.0.0.0 --port $PORT

Configure the `GEMINI_API_KEY` environment variable through Render's environment settings.

**Live Demo:** https://vocaldesk-voice-ai.onrender.com/

---

## 🔐 Security and Reliability

The prototype includes server-side complaint cooldown enforcement, duplicate complaint checks, input validation, and environment-variable-based API key management.

### Current Limitations

- Authentication and per-user access control are not yet implemented.
- Client identification uses IP addresses, which may be shared between users.
- Similar complaints written with different wording may not be recognized as duplicates.
- Reminder alerts require the browser page to remain open.
- Background push notifications, SMS, and email reminders are not implemented.
- SQLite data on Render's ephemeral filesystem may be lost after restarts or redeployments.
- Gemini AI requests require a working internet connection and an available model.

The deployed application is a functional hackathon prototype, not a production-ready private student records platform.

---

## 🔮 Future Enhancements

- Student and administrator authentication
- Role-based complaint management
- Complaint assignment and resolution workflows
- Persistent PostgreSQL database
- Email and push notifications
- Background reminder scheduling
- Multilingual voice support
- Enhanced semantic duplicate complaint detection
- Department-specific ticket routing
- Analytics and administrative reporting

---

## 🎯 Hackathon Objective

VocalDesk AI was developed to demonstrate a practical Voice AI application capable of understanding natural-language requests and converting them into meaningful backend actions.

The application follows the required workflow:

**Voice Input → AI Understanding → Real Action → Voice Output**

The project showcases backend API development, structured AI responses, database operations, rate limiting, deployment, and user-facing voice interaction.

---

## 👩‍💻 Project Developer

Developed as an individual Voice AI hackathon project for the Vocal Labs Backend Developer (Core Tech) opportunity.

---

**VocalDesk AI — Turning Voice into Action.**
