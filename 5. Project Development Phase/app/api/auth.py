import os
import re
import random
import hashlib
import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

from app.database import get_db_session
import app.models as models

router = APIRouter(tags=["Authentication"])

# In-memory storage for pending user registrations
# Key: email (str), Value: {"name": str, "password": str, "otp": str, "expiry": datetime.datetime}
pending_registrations = {}

def send_otp_email(to_email: str, otp: str) -> bool:
    """
    Sends the OTP via SMTP to the user's email.
    Returns True if successfully sent, otherwise False.
    """
    load_dotenv(override=True)
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = os.getenv("SMTP_PORT", "587")
    smtp_user = os.getenv("SMTP_USER", "")
    smtp_password = os.getenv("SMTP_PASSWORD", "")

    if not (smtp_host and smtp_port and smtp_user and smtp_password) or "your_email" in smtp_user or "your_email_app_password" in smtp_password:
        print("[SMTP ERROR] Missing or placeholder SMTP credentials in .env file.")
        return False

    subject = "EduGenie - Your Verification OTP Code"
    
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #0f172a; color: #f8fafc; margin: 0; padding: 20px; }}
        .card {{ max-width: 480px; margin: 0 auto; background: #1e293b; border-radius: 12px; padding: 32px; border: 1px solid #334155; }}
        .header {{ text-align: center; margin-bottom: 24px; }}
        .title {{ font-size: 24px; font-weight: bold; color: #38bdf8; margin: 0; }}
        .subtitle {{ font-size: 14px; color: #94a3b8; margin-top: 6px; }}
        .otp-box {{ background: #0f172a; border: 2px dashed #6366f1; border-radius: 8px; padding: 18px; text-align: center; margin: 24px 0; }}
        .otp-code {{ font-size: 32px; font-weight: 800; letter-spacing: 6px; color: #a855f7; font-family: monospace; }}
        .instructions {{ font-size: 14px; color: #cbd5e1; line-height: 1.6; }}
        .footer {{ text-align: center; margin-top: 24px; font-size: 12px; color: #64748b; border-top: 1px solid #334155; padding-top: 16px; }}
      </style>
    </head>
    <body>
      <div class="card">
        <div class="header">
          <h1 class="title">EduGenie AI 🧠✨</h1>
          <p class="subtitle">Your Smart AI Study Assistant</p>
        </div>
        <p class="instructions">Hello,</p>
        <p class="instructions">Thank you for joining EduGenie! Use the following 6-digit verification code to complete your registration:</p>
        <div class="otp-box">
          <span class="otp-code">{otp}</span>
        </div>
        <p class="instructions">⚠️ This verification code is valid for <strong>10 minutes</strong>. Please do not share this OTP with anyone.</p>
        <div class="footer">
          If you did not request this verification code, you can safely ignore this email.<br>
          © EduGenie AI Assistant
        </div>
      </div>
    </body>
    </html>
    """
    text_body = (
        f"EduGenie Verification OTP\n\n"
        f"Your verification code is: {otp}\n\n"
        f"This code is valid for 10 minutes. Please do not share this OTP with anyone.\n\n"
        f"EduGenie Team 🧠✨"
    )

    try:
        port = int(smtp_port)
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"EduGenie AI <{smtp_user}>"
        msg["To"] = to_email

        part1 = MIMEText(text_body, "plain")
        part2 = MIMEText(html_body, "html")
        msg.attach(part1)
        msg.attach(part2)

        if port == 465:
            with smtplib.SMTP_SSL(smtp_host, port, timeout=15) as server:
                server.login(smtp_user, smtp_password)
                server.sendmail(smtp_user, [to_email], msg.as_string())
        else:
            with smtplib.SMTP(smtp_host, port, timeout=15) as server:
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.sendmail(smtp_user, [to_email], msg.as_string())

        print(f"[SMTP SUCCESS] Verification email sent to {to_email}")
        return True
    except Exception as e:
        print(f"[SMTP ERROR] Failed to send email to {to_email}: {e}")
        return False

# Helper utility: Get or create guest user
def get_current_user_from_request(request: Request, db):
    user_id_cookie = request.cookies.get("user_id")
    if user_id_cookie:
        user = db.query(models.User).filter(models.User.user_id == int(user_id_cookie)).first()
        if user:
            return user
            
    # Fallback/Default: Guest User
    guest = db.query(models.User).filter(models.User.email == "guest@edugenie.com").first()
    if not guest:
        # Create a default guest user with an encrypted/hashed dummy password
        hashed_pw = hashlib.sha256("guestpass123".encode()).hexdigest()
        guest = models.User(
            name="Guest User",
            email="guest@edugenie.com",
            password=hashed_pw
        )
        db.add(guest)
        db.commit()
        db.refresh(guest)
    return guest

@router.post("/register")
async def register_user(request: Request, response: Response):
    db = get_db_session()
    try:
        data = await request.json()
        name = str(data.get("name", "")).strip()
        email = str(data.get("email", "")).strip().lower()
        password = str(data.get("password", ""))
        
        if not name or not email or not password:
            return JSONResponse(status_code=400, content={"error": "All fields (name, email, password) are required."})
            
        # Email format verification
        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(email_pattern, email):
            return JSONResponse(status_code=400, content={"error": "Invalid email address format. Please enter a correct email (e.g. name@domain.com)."})
            
        # Check if user already exists
        existing_user = db.query(models.User).filter(models.User.email == email).first()
        if existing_user:
            return JSONResponse(status_code=400, content={"error": "Account already exists. Please Sign In."})
            
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        # Create user immediately
        new_user = models.User(
            name=name,
            email=email,
            password=hashed_password
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        # Log user in directly via session cookie
        response.set_cookie(key="user_id", value=str(new_user.user_id), httponly=True)
        return {
            "message": "Account created successfully!",
            "user": {"name": new_user.name, "email": new_user.email}
        }
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Registration failed: {str(e)}"})
    finally:
        db.close()


@router.post("/login")
async def login_user(request: Request, response: Response):
    db = get_db_session()
    try:
        data = await request.json()
        email = data.get("email")
        password = data.get("password")
        
        if not email or not password:
            return JSONResponse(status_code=400, content={"error": "Email and password are required."})
            
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        user = db.query(models.User).filter(models.User.email == email, models.User.password == hashed_password).first()
        
        if not user:
            return JSONResponse(status_code=401, content={"error": "Invalid email or password."})
            
        # Single step login: Set user_id in cookies directly
        response.set_cookie(key="user_id", value=str(user.user_id), httponly=True)
        return {"message": "Login successful!", "user": {"name": user.name, "email": user.email}}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Login failed: {str(e)}"})
    finally:
        db.close()

@router.post("/login-guest")
async def login_guest(response: Response):
    db = get_db_session()
    try:
        guest = db.query(models.User).filter(models.User.email == "guest@edugenie.com").first()
        if not guest:
            hashed_pw = hashlib.sha256("guestpass123".encode()).hexdigest()
            guest = models.User(name="Guest User", email="guest@edugenie.com", password=hashed_pw)
            db.add(guest)
            db.commit()
            db.refresh(guest)
        response.set_cookie(key="user_id", value=str(guest.user_id), httponly=True)
        return {"message": "Guest login successful."}
    finally:
        db.close()

@router.post("/logout")
async def logout_user(response: Response):
    response.delete_cookie(key="user_id")
    return {"message": "Logged out successfully."}

@router.get("/current-user")
async def get_current_user(request: Request):
    db = get_db_session()
    try:
        user_id_cookie = request.cookies.get("user_id")
        if user_id_cookie:
            user = db.query(models.User).filter(models.User.user_id == int(user_id_cookie)).first()
            if user:
                return {"logged_in": True, "name": user.name, "email": user.email}
        return {"logged_in": False, "name": "Guest User", "email": "guest@edugenie.com"}
    finally:
        db.close()
