import logging
import groq
from config import GROQ_API_KEY

logger = logging.getLogger(__name__)

def generate_content(topic: str, model: str = "llama3-8b-8192") -> str:
    """
    Generates content on a given topic using the Groq API.
    Handles specific API errors.
    """
    if not GROQ_API_KEY:
        logger.error("GROQ_API_KEY is not configured.")
        return "Error: The AI service is not configured. Please contact the admin."

    client = groq.Groq(api_key=GROQ_API_KEY)

    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a creative content generator for Telegram channels. "
                               "Generate a compelling and engaging post based on the user's topic. "
                               "The post should be well-structured, informative, and ready to be published."
                },
                {
                    "role": "user",
                    "content": f"Topic: {topic}",
                }
            ],
            model=model,
        )
        return chat_completion.choices[0].message.content
    except groq.APIStatusError as e:
        status = e.status_code
        if status == 401:
            logger.error("Groq API Error: Invalid API Key.")
            return "Error: AI service authentication failed. Please contact the admin."
        elif status == 429:
            logger.warning("Groq API Error: Rate limit exceeded.")
            return "Error: AI service is currently busy. Please try again in a few moments."
        elif status >= 500:
            logger.error(f"Groq API Error: Server error (status {status}).")
            return "Error: The AI service is experiencing technical difficulties. Please try again later."
        else:
            logger.error(f"Groq API Error: {e}")
            return f"Error: An unexpected error occurred with the AI service (status {status})."
    except Exception as e:
        logger.error(f"An unexpected error occurred while generating content: {e}")
        return "Error: An unexpected error occurred. Please try again."
