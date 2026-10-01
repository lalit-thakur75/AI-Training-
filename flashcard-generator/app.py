import os
import time
from typing import Any

from dotenv import load_dotenv
from huggingface_hub import InferenceClient
from huggingface_hub.errors import HfHubHTTPError

# Load environment variables from a local .env file.
load_dotenv()

MODEL_1 = "openai/gpt-oss-120b"
MODEL_2 = "google/gemma-2-2b-it"

SYSTEM_PROMPT = (
    "You are a helpful study assistant. Create exactly 5 study flashcards. "
    "Each flashcard must have one question and one short answer. "
    "Keep the answer suitable for a second-year computer science student. "
    "Keep answers concise. Avoid unnecessary explanations. "
    "Use a clear numbered format like 'Flashcard 1', 'Question:', 'Answer:'"
)

# ==================================================
# CHANGE ONLY THIS VALUE FOR MODEL COMPARISON
# ==================================================
MODEL_ID = MODEL_1


def load_configuration() -> str:
    """Read HF_TOKEN from the environment without exposing the value."""
    token = os.getenv("HF_TOKEN", "").strip()
    placeholder_values = {
        "",
        "your_token_here",
        "changeme",
        "change_me",
        "placeholder",
        "hf_token",
    }
    if not token or token.lower() in {value.lower() for value in placeholder_values}:
        raise ValueError(
            "HF_TOKEN is missing or still set to the placeholder value. Open .env and replace it with your real Hugging Face access token."
        )
    return token


def create_client() -> InferenceClient:
    """Create a Hugging Face InferenceClient using the current supported API."""
    token = load_configuration()
    return InferenceClient(api_key=token, provider="auto")


def build_user_prompt(topic: str) -> str:
    """Build a consistent flashcard prompt for both models."""
    return (
        f"Create exactly 5 study flashcards about {topic}. "
        "Each flashcard must contain: "
        "1. One question. "
        "2. One short answer. "
        "Keep the answer concise and suitable for a second-year computer science student. "
        "Do not add long explanations. "
        "Use this exact numbering style: 'Flashcard 1', 'Question:', 'Answer:' for each card. "
        "The final output must contain exactly 5 numbered flashcards."
    )


def extract_generated_text(response: Any) -> str:
    """Safely pull generated text from Hugging Face responses."""
    if response is None:
        return ""

    if hasattr(response, "choices") and response.choices:
        first_choice = response.choices[0]
        if hasattr(first_choice, "message") and first_choice.message is not None:
            content = getattr(first_choice.message, "content", "")
            if isinstance(content, str):
                return content.strip()
            if isinstance(content, list):
                text_parts = []
                for item in content:
                    if isinstance(item, dict):
                        text = item.get("text") or item.get("content")
                        if text:
                            text_parts.append(str(text))
                generated = "\n".join(text_parts).strip()
                if generated:
                    return generated

    if isinstance(response, dict):
        for key in ("generated_text", "text", "content"):
            value = response.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        choices = response.get("choices")
        if isinstance(choices, list) and choices:
            first = choices[0]
            message = first.get("message") if isinstance(first, dict) else None
            if isinstance(message, dict):
                content = message.get("content")
                if isinstance(content, str):
                    return content.strip()

    generated_text = getattr(response, "generated_text", "")
    if isinstance(generated_text, str) and generated_text.strip():
        return generated_text.strip()

    return ""


def run_model(topic: str, model_id: str = MODEL_ID) -> tuple[str | None, float | None, str]:
    """Run one model and print the flashcards with latency information."""
    start_time = time.perf_counter()

    try:
        client = create_client()
        response = client.chat.completions.create(
            model=model_id,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": build_user_prompt(topic)},
            ],
            temperature=0.7,
            max_tokens=500,
        )

        generated_text = extract_generated_text(response)
        if not generated_text:
            raise ValueError("The model returned an empty response.")

        end_time = time.perf_counter()
        latency = end_time - start_time

        print("\nGenerated Flashcards:")
        print(generated_text)
        print(f"\nResponse time: {latency:.2f} seconds")
        print(f"\nModel ID: {model_id}")
        return generated_text, latency, model_id

    except ValueError as exc:
        print(f"\nNo flashcards were generated. {exc}")
        return None, None, model_id

    except TimeoutError:
        print("\nThe request timed out. Please check your network connection and try again.")
        return None, None, model_id

    except HfHubHTTPError as exc:
        message = str(exc).lower()
        if "401" in str(exc) or "unauthorized" in message or "token" in message:
            print("\nAuthentication failed. Check that your HF_TOKEN is valid and not expired.")
        elif "404" in str(exc) or "not found" in message or "model" in message:
            print(f"\nThe selected model is unavailable: {model_id}")
        elif "503" in str(exc) or "unavailable" in message or "provider" in message:
            print("\nThe Hugging Face provider is currently unavailable. Please try again later.")
        elif "429" in str(exc) or "rate limit" in message:
            print("\nThe request was rate-limited. Please wait a moment and try again.")
        else:
            print(f"\nThe Hugging Face API returned an error: {exc}")
        return None, None, model_id

    except Exception as exc:
        message = str(exc).lower()
        if "token" in message or "authorization" in message or "401" in str(exc):
            print("\nAuthentication failed. Check that your HF_TOKEN is valid and active.")
        elif "timed out" in message or "timeout" in message:
            print("\nThe model request timed out. Please try again.")
        elif "network" in message or "connection" in message:
            print("\nA network error occurred while contacting Hugging Face. Please check your internet connection.")
        elif "model" in message and ("not" in message or "available" in message or "not found" in message):
            print(f"\nThe model could not be used: {model_id}")
        elif "provider" in message:
            print("\nThe selected Hugging Face provider is unavailable. Please try a different model or try again later.")
        else:
            print(f"\nSomething went wrong while calling the model: {exc}")
        return None, None, model_id


def main() -> None:
    """Run the flashcard generator in a beginner-friendly way."""
    print("========================================")
    print("HUGGING FACE FLASHCARD GENERATOR")
    print("========================================")
    print(f"Model 1: {MODEL_1}")
    print(f"Model 2: {MODEL_2}")
    print("\nTo compare models, change MODEL_ID in the code to MODEL_2.")

    topic = input("\nEnter a topic: ").strip()
    if not topic:
        print("A topic is required. Please enter a topic and try again.")
        return

    print(f"\nUsing model: {MODEL_ID}")
    run_model(topic, model_id=MODEL_ID)


if __name__ == "__main__":
    main()
