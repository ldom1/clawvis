"""Telegram bot — routes commands through intent router, proxies to agent-service."""
from __future__ import annotations

import asyncio
import logging

from aiohttp import web
from pydantic import ValidationError
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from core.bridge import AgentError, call_agent
from core.config import get_settings
from core.formatter import format_reply
from core.models import OutcomingMessage, incoming_from_update
from core.router import enrich

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
log = logging.getLogger("telegram-bot")

_tg_app: Application | None = None

_HELP_TEXT = (
    "Here's what I can do:\n\n"
    "/tasks <action> — manage tasks (e.g. /tasks create Fix login bug)\n"
    "/projects <action> — manage projects (e.g. /projects list)\n"
    "/status — check agent provider and readiness\n"
    "/ping — check I'm alive\n"
    "/help — show this message\n\n"
    "Or just send me a message and I'll do my best."
)

_UNREACHABLE_MSG = "I couldn't reach the agent right now. Try again in a moment."


async def _cmd_ping(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message:
        await update.message.reply_text("I'm here.")


async def _cmd_help(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message:
        await update.message.reply_text(_HELP_TEXT)


async def _cmd_routed(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None or not update.message.text:
        return
    command = update.message.text.split()[0].lstrip("/").split("@")[0].lower()
    args = " ".join(context.args) if context.args else ""
    prompt = enrich(command, args) or update.message.text
    settings = get_settings()
    try:
        raw = await call_agent(settings, prompt)
    except AgentError:
        log.error("agent.error command=%s", command)
        await update.message.reply_text(_UNREACHABLE_MSG)
        return
    await update.message.reply_text(format_reply(raw))
    log.info("command.replied command=%s chars=%d", command, len(raw))


async def on_message(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    incoming = incoming_from_update(update)
    if incoming is None:
        return
    log.info("message.received from=%s", incoming.user_id)
    settings = get_settings()
    try:
        raw = await call_agent(settings, incoming.text)
    except AgentError:
        log.error("agent.error freeform")
        if update.message:
            await update.message.reply_text(_UNREACHABLE_MSG)
        return
    if update.message:
        await update.message.reply_text(format_reply(raw))
        log.info("message.replied chars=%d", len(raw))


async def _http_send(request: web.Request) -> web.Response:
    """Called by the scheduler to push a skill result to the configured chat."""
    settings = get_settings()
    try:
        payload = OutcomingMessage.model_validate(await request.json())
    except (ValidationError, ValueError):
        return web.json_response({"ok": False, "error": "invalid payload"}, status=400)
    text = payload.text.strip()
    if not text:
        return web.json_response({"ok": False, "error": "empty text"}, status=400)
    if settings.stub_mode:
        log.info("send.stub chars=%d (set TELEGRAM_BOT_TOKEN for real delivery)", len(text))
        return web.json_response({"ok": True, "stub": True})
    if _tg_app is None:
        return web.json_response({"ok": False, "error": "bot not ready"}, status=503)
    await _tg_app.bot.send_message(chat_id=settings.chat_id, text=text)
    log.info("send.ok chars=%d", len(text))
    return web.json_response({"ok": True})


async def _start_http_server() -> None:
    settings = get_settings()
    http_app = web.Application()
    http_app.router.add_post("/send", _http_send)
    runner = web.AppRunner(http_app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", settings.send_port)
    await site.start()
    log.info("http.listen port=%d", settings.send_port)


async def main() -> None:
    global _tg_app
    settings = get_settings()

    await _start_http_server()

    if settings.stub_mode:
        log.warning(
            "telegram.stub_mode TELEGRAM_BOT_TOKEN unset — /send works; polling disabled",
        )
        await asyncio.Event().wait()
        return

    tg_app = Application.builder().token(settings.bot_token).build()
    tg_app.add_handler(CommandHandler("ping", _cmd_ping))
    tg_app.add_handler(CommandHandler("help", _cmd_help))
    tg_app.add_handler(CommandHandler("tasks", _cmd_routed))
    tg_app.add_handler(CommandHandler("projects", _cmd_routed))
    tg_app.add_handler(CommandHandler("status", _cmd_routed))
    tg_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_message))
    _tg_app = tg_app

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
