import os
import random
import asyncio
import logging
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, constants
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes, CallbackQueryHandler, CommandHandler
from duckduckgo_search import DDGS

# --- PROXY/SYSTEM CONFIGURATION ---
TOKEN = "8285816250:AAHHk215dEkzgcFoea3-DlcG9i8csyb90vM"
PORT = int(os.environ.get("PORT", 10000))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- AXIOMATIC GAME ENGINE (BITLIFE LOGIC) ---
class BitLifeEngine:
    def __init__(self):
        self.users = {}

    def get_user(self, uid):
        if uid not in self.users:
            self.users[uid] = {
                "age": 16, "money": 500, "health": 100, 
                "happiness": 100, "intellect": 50, "job": "Student"
            }
        return self.users[uid]

    def process_event(self, uid):
        u = self.get_user(uid)
        u["age"] += random.randint(0, 1) # Aging based on interaction frequency
        
        events = [
            {"msg": "💰 Found a side hustle!", "m": 300, "h": -5, "hp": 10, "i": 5},
            {"msg": "🩺 Caught a fever.", "m": -150, "h": -20, "hp": -10, "i": 0},
            {"msg": "📚 Finished a G12 module.", "m": -50, "h": -5, "hp": 5, "i": 15},
            {"msg": "🎰 Won a small lottery!", "m": 1500, "h": 0, "hp": 50, "i": -5},
            {"msg": "📉 Crypto crashed.", "m": -400, "h": 0, "hp": -20, "i": 5},
            {"msg": "🧘 Meditation session.", "m": 0, "h": 10, "hp": 20, "i": 5}
        ]
        
        ev = random.choice(events)
        u["money"] += ev["m"]
        u["health"] = max(0, min(100, u["health"] + ev["h"]))
        u["happiness"] = max(0, min(100, u["happiness"] + ev["hp"]))
        u["intellect"] += ev["i"]
        
        if u["health"] <= 0:
            self.users[uid] = {"age": 0, "money": 0, "health": 100, "happiness": 100, "intellect": 0, "job": "Reincarnated"}
            return "💀 Life Critical. You have been reincarnated."
        
        return ev["msg"]

# --- QUANTUM SEARCH ENGINE (DDGS WRAPPER) ---
class SearchEngine:
    @staticmethod
    async def execute(category, query):
        prefixes = {
            "MOVIE": f"site:t.me/s/ (mmsub OR 'mm sub' OR 'myanmar subtitle') {query}",
            "SERIES": f"site:t.me/s/ (mmsub OR 'mm sub' OR 'myanmar subtitle' OR 'season' OR 'episodes') {query}",
            "MUSIC": f"site:t.me/s/ (music OR song OR album OR mp3) {query}",
            "EDU": f"site:t.me/s/ ('Grade 12' OR 'BEHS' OR 'Myanmar Education') {query}",
            "GENERAL": f"site:t.me/s/ {query}"
        }
        
        sq = prefixes.get(category, f"site:t.me/s/ {query}")
        results = []
        
        try:
            with DDGS() as ddgs:
                gen = ddgs.text(sq, max_results=12)
                for r in gen:
                    link = r['href'].replace('t.me/s/', 't.me/')
                    results.append(f"📌 **{r['title']}**\n🔗 {link}")
            
            return "\n\n".join(results[:8]) if results else "∅ No vectors found in current manifold."
        except Exception as e:
            logger.error(f"Search Failure: {e}")
            return "⚠️ Systemic entropy detected. Search aborted."

# --- BOT CONTROLLER ---
game = BitLifeEngine()
search = SearchEngine()

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [
        [InlineKeyboardButton("🎬 Movie", callback_data='MOVIE'), InlineKeyboardButton("📺 Series", callback_data='SERIES')],
        [InlineKeyboardButton("🎵 Music", callback_data='MUSIC'), InlineKeyboardButton("🎓 Edu", callback_data='EDU')],
        [InlineKeyboardButton("🌍 General", callback_data='GENERAL')],
        [InlineKeyboardButton("📊 My Stats", callback_data='STATS')]
    ]
    await update.message.reply_text(
        "**SYSTEM INITIALIZED**\nSelect target domain for indexing or check life metrics:",
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode=constants.ParseMode.MARKDOWN
    )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid = query.from_user.id
    await query.answer()

    if query.data == 'STATS':
        u = game.get_user(uid)
        msg = (f"👤 **METRICS: {uid}**\n"
               f"━━━━━━━━━━━━━━\n"
               f"🎂 Age: {u['age']}\n💰 Wealth: {u['money']} Ks\n"
               f"❤️ Vitality: {u['health']}%\n😊 Euphoria: {u['happiness']}%\n"
               f"🧠 Intellect: {u['intellect']}\n💼 Status: {u['job']}")
        await query.message.reply_text(msg, parse_mode=constants.ParseMode.MARKDOWN)
    else:
        context.user_data['cat'] = query.data
        await query.edit_message_text(f"🌐 Mode: **{query.data}**\nEnter query string...")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    cat = context.user_data.get('cat', 'GENERAL')
    user_query = update.message.text

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=constants.ChatAction.TYPING)
    
    # Concurrent Execution
    search_task = asyncio.create_task(search.execute(cat, user_query))
    event_msg = game.process_event(uid)
    u = game.get_user(uid)
    
    search_res = await search_task
    
    output = (f"🔍 **INDEX RESULTS [{cat}]**\n{search_res}\n\n"
              f"━━━━━━━━━━━━━━\n"
              f"🎲 **STOCHASTIC EVENT:**\n{event_msg}\n\n"
              f"💰 Balance: {u['money']} Ks | ❤️ Health: {u['health']}%")
    
    await update.message.reply_text(output, parse_mode=constants.ParseMode.MARKDOWN, disable_web_page_preview=True)

# --- WEB SERVER / WEBHOOK ---
app = Flask(__name__)
bot_app = ApplicationBuilder().token(TOKEN).build()

bot_app.add_handler(CommandHandler("start", cmd_start))
bot_app.add_handler(CallbackQueryHandler(handle_callback))
bot_app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text))

@app.route(f'/{TOKEN}', methods=['POST'])
async def webhook():
    if request.method == "POST":
        update = Update.de_json(request.get_json(force=True), bot_app.bot)
        await bot_app.process_update(update)
        return "OK", 200

@app.route('/')
def health():
    return "Status: Operational. Signal-to-Entropy Ratio: High.", 200

if __name__ == "__main__":
    from threading import Thread
    Thread(target=lambda: app.run(host='0.0.0.0', port=PORT, use_reloader=False)).start()
    bot_app.run_polling() # Local testing or managed hosting
