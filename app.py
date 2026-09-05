import os
import asyncio
from threading import Thread
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# --- 1. Flask Web Server (Required for Render) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# --- 2. Auto-Delete Channel Link Logic ---

# Set your target Channel ID (e.g., -1001234567890 or "@YourChannelUsername")
CHANNEL_ID = os.environ.get("CHANNEL_ID")

async def post_expiring_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Usage in Bot DM: /postlink https://example.com 5
    (where 5 is the expiration time in minutes)
    """
    if not context.args:
        await update.message.reply_text("Usage: /postlink <URL> [minutes]\nExample: /postlink https://google.com 5")
        return

    url = context.args[0]
    # Default to 2 minutes if time is not specified
    expire_minutes = int(context.args[1]) if len(context.args) > 1 else 2
    delay_seconds = expire_minutes * 60

    try:
        # 1. Post the link to the channel
        sent_message = await context.bot.send_message(
            chat_id=CHANNEL_ID,
            text=f"🔗 **Temporary Link** (Self-destructs in {expire_minutes} mins):\n\n{url}",
            parse_mode="Markdown"
        )
        
        await update.message.reply_text(f"Link posted to channel! It will be deleted in {expire_minutes} minute(s).")

        # 2. Wait in background for specified time
        await asyncio.sleep(delay_seconds)

        # 3. Automatically delete the channel post
        await context.bot.delete_message(
            chat_id=CHANNEL_ID,
            message_id=sent_message.message_id
        )

    except Exception as e:
        print(f"Error handling post: {e}")

# --- 3. Bot Initialization ---
if __name__ == "__main__":
    # Start Flask server
    Thread(target=run_flask).start()

    BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
    
    bot_app = ApplicationBuilder().token(BOT_TOKEN).build()
    bot_app.add_handler(CommandHandler("postlink", post_expiring_link))

    print("Jeichotom Mara✓")
    bot_app.run_polling()
    
