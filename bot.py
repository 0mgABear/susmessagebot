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
        logging.info(f"BAN action taken on user {user_id}")
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
            await context.bot.ban_chat_member(chat_id=chat_id, user_id=user_id)
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"⚠️ A suspicious message was detected and removed. The user has been banned. If this was a mistake, please contact an admin."
            )
        except Exception as e:
            logging.error(f"Error: {e}")

def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_webhook(
        listen="0.0.0.0",
        port=80,
        webhook_url=f"https://susmessagebot.commonertech.dev"
    )

if __name__ == "__main__":
    main()