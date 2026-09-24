# 🧠 EduGenie — AI-Powered Educational Study Assistant

EduGenie is an intelligent, hybrid AI study platform designed to revolutionize student learning. It blends high-performance cloud AI (Google Gemini 2.5 Flash) with resource-efficient local edge models (Hugging Face LaMini-Flan-T5) to provide instant Q&As, deep concept explanations, smart summaries, adaptive quizzes, and learning roadmaps.

---

## 🚀 Key Features

1. **💬 Instant Academic Q&A (Cloud AI - Gemini 2.5 Flash)**
   - Delivers direct, accurate explanations for academic questions in sciences, engineering, and mathematics.
2. **💡 Deep Concept Explainer (Local / Edge AI - LaMini-Flan-T5-783M)**
   - Step-by-step conceptual breakdowns with real-world analogies, mechanisms, and key takeaways.
3. **📝 Intelligent Text Summarizer (Cloud AI - Gemini 2.5 Flash)**
   - Condenses lengthy textbook excerpts, academic papers, and lecture transcripts into actionable bullet points.
4. **✏️ Interactive MCQ Quiz Generator (Cloud AI - Gemini 2.5 Flash)**
   - Generates 3 deep conceptual multiple-choice questions with instant scoring, real-time feedback, and correct answer explanations.
5. **🗺️ Adaptive Learning Roadmap (Cloud AI - Gemini 2.5 Flash)**
   - Builds phased beginner-to-advanced curriculums with milestones and curated textbooks, courses, and project recommendations.
6. **📚 Personal Study Notebook & History Log (SQLite + SQLAlchemy)**
   - Persistent database logging for all queries and AI responses with search filtering, single-note deletion, and full history management.
7. **🔊 Speech Synthesis (TTS) & Note Exporting**
   - Built-in text-to-speech audio reader, 1-click clipboard copy, and `.md` note downloads for all generated answers.
8. **🎨 Glassmorphic SaaS Design & Dark/Light Mode**
   - Modern cyber-gradient aesthetic, interactive particle canvas, and responsive mobile layout.

---

## 🛠️ Technology Stack

| Layer | Technologies Used |
|---|---|
| **Frontend** | HTML5, Modern CSS3 (Glassmorphism & Cyber Accents), Vanilla JavaScript (Web Speech API, Canvas API) |
| **Backend Framework** | FastAPI (Python 3.10+), Uvicorn ASGI Server, Jinja2 Templates |
| **Cloud AI Model** | Google Gemini 2.5 Flash (`google-generativeai`) |
| **Local Edge Model** | Hugging Face Transformers (`MBZUAI/LaMini-Flan-T5-783M`, PyTorch) |
| **Database & ORM** | SQLite3, SQLAlchemy ORM |
| **Authentication** | SHA-256 Hashed Passwords, Cookie Sessions, Email OTP Verification (`smtplib`) |

---

## 📦 Getting Started & Setup Guide

### 1. Prerequisites
- Python 3.10 or higher
- Git

### 2. Installation

Navigate into the development directory:
```bash
cd "5. Project Development Phase"
```

Create and activate a virtual environment:
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

Install the required dependencies:
```bash
pip install -r requirements.txt
```

### 3. Environment Variables

Create a `.env` file inside `5. Project Development Phase/`:
```env
# Google Gemini API Key (Get from https://aistudio.google.com/)
GEMINI_API_KEY=your_gemini_api_key_here

# (Optional) SMTP configuration for email OTP registration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_gmail_app_password
```

*(Note: If `GEMINI_API_KEY` is not provided, EduGenie automatically provides intelligent structured fallback responses for seamless local testing and reviews).*

### 4. Running the Application

Launch the FastAPI application server:
```bash
uvicorn main:app --reload --port 8000
```

Open your browser and navigate to:
```
http://127.0.0.1:8000
```

---

## 👥 Project Team

| Team Member | Designated Project Role | Core Responsibilities |
|---|---|---|
| **Radha Krishna** | ⭐ Team Lead & Full-Stack Lead | Project Architecture, FastAPI core, Glassmorphism UI/UX |
| **Yashwanth** | Database Architect & Backend Engineer | SQLite schema, SQLAlchemy ORM, Authentication & Security |
| **Shanker** | AI & Cloud DevOps Engineer | Gemini 2.5 Flash API, Transformers NLP, Deployment |


---

## 📄 License
Academic & Educational Project License. Built for project demonstration and review.