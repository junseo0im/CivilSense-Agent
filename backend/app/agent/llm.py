import json
import logging
from typing import Any

import httpx

from app.config import UPSTAGE_API_KEY, UPSTAGE_BASE_URL, UPSTAGE_CHAT_MODEL

logger = logging.getLogger(__name__)

CHAT_URL = f"{UPSTAGE_BASE_URL.rstrip('/')}/chat/completions"


async def chat(
    user_content: str,
    system_content: str | None = None,
    temperature: float = 0.3,
) -> str:
    if not UPSTAGE_API_KEY:
        raise ValueError(
            "UPSTAGE_API_KEY is not set. Add UPSTAGE_API_KEY=your_key to .env (project root or backend/)."
        )
    messages: list[dict[str, str]] = []
    if system_content:
        messages.append({"role": "system", "content": system_content})
    messages.append({"role": "user", "content": user_content})

    payload: dict[str, Any] = {
        "model": UPSTAGE_CHAT_MODEL,
        "messages": messages,
        "temperature": temperature,
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            resp = await client.post(
                CHAT_URL,
                headers={
                    "Authorization": f"Bearer {UPSTAGE_API_KEY}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            choice = data.get("choices", [{}])[0]
            msg = choice.get("message", {})
            return (msg.get("content") or "").strip()
        except httpx.HTTPStatusError as e:
            logger.error("Upstage API HTTP error: %s %s", e.response.status_code, e.response.text)
            raise
        except Exception as e:
            logger.error("Upstage API error: %s", e)
            raise


def parse_json_from_text(text: str) -> dict[str, Any] | None:
    text = text.strip()
    for start in ("```json", "```"):
        if start in text:
            try:
                part = text.split(start, 1)[1].split("```", 1)[0].strip()
                return json.loads(part)
            except (IndexError, json.JSONDecodeError):
                pass
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    import re
    m = re.search(r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group())
        except json.JSONDecodeError:
            pass
    return None
