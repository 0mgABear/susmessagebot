from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from telegram.constants import ChatMemberStatus
from config import TELEGRAM_BOT_TOKEN, WEBHOOK_URL, USE_POLLING
from moderator import classify_message
from github_sync import sync_example_to_github
from prometheus_client import Counter, start_http_server

import logging
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# Prometheus metrics for Grafana
MESSAGES_CLASSIFIED = Counter('messages_classified_total', 'Messages classified by the bot', ['result'])
BANS_CONFIRMED = Counter('bans_confirmed_total', 'Admin-confirmed correct bans')
FALSE_POSITIVES = Counter('false_positives_total', 'Admin-confirmed false positives')


banned_messages = {}

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handles every incoming message.
    Classifies it and bans the user if it is a scam/spam.

    Args:
        update: The incoming Telegram update
        context: The bot context
    """
    if not update.message or not update.message.text:
        return

    chat_id = update.message.chat_id
    user_id = update.message.from_user.id
    message_id = update.message.message_id
    text = update.message.text

    chat_member = await context.bot.get_chat_member(chat_id, user_id)
    if chat_member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
        return

    result = classify_message(text)
    MESSAGES_CLASSIFIED.labels(result=result).inc()

    if result == "BAN":
        logging.info(f"BAN action taken on user {user_id}")
        banned_messages[message_id] = {"user_id": user_id, "text": text}

        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
            await context.bot.ban_chat_member(chat_id=chat_id, user_id=user_id)
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("✅ Correct Ban", callback_data=f"correct|{message_id}|{chat_id}"),
                    InlineKeyboardButton("❌ Wrong Ban", callback_data=f"false|{message_id}|{chat_id}|{user_id}")
                ]
            ])
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"⚠️ Suspicious message detected and removed. Admin review required:",
                reply_markup=keyboard
            )
        except Exception as e:
            logging.error(f"Error: {e}")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    chat_id = query.message.chat_id

    # check if clicker is admin
    chat_member = await context.bot.get_chat_member(chat_id, user_id)
    if chat_member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
        await query.answer("Only admins can do this.")
        return

    data = query.data.split("|")
    action = data[0]
    message_id = int(data[1])
    
    banned_info = banned_messages.get(message_id)
    if not banned_info:
        await query.answer("Action expired.")
        return

    if action == "correct":
        from vector_store import add_example
        add_example(banned_info["text"], "BAN")
        sync_example_to_github(banned_info["text"], "BAN")
        BANS_CONFIRMED.inc()
        await query.edit_message_text("✅ Ban confirmed. Added to training examples.")
        
    elif action == "false":
        banned_user_id = int(data[3])
        from vector_store import add_example
        add_example(banned_info["text"], "SAFE")
        sync_example_to_github(banned_info["text"], "SAFE")
        FALSE_POSITIVES.inc()
        await context.bot.unban_chat_member(chat_id=chat_id, user_id=banned_user_id)
        await query.edit_message_text("❌ False positive confirmed. User unbanned and added to examples.")

    del banned_messages[message_id]
    await query.answer()

def main():
    if not TELEGRAM_BOT_TOKEN:
        print("TELEGRAM_BOT_TOKEN is not set. Exiting.")
        return
    start_http_server(8000)  # Prometheus metrics endpoint on port 8000
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(handle_callback))
    if USE_POLLING:
        logging.info("Starting bot in polling mode (local development)")
        app.run_polling(drop_pending_updates=True)
    else:
        logging.info("Starting bot in webhook mode")
        app.run_webhook(
            listen="0.0.0.0",
            port=80,
            webhook_url=WEBHOOK_URL
        )

if __name__ == "__main__":
    main()