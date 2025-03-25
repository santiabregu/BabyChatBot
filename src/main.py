from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from src.chatbot import PregnancyChatbot

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
async def get_form(request: Request):
    """
    Render the form for user input (e.g., due date, gender, etc.).
    """
    return templates.TemplateResponse("form.html", {"request": request})

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
    return templates.TemplateResponse("chat.html", {"request": request, "user_name": user_name})

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
    return {"response": response}