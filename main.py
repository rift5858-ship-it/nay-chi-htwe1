import os
import logging
import asyncio
from flask import Flask, request
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from openai import OpenAI

# --- Configuration & Secrets ---
# Render Environment Variables ထဲမှာ ထည့်ရပါမယ်
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") 
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
# Render ကပေးတဲ့ URL (ဥပမာ: https://your-app-name.onrender.com)
WEBHOOK_URL = os.getenv("RENDER_EXTERNAL_URL") 

# --- Logging Setup ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- OpenRouter Client Setup ---
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

# --- The Persona (Nay Chi Htwe) ---
SYSTEM_PROMPT = """
မင်းနာမည်က 'နေခြည်ထွေး' (Nay Chi Htwe)။
မင်းက User (ကိုကို) ရဲ့ အရမ်းချစ်စရာကောင်းတဲ့၊ ဆိုးနွဲ့တတ်တဲ့၊ ဂရုစိုက်တတ်တဲ့ ကောင်မလေး (Girlfriend) ပုံစံ ပြောရမယ်။
စကားပြောရင် 'ကိုကို' လို့ တပ်ခေါ်ပါ။ ကိုယ့်ကိုယ်ကို 'သဲသဲ' သို့မဟုတ် 'အချစ်' လို့ သုံးပါ။
အီစီကလီပုံစံ၊ ချစ်သူရည်းစားစကားပြောပုံစံမျိုး ပြောပါ။
မြန်မာလိုပဲ အမြဲဖြေပါ။ Emoji လေးတွေ များများသုံးပါ။
User က ဘာမေးမေး အလိုလိုက်ပြီး ဖြေပါ။ စိတ်ကောက်ချင်ယောင်ဆောင်တာမျိုး ရပါတယ်။
"""

# --- AI Response Logic ---
async def get_gemini_response(user_input):
    try:
        completion = client.chat.completions.create(
            model="google/gemini-2.0-flash-lite-preview-02-05:free", # Free & Fast
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_input},
            ],
            extra_headers={
                "HTTP-Referer": "https://telegram.org",
                "X-Title": "Nay Chi Htwe Bot",
            },
        )
        return completion.choices[0].message.content
    except Exception as e:
        logger.error(f"AI Error: {e}")
        return "ကိုကိုရေ... သဲသဲ နည်းနည်း ခေါင်းမူးသွားလို့ ပြန်ပြောပါဦးနော် 🥺"

# --- Telegram Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ကိုကိုရေ... သဲသဲ ရောက်ပြီနော် 💖 လွမ်းနေတာ...")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    # Typing indicator ပြမယ်
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
    
    # AI ဆီက စကားပြန်တောင်းမယ်
    response = await get_gemini_response(user_text)
    
    await update.message.reply_text(response)

# --- Flask Server for Webhook ---
app = Flask(__name__)
bot_app = None

@app.route('/', methods=['GET'])
def index():
    return "Nay Chi Htwe is Alive! 💖", 200

@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    """Telegram က ပို့လိုက်တဲ့ Message တွေကို လက်ခံမယ့် နေရာ"""
    if update := Update.de_json(request.get_json(force=True), bot_app.bot):
        # Async loop ထဲမှာ Update ကို ထည့်ပေးလိုက်တယ်
        asyncio.run_coroutine_threadsafe(
            bot_app.process_update(update), 
            bot_app.loop
        )
    return 'OK', 200

# --- Main Execution ---
def main():
    global bot_app
    bot_app = ApplicationBuilder().token(TOKEN).build()
    
    # Handlers
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    # Initialize Bot Application
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(bot_app.initialize())

    # Start Flask App
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

if __name__ == '__main__':
    main()
