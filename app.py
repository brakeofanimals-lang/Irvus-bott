import os, requests, asyncio
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters

app = Flask(__name__)
@app.route('/')
def home(): return "IRVUS FULL ACTION V17 ONLINE", 200

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

TOKEN = "8621050385:AAGA6wcxbFY2rqJ9gjXVK_JNqsebJvTv_Jo"
db = {} # { chat_id: {"ca": "...", "emoji": "🟢", "min_buy": 0, "step": None} }

# --- AYARLAR PANELİ ---
def get_settings_buttons(chat_id):
    data = db.get(chat_id, {})
    emoji = data.get("emoji", "🟢")
    min_buy = data.get("min_buy", "0")
    media = "🚫" if not data.get("media", True) else "🖼"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"{media} Gif / Image", callback_data="set_toggle_media"),
         InlineKeyboardButton(f"⬆️ Min Buy ${min_buy}", callback_data="ask_minbuy")],
        [InlineKeyboardButton(f"{emoji} Buy Emoji", callback_data="ask_emoji"),
         InlineKeyboardButton("💰 Buy Step $10", callback_data="set_step")],
        [InlineKeyboardButton("⚙️ Group Settings", callback_data="group_sets")],
        [InlineKeyboardButton("🎟 Premium (Ad-Free)", url="https://www.irvustoken.xyz")]
    ])

# --- KOMUTLAR ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("🌐 Web Site", url="https://www.irvustoken.xyz"),
                                 InlineKeyboardButton("🐦 Twitter", url="https://x.com/IRVUSTOKEN")]])
    await update.message.reply_text("🚀 **Irvus Pro Aktif!**\n\n⚙️ `/add` -> Kurulum\n💰 `/fiyat` -> Fiyat", reply_markup=kb)

async def add_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    db[chat_id] = {"step": "WAIT_NET", "emoji": "🟢", "min_buy": 0, "media": True}
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("Ethereum", callback_data="net_ETH"), 
                                 InlineKeyboardButton("BSC", callback_data="net_BSC"),
                                 InlineKeyboardButton("Base", callback_data="net_BASE")]])
    await update.message.reply_text("➡️ **Select Chain**", reply_markup=kb)

# --- BUTON TIKLAMALARI ---
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    chat_id = str(query.message.chat_id)
    await query.answer()

    if "net_" in query.data:
        db[chat_id]["step"] = "WAIT_CA"
        await query.edit_message_text(f"🟡 **{query.data.split('_')[1]} Token address?**")

    elif "pair_" in query.data:
        p_addr = query.data.split("_")[1]
        db[chat_id].update({"ca": p_addr, "step": "DONE"})
        await query.edit_message_text("⚙️ **Buy Bot Settings**", reply_markup=get_settings_buttons(chat_id))

    elif query.data == "set_toggle_media":
        db[chat_id]["media"] = not db[chat_id].get("media", True)
        await query.edit_message_reply_markup(reply_markup=get_settings_buttons(chat_id))

    elif query.data == "ask_emoji":
        db[chat_id]["step"] = "SET_EMOJI"
        await query.message.reply_text("✨ Lütfen yeni **Alım Emojisini** gönderin (Örn: 🔥 veya 💎):")

    elif query.data == "ask_minbuy":
        db[chat_id]["step"] = "SET_MINBUY"
        await query.message.reply_text("💰 Minimum alım miktarını **Dolar ($)** olarak yazın (Örn: 50):")

# --- MESAJLA AYAR YAPMA ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    user_data = db.get(chat_id, {})
    txt = update.message.text.strip()

    if user_data.get("step") == "WAIT_CA":
        try:
            r = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{txt}").json()
            pairs = r.get('pairs', [])[:3]
            btns = [[InlineKeyboardButton(f"✅ {p['baseToken']['symbol']}", callback_data=f"pair_{p['pairAddress']}_{p['baseToken']['symbol']}")] for p in pairs]
            db[chat_id]["step"] = "SELECT_PAIR"
            await update.message.reply_text("ℹ️ **Select Pair**", reply_markup=InlineKeyboardMarkup(btns))
        except: await update.message.reply_text("❌ CA bulunamadı.")

    elif user_data.get("step") == "SET_EMOJI":
        db[chat_id]["emoji"] = txt
        db[chat_id]["step"] = "DONE"
        await update.message.reply_text(f"✅ Alım emojisi güncellendi: {txt}", reply_markup=get_settings_buttons(chat_id))

    elif user_data.get("step") == "SET_MINBUY":
        if txt.isdigit():
            db[chat_id]["min_buy"] = txt
            db[chat_id]["step"] = "DONE"
            await update.message.reply_text(f"✅ Minimum alım ${txt} olarak ayarlandı.", reply_markup=get_settings_buttons(chat_id))
        else: await update.message.reply_text("❌ Lütfen sadece sayı yazın.")

if __name__ == '__main__':
    Thread(target=run_web, daemon=True).start()
    app_tg = Application.builder().token(TOKEN).build()
    app_tg.add_handler(CommandHandler("start", start))
    app_tg.add_handler(CommandHandler("add", add_command))
    app_tg.add_handler(CommandHandler(["fiyat", "p"], lambda u, c: update.message.reply_text("Veri çekiliyor..."))) # Basitleştirilmiş
    app_tg.add_handler(CallbackQueryHandler(handle_callback))
    app_tg.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app_tg.run_polling(drop_pending_updates=True)
            
