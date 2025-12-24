import json
import time
from typing import Dict, Any
from openai import OpenAI
from config import settings

# Initialize client
_client = OpenAI(api_key=settings.OPENAI_API_KEY)

class LLMError(Exception):
    """Raised when LLM generation fails"""

def generate_json(prompt: str, max_retries: int = 3) -> Dict[str, Any]:
    """
    Generic function to send a prompt to the LLM and expect a JSON response.
    This matches the call signature in your Burr workflow.
    """
    last_error = None

    for attempt in range(1, max_retries + 1):
        try:
            print(f"  ⏳ LLM generation attempt {attempt}...")

            # correct OpenAI v1.x syntax
            response = _client.chat.completions.create( 
                model=settings.LLM_MODEL, # Ensure model is gpt-3.5-turbo-1106 or newer for json_object
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a helpful assistant. Output valid JSON only."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                temperature=0.2,
                # ✅ CRITICAL: Forces the LLM to output valid JSON
                response_format={ "type": "json_object" } 
            )

            content = response.choices[0].message.content
            print("  ✓ LLM generation successful")
            
            return _safe_parse_json(content)

        except Exception as e:
            print(f"  ⚠️ Attempt {attempt} failed: {e}")
            last_error = e
            time.sleep(2 * attempt) # Exponential backoff

    raise LLMError(f"LLM generation failed after {max_retries} attempts: {last_error}")


def _safe_parse_json(text: str) -> Dict[str, Any]:
    """
    Parses JSON string. Handles cases where LLM wraps output in markdown code blocks.
    """
    try:
        cleaned_text = text.strip()
        # Remove markdown code blocks if present (e.g. ```json ... ```)
        if cleaned_text.startswith("```"):
            cleaned_text = cleaned_text.strip("`").replace("json", "").strip()
        
        return json.loads(cleaned_text)
    except json.JSONDecodeError:
        raise LLMError(f"Invalid JSON returned by LLM:\n{text}")