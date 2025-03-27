from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from src.chatbot import PregnancyChatbot
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.models import Base
from passlib.context import CryptContext
from src.models import User, UserFormData
from sqlalchemy.orm import Session
from fastapi import HTTPException
from fastapi.responses import RedirectResponse
from datetime import datetime
from fastapi import Form
from src.models import Base, engine, User, UserFormData
from fastapi import Request 


Base.metadata.create_all(bind=engine)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

DATABASE_URL = "sqlite:///./babychatbot.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

app = FastAPI()

templates = Jinja2Templates(directory="frontend/templates")

chatbot = PregnancyChatbot()

app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

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
    Handle form submission and store user data in the database.
    """
    db: Session = SessionLocal()
    username = request.cookies.get("username")

    
    parsed_due_date = datetime.strptime(due_date, "%Y-%m-%d").date()

    
    existing_data = db.query(UserFormData).filter(UserFormData.username == username).first()
    if existing_data:
        existing_data.due_date = parsed_due_date
        existing_data.baby_gender = baby_gender
        existing_data.user_name = user_name
    else:
        new_data = UserFormData(
            username=username,
            due_date=parsed_due_date,
            baby_gender=baby_gender,
            user_name=user_name
        )
        db.add(new_data)

    db.commit()
    return RedirectResponse(url="/chat", status_code=303)

from fastapi import Request  

@app.post("/chat")
async def chat(request: Request, user_message: str = Form(...)):
    """
    Handle chat messages and include user data in the context.
    """
    db: Session = SessionLocal()
    username = request.cookies.get("username") 

    user_form_data = db.query(UserFormData).filter(UserFormData.username == username).first()
    if not user_form_data:
        raise HTTPException(status_code=400, detail="User form data not found. Please fill out the form first.")

    user_data["user_name"] = user_form_data.user_name
    user_data["due_date"] = user_form_data.due_date
    user_data["baby_gender"] = user_form_data.baby_gender

    context = (
        f"User Name: {user_data['user_name']}, Due Date for baby to be born: {user_data['due_date']}, "
        f"Baby Gender: {user_data['baby_gender']}. "
        "You are a pregnancy assistant. Provide advice and emotional support tailored to this user's pregnancy."
    )
    chatbot.history[0] = {"role": "system", "content": context}

    response = chatbot.send_message(user_message)
    return {"response": response}

@app.post("/register")
async def register_user(
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...)
):
    db: Session = SessionLocal()
    existing_user = db.query(User).filter((User.username == username) | (User.email == email)).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username or email already exists")

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
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid username or password")

    # Check if the user has already submitted the form
    user_data = db.query(UserFormData).filter(UserFormData.username == username).first()
    if user_data:
        redirect_url = "/chat"  # Redirect to chat if data exists
    else:
        redirect_url = "/form"  # Redirect to form if data doesn't exist

    response = RedirectResponse(url=redirect_url, status_code=303)
    response.set_cookie(key="username", value=username)  # Set the username cookie
    return response

@app.get("/form", response_class=HTMLResponse)
async def get_form(request: Request):
    """
    Render the form for user input (e.g., due date, gender, etc.).
    Show the form only if the user hasn't submitted it yet.
    """
    username = request.cookies.get("username")  # Get the logged-in username
    if not username:
        return RedirectResponse(url="/", status_code=303)  # Redirect to login if not logged in

    db: Session = SessionLocal()
    user_data = db.query(UserFormData).filter(UserFormData.username == username).first()

    # If user data exists, redirect to chat or profile page
    if user_data:
        return RedirectResponse(url="/chat", status_code=303)

    # Otherwise, render the form
    return templates.TemplateResponse("form.html", {"request": request})

@app.get("/chat", response_class=HTMLResponse)
async def get_chat(request: Request):
    """
    Render the chat interface.
    """
    username = request.cookies.get("username")  # Get the logged-in username
    if not username:
        return RedirectResponse(url="/", status_code=303)  # Redirect to login if not logged in

    db: Session = SessionLocal()
    user_data = db.query(UserFormData).filter(UserFormData.username == username).first()

    # Pass all user data to the template
    user_name = user_data.user_name if user_data else "Guest"
    user_due_date = user_data.due_date if user_data else "Not provided"
    user_baby_gender = user_data.baby_gender if user_data else "Not provided"

    return templates.TemplateResponse(
        "chat.html",
        {
            "request": request,
            "user_name": user_name,
            "user_due_date": user_due_date,
            "user_baby_gender": user_baby_gender,
        }
    )

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


@app.get("/facts", response_class=HTMLResponse)
async def get_facts(request: Request):
    """
    Provide interesting facts based on the user's form data.
    """
    db: Session = SessionLocal()
    username = request.cookies.get("username")  # Get the logged-in username

    user_data = db.query(UserFormData).filter(UserFormData.username == username).first()
    if not user_data:
        return {"message": "No form data found. Please fill out the form first."}

    if user_data.baby_gender == "girl":
        fact = "Did you know? Baby girls are born with more taste buds than boys!"
    elif user_data.baby_gender == "boy":
        fact = "Fun fact: Baby boys are more likely to be left-handed than girls!"
    else:
        fact = "Babies are born with 300 bones, but adults only have 206!"

    return templates.TemplateResponse(
        "facts.html",
        {"request": request, "fact": fact, "due_date": user_data.due_date}
    )


@app.get("/profile", response_class=HTMLResponse)
async def get_profile(request: Request):
    """
    Render the profile page where users can view and edit their data.
    """
    username = request.cookies.get("username")  # Get the logged-in username
    if not username:
        return RedirectResponse(url="/", status_code=303)  # Redirect to login if not logged in

    db: Session = SessionLocal()
    user_data = db.query(UserFormData).filter(UserFormData.username == username).first()

    # Pass the user's data to the profile template
    return templates.TemplateResponse("profile.html", {"request": request, "user_data": user_data})

@app.post("/update_profile", response_class=HTMLResponse)
async def update_profile(
    request: Request,
    user_name: str = Form(...),
    due_date: str = Form(...),
    baby_gender: str = Form(...)
):
    """
    Update the user's profile data in the database.
    """
    username = request.cookies.get("username")  # Get the logged-in username
    if not username:
        return RedirectResponse(url="/", status_code=303)  # Redirect to login if not logged in

    db: Session = SessionLocal()
    user_data = db.query(UserFormData).filter(UserFormData.username == username).first()

    # Update the user's data
    if user_data:
        user_data.user_name = user_name
        user_data.due_date = datetime.strptime(due_date, "%Y-%m-%d").date()
        user_data.baby_gender = baby_gender
        db.commit()

    return RedirectResponse(url="/profile", status_code=303)