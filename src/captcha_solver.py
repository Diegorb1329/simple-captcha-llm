"""Captcha solving using LLM APIs (OpenAI or Anthropic)."""

import base64
import os
from config import CAPTCHA_PROMPTS, PROMPT_NAMES

_prompt_index = 0


def _encode_base64(image_bytes: bytes) -> str:
    return base64.b64encode(image_bytes).decode("utf-8")


def _solve_openai(image_bytes: bytes, prompt: str) -> str:
    from openai import OpenAI
    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-5.1-2025-11-13",
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{_encode_base64(image_bytes)}"}}
            ]
        }],
        max_completion_tokens=50
    )
    return response.choices[0].message.content.strip()


def _solve_anthropic(image_bytes: bytes, prompt: str) -> str:
    import anthropic
    client = anthropic.Anthropic()
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=50,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": _encode_base64(image_bytes)}},
                {"type": "text", "text": prompt}
            ]
        }]
    )
    return response.content[0].text.strip()


def _is_valid_response(response: str) -> bool:
    if not response or len(response) > 15:
        return False
    refusals = ["sorry", "can't", "cannot", "unable", "assist", "help"]
    if any(r in response.lower() for r in refusals):
        return False
    return bool(response.replace(" ", "").replace("-", "").replace("_", ""))


def solve_captcha(image_bytes: bytes) -> str:
    """Solve captcha with prompt rotation and fallback."""
    global _prompt_index
    
    if not os.environ.get("OPENAI_API_KEY") and not os.environ.get("ANTHROPIC_API_KEY"):
        raise ValueError("Set OPENAI_API_KEY or ANTHROPIC_API_KEY environment variable.")
    
    use_openai = bool(os.environ.get("OPENAI_API_KEY"))
    api_name = "OpenAI" if use_openai else "Claude"
    solver = _solve_openai if use_openai else _solve_anthropic
    
    for attempt in range(len(CAPTCHA_PROMPTS)):
        idx = (_prompt_index + attempt) % len(CAPTCHA_PROMPTS)
        print(f"  Using {api_name} with '{PROMPT_NAMES[idx]}' prompt...")
        
        try:
            response = solver(image_bytes, CAPTCHA_PROMPTS[idx])
            if _is_valid_response(response):
                _prompt_index = (idx + 1) % len(CAPTCHA_PROMPTS)
                return response
            print(f"    Invalid response: '{response[:30]}...', trying next...")
        except Exception as e:
            print(f"    Error: {e}, trying next...")
    
    _prompt_index = (_prompt_index + 1) % len(CAPTCHA_PROMPTS)
    raise ValueError("All prompts failed")
