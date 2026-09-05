import os
import uuid
import time
from threading import Thread
from flask import Flask, redirect, abort
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# --- 1. Flask App Setup ---
app = Flask(__name__)

# In-memory store for links (Note: Cleared on app restart)
# Format: { unique_id: {"destination": str, "expires_at": float} }
link_db = {}

# Set how long links should last (in seconds). Example: 300 seconds = 5 minutes
LINK_LIFETIME = 300 

@app.route('/')
def home():
    return "Bot and Link Expire Service are running!"

@app.route('/l/<link_id>')
def handle_redirect(link_id):
    """Handles short links and checks if they are expired."""
    data = link_db.get(link_id)
    
    if not data:
        return "Link not found or has already expired.", 404
        
    # Check if link expired
    if time.time() > data["expires_at"]:
        del link_db[link_id]  # Clean up expired link
        return "This link has expired!", 410

    # Redirect user to the original target URL
    return redirect(data["destination"])

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# --- 2. Telegram Bot Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome! Send /gen <URL> to create a temporary link that expires in 5 minutes."
    )

async def generate_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /gen https://example.com")
        return

    original_url = context.args[0]
    if not original_url.startswith(("http://", "https://")):
        await update.message.reply_text("Please provide a valid URL starting with http:// or https://")
        return

    # Generate a unique ID for the link
    link_id = str(uuid.uuid4())[:8]
    expires_at = time.time() + LINK_LIFETIME
    
    # Store in memory
    link_db[link_id] = {
        "destination": original_url,
        "expires_at": expires_at
    }

    # Build the short link using your Render app's domain
    # Example: https://your-app-name.onrender.com/l/abc1234
    render_domain = os.environ.get("RENDER_EXTERNAL_URL", "http://localhost:10000")
    expiring_url = f"{render_domain}/l/{link_id}"

    await update.message.reply_text(
        f"Here is your temporary link (expires in 5 minutes):\n\n{expiring_url}"
    )

# --- 3. Start Bot and Flask Thread ---
if __name__ == "__main__":
    # Start Flask HTTP server in background thread for Render compatibility
    Thread(target=run_flask).start()

    # Get your bot token from environment variables
    BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
    
    if not BOT_TOKEN:
        print("Error: TELEGRAM_BOT_TOKEN environment variable missing!")
    else:
        bot_app = ApplicationBuilder().token(BOT_TOKEN).build()
        bot_app.add_handler(CommandHandler("start", start))
        bot_app.add_handler(CommandHandler("gen", generate_link))
        
        print("Bot is starting...")
        bot_app.run_polling()
      
