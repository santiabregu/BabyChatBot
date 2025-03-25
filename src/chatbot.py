from google import genai
from src.config import GEMINI_API_KEY  # Ensure GEMINI_API_KEY is loaded from your config
import logging

# Configure logging
logging.basicConfig(level=logging.ERROR)

class PregnancyChatbot:
    def __init__(self):
        self.history = [
            {
                "role": "system",
                "content": (
                    "You are a friendly, caring pregnancy assistant. "
                    "Your tone is warm, supportive, and encouraging. "
                    "You provide advice and emotional support to pregnant individuals. "
                    "Always focus on pregnancy-related topics and tailor your responses to the user's situation. "
                    "If the user expresses fear or anxiety, provide calming advice and relate it to pregnancy when possible."
                ),
            }
        ]
        # Initialize the Google GenAI client
        self.client = genai.Client(api_key=GEMINI_API_KEY)

    def send_message(self, user_message):
        """
        Sends a message to the Gemini API using the google-genai library and retrieves a response.
        """
        # Add the user's message to the conversation history
        self.history.append({"role": "user", "content": user_message})

        try:
            # Prepare the conversation history for the API call
            contents = [entry["content"] for entry in self.history]

            # Make the API call using the google-genai library
            response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=contents  # Pass the full conversation history
            )

            # Extract the response text
            bot_message = response.text
            self.history.append({"role": "assistant", "content": bot_message})
            return bot_message
        except Exception as e:
            logging.error(f"Error while connecting to the API: {e}")
            return f"An error occurred while connecting to the API: {e}"