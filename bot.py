from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from telegram.constants import ChatMemberStatus
from config import TELEGRAM_BOT_TOKEN
from moderator import classify_message

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

    if result == "BAN":
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
            await context.bot.send_message(chat_id=chat_id, text="⚠️ Suspicious message detected and removed.")
        except Exception as e:
            pass

def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()