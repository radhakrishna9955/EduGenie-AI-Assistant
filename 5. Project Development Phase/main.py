"""
main.py
--------------------------------------------------------------
EduGenie Learning Assistant — Central FastAPI Application
--------------------------------------------------------------
"""

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Database imports
from app.database import engine
import app.models as models

# Router imports
from app.api import auth, study

# Ensure database tables are created on app startup
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="EduGenie Learning Assistant",
    description="An AI-powered educational assistant for Q&A, explanations, summaries, quizzes, and learning paths.",
    version="1.0.0",
)

# Mount the /static directory at the /static URL path
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize Jinja2 templating
templates = Jinja2Templates(directory="templates")

# Include the routers
app.include_router(auth.router)
app.include_router(study.router)

@app.get("/")
async def read_root(request: Request):
    """Render the main application page."""
    return templates.TemplateResponse(request=request, name="index.html")

