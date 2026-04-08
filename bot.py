from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, MessageHandler, CallbackQueryHandler, filters, ContextTypes, CommandHandler
from telegram.constants import ChatMemberStatus
from config import TELEGRAM_BOT_TOKEN, WEBHOOK_URL, USE_POLLING
from moderator import classify_message
from github_sync import sync_example_to_github
from prometheus_client import Gauge, start_http_server
from http.server import HTTPServer, BaseHTTPRequestHandler
from stats import init_db, get_stat, increment_stat, decrement_stat, add_group, update_group_member_count, get_groups_count, get_total_members, get_all_group_ids
import asyncio
import threading

import logging
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# Prometheus metrics for Grafana 
MESSAGES_CLASSIFIED_SAFE = Gauge('messages_classified_safe_total', 'SAFE classifications')
MESSAGES_CLASSIFIED_BAN = Gauge('messages_classified_ban_total', 'BAN classifications')
BANS_CONFIRMED = Gauge('bans_confirmed_total', 'Admin-confirmed correct bans')
FALSE_POSITIVES = Gauge('false_positives_total', 'Admin-confirmed false positives')
FALSE_NEGATIVES = Gauge('false_negatives_total', 'Admin-reported false negatives')
# Other Generic Stats
GROUPS_COUNT = Gauge('groups_count_total', 'Number of groups bot is in')
MEMBERS_PROTECTED = Gauge('members_protected_total', 'Total members protected')

ACCURATE_CLASSIFICATIONS = Gauge('accurate_classifications_total', 'Accurately classified messages')

def init_metrics():
    """Load persisted values from SQLite into Prometheus gauges."""
    MESSAGES_CLASSIFIED_SAFE.set(get_stat('messages_safe'))
    MESSAGES_CLASSIFIED_BAN.set(get_stat('messages_ban'))
    BANS_CONFIRMED.set(get_stat('bans_confirmed'))
    FALSE_POSITIVES.set(get_stat('false_positives'))
    FALSE_NEGATIVES.set(get_stat('false_negatives'))
    GROUPS_COUNT.set(get_groups_count())
    MEMBERS_PROTECTED.set(get_total_members())
    ACCURATE_CLASSIFICATIONS.set(get_stat('accurate_classifications'))

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'OK')
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_HEAD(self):
        if self.path == '/health':
            self.send_response(200)
            self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        pass

def start_health_server():
    server = HTTPServer(('0.0.0.0', 8001), HealthHandler)
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()

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
    # Track new groups
    member_count = await context.bot.get_chat_member_count(chat_id)
    is_new = add_group(chat_id, member_count)
    if is_new:
        GROUPS_COUNT.set(get_groups_count())
        MEMBERS_PROTECTED.set(get_total_members())
    result = classify_message(text)

    if result == "BAN":
        logging.info(f"BAN action taken on user {user_id}")
        increment_stat('messages_ban')
        MESSAGES_CLASSIFIED_BAN.set(get_stat('messages_ban'))
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
                text=f"⚠️ Suspicious message detected and removed.\n\n"
                    f"👤 User: {update.message.from_user.full_name}"
                    f"{f' (@{update.message.from_user.username})' if update.message.from_user.username else ''}\n"
                    f"🆔 ID: {user_id}\n\n"
                    f"📝 Message:\n{text[:200]}{'...' if len(text) > 200 else ''}",
                reply_markup=keyboard
            )
        except Exception as e:
            logging.error(f"Error: {e}")
    else:
        increment_stat('messages_safe')
        MESSAGES_CLASSIFIED_SAFE.set(get_stat('messages_safe'))
        increment_stat('accurate_classifications')
        ACCURATE_CLASSIFICATIONS.set(get_stat('accurate_classifications'))

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
        increment_stat('bans_confirmed')
        BANS_CONFIRMED.set(get_stat('bans_confirmed'))
        increment_stat('accurate_classifications')
        ACCURATE_CLASSIFICATIONS.set(get_stat('accurate_classifications'))
        await query.edit_message_text("✅ Ban confirmed.")
        
    elif action == "false":
        banned_user_id = int(data[3])
        from vector_store import add_example
        add_example(banned_info["text"], "SAFE")
        sync_example_to_github(banned_info["text"], "SAFE")
        increment_stat('false_positives')
        FALSE_POSITIVES.set(get_stat('false_positives'))
        await context.bot.unban_chat_member(chat_id=chat_id, user_id=banned_user_id)
        await query.edit_message_text("❌ False positive confirmed.")

    del banned_messages[message_id]
    await query.answer()

reported_messages = {}

async def handle_report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handles /report command.
    Admins: immediately ban and add to training.
    Non-admins: send to admins for review via inline keyboard.
    """
    if not update.message:
        return

    chat_id = update.message.chat_id
    user_id = update.message.from_user.id

    # Check if it's a reply
    if not update.message.reply_to_message:
        await update.message.reply_text("Please reply to the scam message with /report.")
        return
    # Handle non-text messages
    if not update.message.reply_to_message.text:
        reported_user = update.message.reply_to_message.from_user
        reported_message_id = update.message.reply_to_message.message_id
        
        # Store minimal info for callback
        reported_messages[reported_message_id] = {
            "text": None,
            "user_id": reported_user.id,
            "chat_id": chat_id,
            "message_id": reported_message_id,
            "reported_by": update.message.from_user.username or str(user_id)
        }
        
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Ban", callback_data=f"report_confirm|{reported_message_id}|{chat_id}|{reported_user.id}"),
                InlineKeyboardButton("❌ Dismiss", callback_data=f"report_dismiss|{reported_message_id}|{chat_id}")
            ]
        ])
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"🚨 Non-text report by @{update.message.from_user.username or str(user_id)}\n\n"
                f"👤 Reported user: {reported_user.full_name}"
                f"{f' (@{reported_user.username})' if reported_user.username else ''}\n"
                f"🆔 ID: {reported_user.id}\n\n"
                f"⚠️ Admin review required.",
            reply_markup=keyboard
        )
        return

    reported_text = update.message.reply_to_message.text
    reported_user_id = update.message.reply_to_message.from_user.id
    reported_message_id = update.message.reply_to_message.message_id

    chat_member = await context.bot.get_chat_member(chat_id, user_id)
    is_admin = chat_member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]

    if is_admin:
        # Act immediately
        from vector_store import add_example
        add_example(reported_text, "BAN")
        sync_example_to_github(reported_text, "BAN")
        increment_stat('false_negatives')
        FALSE_NEGATIVES.set(get_stat('false_negatives'))
        decrement_stat('accurate_classifications')
        ACCURATE_CLASSIFICATIONS.set(get_stat('accurate_classifications'))
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=reported_message_id)
            await context.bot.ban_chat_member(chat_id=chat_id, user_id=reported_user_id)
            await update.message.reply_text("✅ User banned.")
        except Exception as e:
            logging.error(f"Error banning reported user: {e}")
            await update.message.reply_text("✅ Message added to training examples. Could not ban user.")
    else:
        # Store and send to admins for review
        reported_messages[reported_message_id] = {
            "text": reported_text,
            "user_id": reported_user_id,
            "chat_id": chat_id,
            "message_id": reported_message_id,
            "reported_by": update.message.from_user.username or str(user_id)
        }
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Confirm Ban", callback_data=f"report_confirm|{reported_message_id}|{chat_id}"),
                InlineKeyboardButton("❌ Dismiss", callback_data=f"report_dismiss|{reported_message_id}|{chat_id}")
            ]
        ])
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"🚨 Scam report by @{reported_messages[reported_message_id]['reported_by']}. Admin review required:",
            reply_markup=keyboard
        )

async def handle_report_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles admin confirmation/dismissal of user-reported scams."""
    query = update.callback_query
    user_id = query.from_user.id
    chat_id = query.message.chat_id

    # Check if admin
    chat_member = await context.bot.get_chat_member(chat_id, user_id)
    if chat_member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
        await query.answer("Only admins can do this.")
        return

    data = query.data.split("|")
    action = data[0]
    message_id = int(data[1])

    report_info = reported_messages.get(message_id)
    if not report_info:
        await query.answer("Report expired — bot may have restarted. Please /report again.")
        return

    if action == "report_confirm":
        if report_info["text"] is not None:
            from vector_store import add_example
            add_example(report_info["text"], "BAN")
            sync_example_to_github(report_info["text"], "BAN")
            increment_stat('false_negatives')
            FALSE_NEGATIVES.set(get_stat('false_negatives'))
            decrement_stat('accurate_classifications')
            ACCURATE_CLASSIFICATIONS.set(get_stat('accurate_classifications'))
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=report_info["message_id"])
            await context.bot.ban_chat_member(chat_id=chat_id, user_id=report_info["user_id"])
            await query.edit_message_text("✅ Report confirmed. User banned.")
        except Exception as e:
            logging.error(f"Error banning reported user: {e}")
            await query.edit_message_text("✅ Could not ban user — they may have already left.")

    elif action == "report_dismiss":
        await query.edit_message_text("❌ Report dismissed.")

    del reported_messages[message_id]
    await query.answer()

async def update_member_counts(context: ContextTypes.DEFAULT_TYPE):
    """Background task to update member counts daily."""
    group_ids = get_all_group_ids()
    for chat_id in group_ids:
        try:
            count = await context.bot.get_chat_member_count(chat_id)
            update_group_member_count(chat_id, count)
        except Exception as e:
            logging.error(f"Error updating member count for {chat_id}: {e}")
    MEMBERS_PROTECTED.set(get_total_members())
    logging.info("Updated member counts for all groups")

async def handle_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles /stats command — admins only."""
    if not update.message:
        return

    chat_id = update.message.chat_id
    user_id = update.message.from_user.id

    chat_member = await context.bot.get_chat_member(chat_id, user_id)
    if chat_member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
        await update.message.reply_text("Only admins can use this command.")
        return

    accurate = get_stat('accurate_classifications')
    total = accurate + get_stat('false_positives') + get_stat('false_negatives')
    accuracy = (accurate / total * 100) if total > 0 else 0

    await update.message.reply_text(
        f"📊 Sus Message Bot Stats\n\n"
        f"👥 Groups protected: {get_groups_count()}\n"
        f"🛡️ Members protected: {get_total_members():,}\n"
        f"📨 Messages scanned: {get_stat('messages_safe') + get_stat('messages_ban'):,}\n"
        f"🚫 Total bans: {get_stat('bans_confirmed') + get_stat('false_positives')}\n"
        f"✅ Accuracy rate: {accuracy:.1f}%\n"
    )

def main():
    if not TELEGRAM_BOT_TOKEN:
        print("TELEGRAM_BOT_TOKEN is not set. Exiting.")
        return
    init_db() 
    init_metrics()
    start_health_server()
    start_http_server(8000)  # Prometheus metrics endpoint on port 8000
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(handle_callback, pattern="^(correct|false)"))
    app.add_handler(CallbackQueryHandler(handle_report_callback, pattern="^(report_confirm|report_dismiss)"))
    app.add_handler(CommandHandler("report", handle_report))
    app.add_handler(CommandHandler("stats", handle_stats))
    app.job_queue.run_repeating(update_member_counts, interval=86400, first=86400)
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