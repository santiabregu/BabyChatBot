from google import genai
from google.genai import types
from src.config import GEMINI_API_KEY  
import logging
import random
import re

# Configure logging
logging.basicConfig(level=logging.ERROR)

class PregnancyChatbot:
    def __init__(self):
        self.history = [
            {
                "role": "system",
                "content": (
                    "You are a friendly and supportive pregnancy assistant. "
                    "Your role is to provide **practical** and **empathetic** answers to pregnancy-related questions. "
                    "If the user expresses distress, always provide **at least one actionable solution** first, then empathy. "
                    "Keep responses **concise, factual, and solution-driven**."
                ),
            }
        ]
        self.client = genai.Client(api_key=GEMINI_API_KEY)

    def truncate_response(self, response_text):
        """
        Truncates the response to end at the last complete sentence.
        """
        if "." in response_text:
            return response_text[:response_text.rfind(".") + 1]
        return response_text

    def detect_emotion(self, user_message):
        """
        Classifies the user's distress level (mild or severe).
        """
        mild_discomfort = [
            "nauseous", "nausea", "vomiting", "morning sickness",
            "tired", "fatigue", "cravings", "back pain"
        ]
        severe_distress = [
            "worried", "anxious", "scared", "stressed", "depressed",
            "severe pain", "bleeding", "fainting", "dizzy"
        ]

        for word in severe_distress:
            if re.search(rf"\b{word}\b", user_message, re.IGNORECASE):
                return "severe"
        
        for word in mild_discomfort:
            if re.search(rf"\b{word}\b", user_message, re.IGNORECASE):
                return "mild"
        
        return "neutral"

    def provide_practical_advice(self, emotion, user_message):
        """
        Provides quick, useful advice based on distress level.
        """
        if emotion == "mild":
            return random.choice([
                "Try sipping ginger tea 🍵, resting, and eating small meals throughout the day.",
                "Drinking plenty of water and having light snacks can help with nausea. Stay hydrated! 💧",
                "Lying on your left side and doing gentle stretches might ease discomfort. 🛌"
            ])
        
        if emotion == "severe":
            return random.choice([
                "If you're feeling extremely unwell, consider calling your doctor. Your health matters! 📞",
                "Deep breathing and meditation might help with stress, but don’t hesitate to reach out for support. 💙",
                "Severe pain or unusual symptoms? It's always best to check with a medical professional. 💊"
            ])
        
        return ""

    def send_message(self, user_message):
        """
        Sends a message to the Gemini API and retrieves a more action-oriented response.
        """
        emotion = self.detect_emotion(user_message)

        self.history.append({"role": "user", "content": user_message})

        try:
            contents = [entry["content"] for entry in self.history]

            response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=contents,
                config=types.GenerateContentConfig(
                    max_output_tokens=300,  
                    temperature=0.3  
                )
            )

            bot_message = response.text.strip()
            bot_message = self.truncate_response(bot_message)

            # Add **practical advice** FIRST, then empathy
            advice = self.provide_practical_advice(emotion, user_message)
            if advice:
                bot_message = f"{advice} {bot_message}"

            # Add a **soft emoji** for warmth
            emoji = random.choice(["💕", "🤗", "🌟", "💪", "👶"])
            bot_message = f"{bot_message} {emoji}"

            self.history.append({"role": "assistant", "content": bot_message})
            return bot_message

        except Exception as e:
            logging.error(f"Error while connecting to the API: {e}")
            return "Connection error. Try later. 💜"