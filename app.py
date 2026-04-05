import os, requests, asyncio
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters

app = Flask(__name__)
@app.route('/')
def home(): return "IRVUS MULTI-LANG V23 ONLINE", 200

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

TOKEN = "8621050385:AAGA6wcxbFY2rqJ9gjXVK_JNqsebJvTv_Jo"
db = {} # { chat_id: {"lang": "tr", "ca": "...", "emoji": "🟢", ...} }

# --- DİL PAKETLERİ ---
STRINGS = {
    "tr": {
        "welcome": "🚀 **Irvus Pro Bot'a Hoş Geldiniz!**\n\n🖼 `/ciz` -> AI Çizim\n💰 `/fiyat` -> Fiyat Bilgisi\n⚙️ `/add` -> Kurulum",
        "select_net": "➡️ **Lütfen Ağ Seçin:**",
        "send_ca": "🟡 **{} Kontrat Adresini Gönderin:**",
        "setup_done": "✅ **{}** Kurulum Tamamlandı!",
        "no_setup": "❌ Önce `/add` yaparak bir havuz seçmelisin.",
        "ask_emoji": "✨ Yeni emojiyi gönderin:",
        "ask_min": "💰 Min dolar miktarını yazın:"
    },
    "en": {
        "welcome": "🚀 **Welcome to Irvus Pro Bot!**\n\n🖼 `/draw` -> AI Image\n💰 `/price` -> Market Data\n⚙️ `/add` -> Setup",
        "select_net": "➡️ **Select Chain:**",
        "send_ca": "🟡 **Send {} Token Address:**",
        "setup_done": "✅ **{}** Setup Completed!",
        "no_setup": "❌ Please setup first using `/add`.",
        "ask_emoji": "✨ Send the new emoji:",
        "ask_min": "💰 Enter min dollar amount:"
    }
}

# --- BUTONLAR ---
def get_start_buttons():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🇹🇷 Türkçe", callback_data="l_tr"), InlineKeyboardButton("🇺🇸 English", callback_data="l_en")],
        [InlineKeyboardButton("🌐 Web Site", url="https://www.irvustoken.xyz"), InlineKeyboardButton("🐦 Twitter", url="https://x.com/IRVUSTOKEN")]
    ])

def get_settings_buttons(chat_id):
    data = db.get(chat_id, {})
    emoji = data.get("emoji", "🟢")
    min_buy = data.get("min_buy", "0")
    media = "🚫" if not data.get("media", True) else "🖼"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"{media} Gif / Image", callback_data="btn_media"), InlineKeyboardButton(f"⬆️ Min Buy ${min_buy}", callback_data="btn_min")],
        [InlineKeyboardButton(f"{emoji} Buy Emoji", callback_data="btn_emoji"), InlineKeyboardButton("💰 Buy Step $10", callback_data="btn_step")],
        [InlineKeyboardButton("⚙️ Group Settings", callback_data="btn_group")],
        [InlineKeyboardButton("🔹 Premium (Ad-Free) 🔹", url="https://www.irvustoken.xyz")]
    ])

# --- KOMUTLAR ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Please select your language / Lütfen dil seçiniz:", reply_markup=get_start_buttons())

async def add_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    lang = db.get(chat_id, {}).get("lang", "en")
    db[chat_id] = {"lang": lang, "step": "WAIT_NET", "emoji": "🟢", "min_buy": 0, "media": True, "pairs": []}
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("Ethereum", callback_data="n_eth"), InlineKeyboardButton("BSC", callback_data="n_bsc"), InlineKeyboardButton("Base", callback_data="n_base")]])
    await update.message.reply_text(STRINGS[lang]["select_net"], reply_markup=kb)

async def price_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    lang = db.get(chat_id, {}).get("lang", "en")
    ca = db.get(chat_id, {}).get("ca")
    if not ca:
        await update.message.reply_text(STRINGS[lang]["no_setup"])
        return
    try:
        r = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{ca}").json()
        p = r['pairs'][0]
        msg = f"💎 **{p['baseToken']['symbol']}**\n💰 Price: `${p['priceUsd']}`\n📊 24h: %{p['priceChange']['h24']}"
        await update.message.reply_text(msg)
    except: pass

# --- CALLBACK ---
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    chat_id = str(query.message.chat_id)
    await query.answer()

    if query.data.startswith("l_"):
        lang = query.data.split("_")[1]
        if chat_id not in db: db[chat_id] = {}
        db[chat_id]["lang"] = lang
        await query.edit_message_text(STRINGS[lang]["welcome"], reply_markup=get_start_buttons(), parse_mode='Markdown')

    elif query.data.startswith("n_"):
        lang = db.get(chat_id, {}).get("lang", "en")
        db[chat_id]["step"] = "WAIT_CA"
        await query.edit_message_text(STRINGS[lang]["send_ca"].format(query.data[2:].upper()))

    elif query.data.startswith("idx_"):
        lang = db.get(chat_id, {}).get("lang", "en")
        idx = int(query.data.split("_")[1])
        pair = db[chat_id]["pairs"][idx]
        db[chat_id].update({"ca": pair['addr'], "sym": pair['sym'], "step": "DONE"})
        await query.edit_message_text(STRINGS[lang]["setup_done"].format(pair['sym']), reply_markup=get_settings_buttons(chat_id))

    elif query.data == "btn_media":
        db[chat_id]["media"] = not db[chat_id].get("media", True)
        await query.edit_message_reply_markup(reply_markup=get_settings_buttons(chat_id))

    elif query.data == "btn_emoji":
        lang = db.get(chat_id, {}).get("lang", "en")
        db[chat_id]["step"] = "ASK_EMOJI"
        await query.message.reply_text(STRINGS[lang]["ask_emoji"])

# --- MESSAGE ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    user_data = db.get(chat_id, {})
    lang = user_data.get("lang", "en")
    txt = update.message.text.strip()

    if user_data.get("step") == "WAIT_CA":
        try:
            r = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{txt}").json()
            pairs = r.get('pairs', [])
            if not pairs:
                await update.message.reply_text("❌ Pair not found.")
                return
            db[chat_id]["pairs"] = []
            btns = []
            for i, p in enumerate(pairs[:5]):
                db[chat_id]["pairs"].append({"addr": p['pairAddress'], "sym": p['baseToken']['symbol']})
                btns.append([InlineKeyboardButton(f"✅ {p['baseToken']['symbol']} / {p['quoteToken']['symbol']}", callback_data=f"idx_{i}")])
            db[chat_id]["step"] = "SELECT_PAIR"
            await update.message.reply_text("ℹ️ Select Pair:", reply_markup=InlineKeyboardMarkup(btns))
        except: pass
    
    elif user_data.get("step") == "ASK_EMOJI":
        db[chat_id]["emoji"] = txt
        db[chat_id]["step"] = "DONE"
        await update.message.reply_text("✅ OK", reply_markup=get_settings_buttons(chat_id))

if __name__ == '__main__':
    Thread(target=run_web, daemon=True).start()
    app_tg = Application.builder().token(TOKEN).build()
    app_tg.add_handler(CommandHandler("start", start))
    app_tg.add_handler(CommandHandler("add", add_command))
    app_tg.add_handler(CommandHandler(["fiyat", "p"], price_command))
    app_tg.add_handler(CallbackQueryHandler(handle_callback))
    app_tg.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app_tg.run_polling(drop_pending_updates=True)
    
