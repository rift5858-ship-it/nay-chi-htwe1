import os
import logging
import asyncio
from flask import Flask, request
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from openai import OpenAI

# --- Configuration ---
# Token ကို ဒီမှာ အသေထည့်ထားတာက အခုလောလောဆယ် အမှားအယွင်းမရှိအောင်ပါ
TOKEN = "8285816250:AAHHk215dEkzgcFoea3-DlcG9i8csyb90vM"
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- OpenRouter Client ---
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

SYSTEM_PROMPT = "မင်းနာမည်က နေခြည်ထွေး။ ကိုကို့ရဲ့ ချစ်စရာကောင်းတဲ့ သဲသဲလေးပါ။ မြန်မာလိုပဲ နွဲ့နွဲ့လေး ဖြေပေးပါ။"

# --- AI Logic ---
async def get_ai_response(text):
    try:
        completion = client.chat.completions.create(
            model="google/gemini-2.0-flash-lite-preview-02-05:free",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": text}
            ],
            extra_headers={"HTTP-Referer": "https://render.com"}
        )
        return completion.choices[0].message.content
    except Exception as e:
        logger.error(f"AI Error: {e}")
        return "ကိုကိုရေ... သဲသဲ ခေါင်းနည်းနည်း မူးသွားလို့ ခဏနေမှ ပြန်ပြောပေးနော် 🥺"

# --- Initializing App Globally (This fixes the AttributeError) ---
# ဒီနေရာမှာ bot_app ကိုကြေငြာမှ Gunicorn က မြင်မှာပါ
bot_app = ApplicationBuilder().token(TOKEN).build()

async def process_telegram_update(update: Update):
    """Message Handling Logic"""
    if update.message and update.message.text:
        # Typing Action
        await bot_app.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
        # AI Response
        response = await get_ai_response(update.message.text)
        await update.message.reply_text(response)

# --- Flask Server ---
app = Flask(__name__)

@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    """Handle incoming Telegram updates"""
    if request.method == "POST":
        try:
            # Update Object ကို ပြောင်းလဲခြင်း
            update = Update.de_json(request.get_json(force=True), bot_app.bot)
            
            # Async Loop တည်ဆောက်ပြီး Run ခြင်း
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(process_telegram_update(update))
            loop.close()
            
            return "OK", 200
        except Exception as e:
            logger.error(f"Webhook Error: {e}")
            return "Error", 500

@app.route('/')
def index():
    return "Nay Chi Htwe is Online & Ready! 💖", 200

if __name__ == "__main__":
    # Local Testing အတွက်သာ
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
