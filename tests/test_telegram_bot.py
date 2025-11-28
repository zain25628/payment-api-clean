import json

import pytest
import httpx

from telegram_bot import (
    build_telegram_api_url,
    call_health,
    handle_update,
)


def test_build_telegram_api_url_examples():
    assert build_telegram_api_url("TOKEN123", "getMe") == "https://api.telegram.org/botTOKEN123/getMe"
    assert build_telegram_api_url("TOKEN123", "sendMessage") == "https://api.telegram.org/botTOKEN123/sendMessage"


def test_call_health_success():
    async def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/health"):
            return httpx.Response(200, json={"status": "ok"})
        return httpx.Response(404)

    async def _run():
        transport = httpx.MockTransport(handler)
        async with httpx.AsyncClient(transport=transport) as client:
            result = await call_health("http://example.local", client)
            assert result is not None
            assert result.get("status") == "ok"

    import asyncio

    asyncio.run(_run())


def test_call_health_failure():
    async def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/health"):
            return httpx.Response(500)
        return httpx.Response(404)

    async def _run():
        transport = httpx.MockTransport(handler)
        async with httpx.AsyncClient(transport=transport) as client:
            result = await call_health("http://example.local", client)
            assert result is None

    import asyncio

    asyncio.run(_run())


def test_handle_update_start_sends_message():
    recorded: dict = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        # capture POST sendMessage payload
        if request.method == "POST" and request.url.path.endswith("/sendMessage"):
            body = request.content
            try:
                payload = json.loads(body.decode()) if body else {}
            except Exception:
                payload = {}
            recorded["last_post"] = {"url": str(request.url), "json": payload}
            return httpx.Response(200, json={"ok": True})
        return httpx.Response(200, json={})

    async def _run():
        transport = httpx.MockTransport(handler)
        async with httpx.AsyncClient(transport=transport) as client:
            update = {
                "update_id": 1,
                "message": {
                    "message_id": 10,
                    "chat": {"id": 12345},
                    "text": "/start",
                },
            }
            await handle_update(update, token="TOKEN123", api_base_url="http://example.local", client=client)

    import asyncio

    asyncio.run(_run())

    assert "last_post" in recorded
    post = recorded["last_post"]
    assert "chat_id" in post["json"]
    assert post["json"]["chat_id"] == 12345
    assert "بوابة" in post["json"].get("text", "") or "Welcome" in post["json"].get("text", "")


def test_handle_update_ping_reports_health():
    recorded: dict = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        # API health check
        if request.url.path.endswith("/health"):
            return httpx.Response(200, json={"status": "ok"})

        # capture Telegram sendMessage
        if request.method == "POST" and request.url.path.endswith("/sendMessage"):
            body = request.content
            try:
                payload = json.loads(body.decode()) if body else {}
            except Exception:
                payload = {}
            recorded["last_post"] = payload
            return httpx.Response(200, json={"ok": True})

        return httpx.Response(404)

    async def _run():
        transport = httpx.MockTransport(handler)
        async with httpx.AsyncClient(transport=transport) as client:
            update = {
                "update_id": 2,
                "message": {
                    "message_id": 11,
                    "chat": {"id": 54321},
                    "text": "/ping",
                },
            }
            await handle_update(update, token="TOKEN123", api_base_url="http://example.local", client=client)

    import asyncio

    asyncio.run(_run())

    assert "last_post" in recorded
    payload = recorded["last_post"]
    assert payload.get("chat_id") == 54321
    # message should indicate API status ok (as per bot implementation)
    assert "ok" in payload.get("text", "").lower()
