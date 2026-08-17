import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, 
    CommandHandler, 
    ContextTypes
)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", 
    level=logging.INFO
)

# --- CONFIGURATION ---

# Read configuration from environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", "0"))

# SQLite database file path
DB_FILE = os.getenv("DB_FILE", "bot_subscribers.db")

BOT_TOKEN = "8864761914:AAE94-j290jeUhZkKiLoYkg2_9tWLEwsqvE"  # Token from @BotFather
ADMIN_USER_ID = 7284852220      # Your numeric Telegram user ID
DB_FILE = "bot_subscribers.db"

# --- DATABASE HELPER FUNCTIONS ---
def init_db():
    """Initializes the SQLite database table."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS subscribers (
            user_id INTEGER PRIMARY KEY,
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def add_subscriber(user_id: int):
    """Adds a new subscriber to the database."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO subscribers (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()

def get_subscribers():
    """Fetches all subscriber chat IDs from the database."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM subscribers")
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]

def remove_subscriber(user_id: int):
    """Removes a subscriber who has blocked the bot or deleted their account."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM subscribers WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

# --- HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    add_subscriber(chat_id)

    # Inline buttons
    keyboard = [
        [InlineKeyboardButton(text="🌐 የመከታተያ ቁጥር ላክ", url="https://addismobileapps.com/sms.html")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    caption_text = f"👋 እንኳን ወደ ቤስት ጆብስ የምዝገባ ማዕከል በሰላም መጡ። {update.effective_user.first_name}!\n\n የመከታተያ ቁጥር ላክ ለማግኘት ከታች ያለውን ሊንክ ነክተው መልእክቱን ይላኩ"

    # Path to the image in your folder
    image_path = os.path.join("image", "img1.jpg")

    # Open and send the image
    with open(image_path, "rb") as photo_file:
        await update.message.reply_photo(
            photo=photo_file,
            caption=caption_text,
            reply_markup=reply_markup
        )
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sender_id = update.effective_user.id

    # Admin restriction check
    if sender_id != ADMIN_USER_ID:
        await update.message.reply_text("⛔ Unauthorized command.")
        return

    # Reply check
    if not update.message.reply_to_message:
        instructions = (
            "⚠️ **How to Broadcast Media & Buttons:**\n\n"
            "1. Upload or forward any **Photo, Video, GIF, or Text** to this chat.\n"
            "2. **Reply** to that media message with:\n"
            "`/broadcast Button Text | https://yourlink.com`\n\n"
            "*Example:*\n`/broadcast 🚀 Visit Website | https://google.com`"
        )
        await update.message.reply_text(instructions, parse_mode="Markdown")
        return

    # Parse link button from reply command
    args_text = " ".join(context.args)
    reply_markup = None

    if "|" in args_text:
        try:
            button_label, button_url = args_text.split("|", 1)
            button_label = button_label.strip()
            button_url = button_url.strip()

            inline_keyboard = [[InlineKeyboardButton(text=button_label, url=button_url)]]
            reply_markup = InlineKeyboardMarkup(inline_keyboard)
        except Exception:
            await update.message.reply_text("❌ Invalid button format. Use: `Button Text | https://url.com`", parse_mode="Markdown")
            return

    target_msg = update.message.reply_to_message
    subscribers_list = get_subscribers()

    sent_count = 0
    failed_count = 0

    status_msg = await update.message.reply_text(f"🔄 Broadcasting to {len(subscribers_list)} users...")

    for user_id in subscribers_list:
        try:
            await context.bot.copy_message(
                chat_id=user_id,
                from_chat_id=target_msg.chat_id,
                message_id=target_msg.message_id,
                reply_markup=reply_markup
            )
            sent_count += 1
        except Exception as e:
            logging.error(f"Failed delivery to {user_id}: {e}")
            failed_count += 1
            # Automatically clean up users who blocked the bot or deleted their account
            remove_subscriber(user_id)

    await status_msg.edit_text(
        f"📢 **Broadcast Complete**\n\n"
        f"✅ Delivered: {sent_count}\n"
        f"❌ Removed/Blocked: {failed_count}\n"
        f"📊 Remaining DB Active Users: {len(get_subscribers())}",
        parse_mode="Markdown"
    )

def main():
    # Initialize the database on startup
    init_db()

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("broadcast", broadcast))

    logging.info("Bot started successfully with SQLite persistence.")
    app.run_polling()

if __name__ == "__main__":
    main()