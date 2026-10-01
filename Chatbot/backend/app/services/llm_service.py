from openai import OpenAI
from app.config import settings

# Initialize the OpenAI client pointing to Groq's API
client = OpenAI(
    api_key=settings.LLM_API_KEY,
    base_url="https://api.groq.com/openai/v1"
)

def generate_chat_response(messages: list) -> str:
    """
    Generates a response using the Groq API (Llama 3).
    """
    try:
        if not settings.LLM_API_KEY or settings.LLM_API_KEY == "your_api_key":
            return "Error: Groq API Key is missing or invalid. Please check your backend/.env file."

        response = client.chat.completions.create(
            model="llama3-8b-8192", # Using a fast default model on Groq
            messages=messages,
            temperature=0.7,
            max_tokens=1024
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error calling LLM API: {e}")
        return f"Error connecting to AI API: {str(e)}"
