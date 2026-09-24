import os
import re
import random
import hashlib
import datetime
import smtplib
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
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = os.getenv("SMTP_PORT")
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")

    subject = "EduGenie Verification OTP"
    body = (
        f"Hello,\n\n"
        f"Your EduGenie verification code is: {otp}\n\n"
        f"This OTP is valid for 10 minutes. If you did not request this, please ignore this email.\n\n"
        f"Happy Learning!\n"
        f"EduGenie Team 🧠✨"
    )

    if not (smtp_host and smtp_port and smtp_user and smtp_password):
        print("[SMTP ERROR] Missing SMTP environment variables in .env configuration.")
        return False

    try:
        port = int(smtp_port)
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = smtp_user
        msg["To"] = to_email

        with smtplib.SMTP(smtp_host, port) as server:
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
async def register_user(request: Request):
    db = get_db_session()
    try:
        data = await request.json()
        name = data.get("name")
        email = data.get("email")
        password = data.get("password")
        
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
            
        # Generate 6-digit OTP
        generated_otp = f"{random.randint(100000, 999999)}"
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        # Store in transient registration dictionary
        pending_registrations[email] = {
            "name": name,
            "password": hashed_password,
            "otp": generated_otp,
            "expiry": datetime.datetime.utcnow() + datetime.timedelta(minutes=10)
        }
        
        # Trigger OTP send
        sent_via_smtp = send_otp_email(email, generated_otp)
        
        print(f"\n=======================================================")
        print(f"🔑 [EduGenie Verification OTP] For: {email} -> CODE: {generated_otp}")
        print(f"=======================================================\n")
        
        if sent_via_smtp:
            msg = "Verification OTP has been sent to your email. Please check your inbox."
        else:
            msg = f"Email delivery unconfigured. Your Verification Code is: <b style='color:var(--brand-cyan); font-size:1.1rem;'>{generated_otp}</b>"
            
        return {
            "verification_required": True,
            "email": email,
            "message": msg
        }
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Registration initiation failed: {str(e)}"})
    finally:
        db.close()

@router.post("/verify-registration")
async def verify_registration(request: Request, response: Response):
    db = get_db_session()
    try:
        data = await request.json()
        email = data.get("email")
        otp = data.get("otp")
        
        if not email or not otp:
            return JSONResponse(status_code=400, content={"error": "Email and verification OTP are required."})
            
        pending = pending_registrations.get(email)
        if not pending:
            return JSONResponse(status_code=400, content={"error": "No pending registration found for this email. Please register again."})
            
        # Expiry check
        if datetime.datetime.utcnow() > pending["expiry"]:
            pending_registrations.pop(email, None)
            return JSONResponse(status_code=400, content={"error": "Verification OTP has expired. Please sign up again."})
            
        # Code check
        if pending["otp"] != str(otp).strip():
            return JSONResponse(status_code=400, content={"error": "Incorrect verification code. Please check and try again."})
            
        # OTP is correct! Create user database entry
        new_user = models.User(
            name=pending["name"],
            email=email,
            password=pending["password"]
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        # Remove from transient registrations
        pending_registrations.pop(email, None)
        
        # Log user in directly
        response.set_cookie(key="user_id", value=str(new_user.user_id), httponly=True)
        return {"message": "Account created and verified successfully!", "user": {"name": new_user.name, "email": new_user.email}}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Verification failed: {str(e)}"})
    finally:
        db.close()

@router.post("/resend-registration-otp")
async def resend_registration_otp(request: Request):
    try:
        data = await request.json()
        email = data.get("email")
        
        if not email:
            return JSONResponse(status_code=400, content={"error": "Email is required to resend OTP."})
            
        pending = pending_registrations.get(email)
        if not pending:
            return JSONResponse(status_code=400, content={"error": "No pending registration found. Please start sign up from the beginning."})
            
        # Regenerate OTP
        new_otp = f"{random.randint(100000, 999999)}"
        pending["otp"] = new_otp
        pending["expiry"] = datetime.datetime.utcnow() + datetime.timedelta(minutes=10)
        
        # Send
        sent_via_smtp = send_otp_email(email, new_otp)
        print(f"\n=======================================================")
        print(f"🔑 [EduGenie Resent OTP] For: {email} -> CODE: {new_otp}")
        print(f"=======================================================\n")
        
        if sent_via_smtp:
            msg = "A new verification OTP has been sent. Please check your email."
        else:
            msg = f"Your new Verification Code is: <b style='color:var(--brand-cyan); font-size:1.1rem;'>{new_otp}</b>"
            
        return {
            "message": msg
        }
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Resending OTP failed: {str(e)}"})


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
