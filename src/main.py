from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from src.chatbot import PregnancyChatbot
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.models import Base
from passlib.context import CryptContext
from src.models import User
from sqlalchemy.orm import Session
from fastapi import HTTPException
from fastapi.responses import RedirectResponse



# Create a password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

DATABASE_URL = "sqlite:///./babychatbot.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI()

# Initialize templates for rendering HTML
templates = Jinja2Templates(directory="frontend/templates")

# Initialize the chatbot
chatbot = PregnancyChatbot()

# Serve static files (e.g., CSS, JS)
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

# Store user data
user_data = {}

@app.get("/", response_class=HTMLResponse)
async def get_login(request: Request):
    """
    Render the login screen.
    """
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/submit", response_class=HTMLResponse)
async def submit_form(
    request: Request,
    due_date: str = Form(...),
    baby_gender: str = Form(...),
    user_name: str = Form(...)
):
    """
    Handle form submission and store user data.
    """
    global user_data
    user_data = {
        "due_date": due_date,
        "baby_gender": baby_gender,
        "user_name": user_name,
    }
    return RedirectResponse(url="/chat", status_code=303)

@app.post("/chat")
async def chat(user_message: str = Form(...)):
    """
    Handle chat messages and include user data in the context.
    """
    global user_data
    context = (
        f"User Name: {user_data['user_name']}, Due Date: {user_data['due_date']}, "
        f"Baby Gender: {user_data['baby_gender']}. "
        "You are a pregnancy assistant. Provide advice and emotional support tailored to this user's pregnancy."
    )
    chatbot.history[0] = {"role": "system", "content": context}

    # Get AI response
    response = chatbot.send_message(user_message)
    return {"response": response}\
    
@app.post("/register")
async def register_user(
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...)
):
    db: Session = SessionLocal()
    # Check if the username or email already exists
    existing_user = db.query(User).filter((User.username == username) | (User.email == email)).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username or email already exists")

    # Hash the password and save the user
    hashed_password = hash_password(password)
    new_user = User(username=username, email=email, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User registered successfully"}

@app.post("/login", response_class=HTMLResponse)
async def login_user(
    request: Request,
    username: str = Form(...),
    password: str = Form(...)
):
    db: Session = SessionLocal()
    # Find the user by username
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid username or password")

    # Redirect to the form after successful login
    response = RedirectResponse(url="/form", status_code=303)
    response.set_cookie(key="username", value=username)  # Optional: Set a cookie for session tracking
    return response

@app.get("/form", response_class=HTMLResponse)
async def get_form(request: Request):
    """
    Render the form for user input (e.g., due date, gender, etc.).
    """
    username = request.cookies.get("username")  # Optional: Get the username from the cookie
    if not username:
        return RedirectResponse(url="/", status_code=303)  # Redirect to login if not logged in
    return templates.TemplateResponse("form.html", {"request": request})

@app.get("/chat", response_class=HTMLResponse)
async def get_chat(request: Request):
    """
    Render the chatbot interface.
    """
    username = request.cookies.get("username")  # Optional: Get the username from the cookie
    if not username:
        return RedirectResponse(url="/", status_code=303)  # Redirect to login if not logged in
    return templates.TemplateResponse("chat.html", {"request": request, "user_name": user_data.get("user_name")})

@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie(key="username")  # Clear the username cookie
    return response

@app.get("/register", response_class=HTMLResponse)
async def get_register(request: Request):
    """
    Render the registration page.
    """
    return templates.TemplateResponse("register.html", {"request": request})