"""Telegram bot — proxies messages to agent-service and exposes /send for the scheduler."""
from __future__ import annotations

import asyncio
import logging
import os

import httpx
from aiohttp import web
from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters

AGENT_URL = os.environ["AGENT_URL"]        # e.g. http://agent-service:8092
BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = int(os.environ["TELEGRAM_CHAT_ID"])
SEND_PORT = int(os.environ.get("TELEGRAM_SEND_PORT", "8094"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
log = logging.getLogger("telegram-bot")

_tg_app: Application | None = None


async def _call_agent(prompt: str) -> str:
    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(
            f"{AGENT_URL}/chat",
            json={"message": prompt, "history": []},
        )
        resp.raise_for_status()
        return resp.text


async def on_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    assert update.message and update.message.text
    prompt = update.message.text
    log.info("message.received from=%s", update.effective_user and update.effective_user.id)
    try:
        reply = await _call_agent(prompt)
    except Exception as exc:
        reply = f"[agent error: {exc}]"
        log.error("agent.error %s", exc)
    await update.message.reply_text(reply)
    log.info("message.replied chars=%d", len(reply))


async def _http_send(request: web.Request) -> web.Response:
    """Called by the scheduler to push a skill result to the configured chat."""
    data = await request.json()
    text = (data.get("text") or "").strip()
    if not text:
        return web.json_response({"ok": False, "error": "empty text"}, status=400)
    if _tg_app is None:
        return web.json_response({"ok": False, "error": "bot not ready"}, status=503)
    await _tg_app.bot.send_message(chat_id=CHAT_ID, text=text)
    log.info("send.ok chars=%d", len(text))
    return web.json_response({"ok": True})


async def _start_http_server() -> None:
    http_app = web.Application()
    http_app.router.add_post("/send", _http_send)
    runner = web.AppRunner(http_app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", SEND_PORT)
    await site.start()
    log.info("http.listen port=%d", SEND_PORT)


async def main() -> None:
    global _tg_app

    tg_app = Application.builder().token(BOT_TOKEN).build()
    tg_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_message))
    _tg_app = tg_app

    await _start_http_server()

    async with tg_app:
        await tg_app.initialize()
        await tg_app.start()
        await tg_app.updater.start_polling(allowed_updates=Update.ALL_TYPES)
        log.info("bot.polling_started")
        try:
            await asyncio.Event().wait()
        finally:
            await tg_app.updater.stop()
            await tg_app.stop()


if __name__ == "__main__":
    asyncio.run(main())
