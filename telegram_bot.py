"""
Simple Telegram bot for local/demo integration with the Payment API.

This script is intended for development/demo use only — it's not production
ready (no webhook support, no robust error handling, no persistence).

Usage:
  - Put `TELEGRAM_BOT_TOKEN` in your `.env` or environment.
  - Ensure `PAYMENT_API_BASE_URL` points to a running API instance.
  - Run: `python telegram_bot.py` (from the project venv).
"""
from __future__ import annotations

import asyncio
import logging
import os
import time
from typing import Any, Dict, List, Optional

import httpx
from dotenv import load_dotenv


# Basic logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


# Load .env if present
load_dotenv()

# Configuration (module-level defaults, do not exit on import)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
PAYMENT_API_BASE_URL = os.getenv("PAYMENT_API_BASE_URL", "http://127.0.0.1:8000")
POLL_INTERVAL_SECONDS = int(os.getenv("POLL_INTERVAL_SECONDS", "2"))


def build_telegram_api_url(token: str, method: str) -> str:
    """Build a full Telegram API method URL for a bot token.

    Example: https://api.telegram.org/bot<TOKEN>/getUpdates
    """
    return f"https://api.telegram.org/bot{token}/{method}"


async def fetch_updates(token: str, offset: Optional[int], client: httpx.AsyncClient) -> List[Dict[str, Any]]:
    """Fetch updates from Telegram using getUpdates.

    Returns list of update dicts.
    """
    url = build_telegram_api_url(token, "getUpdates")
    params: Dict[str, Any] = {"timeout": 30, "limit": 100}
    if offset is not None:
        params["offset"] = offset
    try:
        resp = await client.get(url, params=params, timeout=35.0)
        resp.raise_for_status()
        data = resp.json()
        return data.get("result", [])
    except Exception as exc:
        logger.error("Error fetching updates: %s", exc)
        return []


async def send_message(token: str, chat_id: int | str, text: str, client: httpx.AsyncClient) -> None:
    """Send a text message to a chat using sendMessage."""
    url = build_telegram_api_url(token, "sendMessage")
    payload = {"chat_id": chat_id, "text": text}
    try:
        resp = await client.post(url, json=payload, timeout=15.0)
        resp.raise_for_status()
    except Exception as exc:
        logger.error("Failed to send message to %s: %s", chat_id, exc)


async def call_health(api_base_url: str, client: httpx.AsyncClient) -> Optional[Dict[str, Any]]:
    """Call the API health endpoint and return JSON or None on failure."""
    url = f"{api_base_url.rstrip('/')}/health"
    try:
        resp = await client.get(url, timeout=10.0)
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        logger.warning("Health check failed: %s", exc)
        return None


async def handle_update(update: Dict[str, Any], token: str, api_base_url: str, client: httpx.AsyncClient) -> None:
    """Handle a single Telegram update (supports simple commands).

    Supported commands:
    - /start: welcome message
    - /ping: call API health and reply with status
    """
    # Telegram may include message or edited_message
    message = update.get("message") or update.get("edited_message")
    if not message:
        return

    chat = message.get("chat", {})
    chat_id = chat.get("id")
    text = message.get("text", "")
    logger.info("Received message from %s: %s", chat_id, text)

    if not text or not chat_id:
        return

    # Simple command handling
    if text.strip().startswith("/start"):
        await send_message(token, chat_id, "مرحبًا — هذا بوت تجريبي لبوابة الدفع (Payment API).", client)
        return

    if text.strip().startswith("/ping"):
        health = await call_health(api_base_url, client)
        if health and health.get("status") == "ok":
            await send_message(token, chat_id, "API status: ok", client)
        else:
            await send_message(token, chat_id, "API غير متاح الآن أو فشل فحص الصحة.", client)
        return


async def run_bot() -> None:
    """Main loop: long-poll Telegram getUpdates and dispatch handlers.

    Note: this is a development/demo loop (not production). For production
    use webhooks or a more robust worker model.
    """
    token = TELEGRAM_BOT_TOKEN or os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        # Required only when running as a script
        logger.error("TELEGRAM_BOT_TOKEN is not set. Please set it in .env or environment and rerun.")
        return

    api_base = PAYMENT_API_BASE_URL
    offset: Optional[int] = None

    async with httpx.AsyncClient() as client:
        logger.info("Telegram bot started (polling every %s seconds).", POLL_INTERVAL_SECONDS)
        while True:
            try:
                updates = await fetch_updates(token, offset, client)
                if updates:
                    for upd in updates:
                        try:
                            await handle_update(upd, token, api_base, client)
                        except Exception as exc:
                            logger.exception("Error handling update: %s", exc)
                        offset = upd.get("update_id", 0) + 1
                else:
                    # no updates, sleep briefly to avoid tight loop
                    await asyncio.sleep(POLL_INTERVAL_SECONDS)
            except Exception as exc:
                logger.exception("Unexpected error in polling loop: %s", exc)
                await asyncio.sleep(max(1, POLL_INTERVAL_SECONDS))


if __name__ == "__main__":
    # Run the bot using asyncio — this check prevents execution on import.
    try:
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
