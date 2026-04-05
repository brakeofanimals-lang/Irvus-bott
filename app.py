import os, requests, asyncio
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters

app = Flask(__name__)
@app.route('/')
def home(): return "IRVUS SETTINGS PANEL ACTIVE", 200

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

TOKEN = "8621050385:AAGA6wcxbFY2rqJ9gjXVK_JNqsebJvTv_Jo"
# Grupların özel ayarlarını tutan hafıza
db = {} 

# --- AYARLAR PANELİ BUTONLARI (Görseldekiyle Aynı) ---
def get_buy_settings_buttons(chat_id):
    data = db.get(chat_id, {})
    emoji = data.get("emoji", "🟢")
    min_buy = data.get("min_buy", "0")
    media_status = "🚫" if not data.get("media") else "🖼"
    
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"{media_status} Gif / Image", callback_data="toggle_media"),
         InlineKeyboardButton(f"⬆️ Min Buy ${min_buy}", callback_data="set_minbuy")],
        [InlineKeyboardButton(f"{emoji} Buy Emoji", callback_data="set_emoji"),
         InlineKeyboardButton("💰 Buy Step $10", callback_data="set_step")],
        [InlineKeyboardButton("Big Buy Comp ⏩", callback_data="comp_big"),
         InlineKeyboardButton("Last Buy Comp ⏩", callback_data="comp_last")],
        [InlineKeyboardButton("⚙️ Group Settings", callback_data="group_sets")],
        [InlineKeyboardButton("🥇 Trending Fast-Track", url="https://x.com/IRVUSTOKEN")],
        [InlineKeyboardButton("🎟 Premium (Ad-Free)", url="https://www.irvustoken.xyz")]
    ])

# --- KURULUM AKIŞI ---
async def add_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    db[chat_id] = {"step": "WAIT_NET", "emoji": "🟢", "min_buy": "0", "media": True}
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("Ethereum", callback_data="net_ETH"), 
                                 InlineKeyboardButton("BSC", callback_data="net_BSC"),
                                 InlineKeyboardButton("Base", callback_data="net_BASE")]])
    await update.message.reply_text("➡️ **Select Chain**", reply_markup=kb)

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    chat_id = str(query.message.chat_id)
    await query.answer()

    if "net_" in query.data:
        db[chat_id]["step"] = "WAIT_CA"
        await query.edit_message_text(f"🟡 **{query.data.split('_')[1]} Token address?**")

    elif "pair_" in query.data:
        p_name = query.data.split("_")[2]
        db[chat_id].update({"pair_id": query.data.split("_")[1], "step": "DONE"})
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("🟢 Buy Bot Settings", callback_data="open_settings")]])
        await query.edit_message_text(f"✅ **{p_name}** added to **Irvus Bot!**", reply_markup=kb)

    elif query.data == "open_settings":
        await query.edit_message_text("⚙️ **Buy Bot Settings**", reply_markup=get_buy_settings_buttons(chat_id))

    # Ayarları Değiştirme (Örnek: Medya Aç/Kapat)
    elif query.data == "toggle_media":
        db[chat_id]["media"] = not db[chat_id].get("media", True)
        await query.edit_message_reply_markup(reply_markup=get_buy_settings_buttons(chat_id))

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    if db.get(chat_id, {}).get("step") == "WAIT_CA":
        ca = update.message.text.strip()
        try:
            r = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{ca}").json()
            pairs = r.get('pairs', [])[:3]
            buttons = [[InlineKeyboardButton(f"✅ {p['baseToken']['symbol']}", callback_data=f"pair_{p['pairAddress']}_{p['baseToken']['symbol']}")] for p in pairs]
            await update.message.reply_text("ℹ️ **Select Pair**", reply_markup=InlineKeyboardMarkup(buttons))
        except: pass

if __name__ == '__main__':
    Thread(target=run_web, daemon=True).start()
    app_tg = Application.builder().token(TOKEN).build()
    app_tg.add_handler(CommandHandler("add", add_command))
    app_tg.add_handler(CallbackQueryHandler(handle_callback))
    app_tg.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app_tg.run_polling(drop_pending_updates=True)
    
