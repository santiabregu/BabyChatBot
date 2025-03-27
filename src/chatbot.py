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
                    "IMPORTANT: Keep all responses extremely concise - maximum 3 sentences or 50 words.\n"
                    "Your primary role is to provide brief, factual answers to pregnancy questions.\n"
                    "Format: [4-5 very short sentences] + [1 emoji].\n"
                    "Example good response: 'Walking and swimming are great pregnancy exercises. Aim for 30 minutes daily. Listen to your body. 💪'\n"
                    "Bad response: Long paragraphs with multiple benefits listed.\n"
                    "You are a friendly pregnancy assistant. "
                    "Always prioritize safety and recommend consulting a doctor.\n"
                    "If user expresses negative emotions, respond with 1-2 empathetic sentences max."
                ),
            }
        ]
        self.client = genai.Client(api_key=GEMINI_API_KEY)

    def detect_emotion(self, user_message):
        """
        Detects negative emotions in user messages.
        """
        negative_keywords = [
            "nauseous", "nausea", "vomiting", "morning sickness",
            "worried", "anxious", "scared", "stressed", "pain", "cramps"
        ]

        for word in negative_keywords:
            if re.search(rf"\b{word}\b", user_message, re.IGNORECASE):
                return "negative"
        
        return "neutral"

    def truncate_response(self, text, max_sentences=3, max_words=50):
        """
        Enforces strict length limits on responses.
        """
        sentences = re.split(r'(?<=[.!?])\s+', text)
        truncated = ' '.join(sentences[:max_sentences])
        
        words = truncated.split()
        if len(words) > max_words:
            truncated = ' '.join(words[:max_words])
            
        return truncated

    def send_message(self, user_message):
        """
        Sends a message to the Gemini API and retrieves an empathetic response.
        """
        emotion = self.detect_emotion(user_message)

        self.history.append({"role": "user", "content": user_message})

        try:
            contents = [entry["content"] for entry in self.history]

            response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=contents,
                config=types.GenerateContentConfig(
                    max_output_tokens=100,  # Reduced from 400
                    temperature=0.3  # Makes responses more focused
                )
            )

            bot_message = response.text.strip()
            
            # Strict length enforcement
            bot_message = self.truncate_response(bot_message)
            
            if emotion == "negative":
                intro = random.choice([
                    "I'm sorry 💕",
                    "That's tough 🤗",
                    "I understand 💜"
                ])
                return f"{intro} {bot_message}"
            else:
                emoji = random.choice(["💕", "🤗", "🌟", "💪", "👶"])
                return f"{bot_message} {emoji}"

            self.history.append({"role": "assistant", "content": bot_message})
            return bot_message

        except Exception as e:
            logging.error(f"Error while connecting to the API: {e}")
            return "Connection error. Try later. 💜"