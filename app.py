import os, requests, asyncio
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters

app = Flask(__name__)
@app.route('/')
def home(): return "IRVUS ENGINE V26 ONLINE", 200

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

TOKEN = "8621050385:AAGA6wcxbFY2rqJ9gjXVK_JNqsebJvTv_Jo"
db = {} # { chat_id: {"ca": "...", "emoji": "🟢", "min_buy": 0, "media": True, "last_vol": 0} }

def get_settings_buttons(chat_id):
    data = db.get(chat_id, {})
    emoji = data.get("emoji", "🟢")
    min_buy = data.get("min_buy", "0")
    media = "🚫" if not data.get("media", True) else "🖼"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"{media} Gif / Image", callback_data="act_media"), InlineKeyboardButton(f"⬆️ Min Buy ${min_buy}", callback_data="act_min")],
        [InlineKeyboardButton(f"{emoji} Buy Emoji", callback_data="act_emoji"), InlineKeyboardButton("💰 Buy Step $10", callback_data="act_step")],
        [InlineKeyboardButton("⚙️ Group Settings", callback_data="act_group")],
        [InlineKeyboardButton("🔹 Premium (Ad-Free) 🔹", url="https://www.irvustoken.xyz")]
    ])

# --- ALIM SNIPER ---
async def track_buys(context: ContextTypes.DEFAULT_TYPE):
    for chat_id, data in db.items():
        if not data.get("ca"): continue
        try:
            r = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{data['ca']}", timeout=5).json()
            p = r['pairs'][0]
            vol = float(p.get('volume', {}).get('h24', 0))
            if data.get("last_vol", 0) > 0 and vol > data["last_vol"]:
                diff = vol - data["last_vol"]
                if diff >= float(data.get("min_buy", 0)):
                    txt = f"🚀 **NEW BUY!**\n{data.get('emoji','🟢')*5}\n\n💰 Price: `${p['priceUsd']}`\n📊 Vol: `${int(diff):,}`"
                    await context.bot.send_message(chat_id, txt, parse_mode='Markdown')
            db[chat_id]["last_vol"] = vol
        except: continue

# --- KOMUTLAR ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("🇹🇷 Türkçe", callback_data="l_tr"), InlineKeyboardButton("🇺🇸 English", callback_data="l_en")]])
    await update.message.reply_text("🚀 **Irvus Pro Online!**\n\n🖼 `/ciz` | 💰 `/fiyat` | ⚙️ `/add`", reply_markup=kb)

async def price_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    ca = db.get(chat_id, {}).get("ca")
    if not ca: return await update.message.reply_text("❌ Önce `/add` yapmalısın.")
    try:
        r = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{ca}").json()
        p = r['pairs'][0]
        await update.message.reply_text(f"💎 **{p['baseToken']['symbol']}**\n💰 Price: `${p['priceUsd']}`\n📊 24h: %{p['priceChange']['h24']}")
    except: await update.message.reply_text("❌ Hata.")

async def draw_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    p = " ".join(context.args)
    if not p: return
    await update.message.reply_text("🎨 Drawing...")
    await update.message.reply_photo(f"https://image.pollinations.ai/prompt/{p.replace(' ','%20')}?nologo=true")

async def add_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    db[chat_id] = db.get(chat_id, {"emoji": "🟢", "min_buy": 0, "media": True})
    db[chat_id]["step"] = "WAIT_NET"
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("ETH", callback_data="n_eth"), InlineKeyboardButton("BSC", callback_data="n_bsc"), InlineKeyboardButton("BASE", callback_data="n_base")]])
    await update.message.reply_text("➡️ **Select Chain:**", reply_markup=kb)

# --- CALLBACKS ---
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    chat_id = str(query.message.chat_id)
    await query.answer()

    if query.data.startswith("n_"):
        db[chat_id]["step"] = "WAIT_CA"
        await query.edit_message_text(f"🟡 **{query.data[2:].upper()} Token Address?**")
    elif query.data.startswith("idx_"):
        idx = int(query.data.split("_")[1])
        pair = db[chat_id]["pairs"][idx]
        db[chat_id].update({"ca": pair['addr'], "step": "DONE", "last_vol": 0})
        await query.edit_message_text(f"✅ **{pair['sym']}** Setup Done!", reply_markup=get_settings_buttons(chat_id))
    elif query.data == "act_media":
        db[chat_id]["media"] = not db[chat_id].get("media", True)
        await query.edit_message_reply_markup(reply_markup=get_settings_buttons(chat_id))
    elif query.data == "act_emoji":
        db[chat_id]["step"] = "ASK_EMOJI"
        await query.message.reply_text("✨ Send the new emoji:")
    elif query.data == "act_min":
        db[chat_id]["step"] = "ASK_MIN"
        await query.message.reply_text("💰 Enter min buy amount ($):")

# --- MESSAGES ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    user_data = db.get(chat_id, {})
    txt = update.message.text.strip()

    if user_data.get("step") == "WAIT_CA":
        try:
            r = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{txt}").json()
            pairs = r.get('pairs', [])
            db[chat_id]["pairs"] = [{"addr": p['pairAddress'], "sym": p['baseToken']['symbol']} for p in pairs[:5]]
            btns = [[InlineKeyboardButton(f"✅ {p['baseToken']['symbol']}", callback_data=f"idx_{i}")] for i, p in enumerate(pairs[:5])]
            db[chat_id]["step"] = "SELECT_PAIR"
            await update.message.reply_text("ℹ️ Select Pair:", reply_markup=InlineKeyboardMarkup(btns))
        except: await update.message.reply_text("❌ Error.")
    elif user_data.get("step") == "ASK_EMOJI":
        db[chat_id].update({"emoji": txt, "step": "DONE"})
        await update.message.reply_text(f"✅ Emoji: {txt}", reply_markup=get_settings_buttons(chat_id))
    elif user_data.get("step") == "ASK_MIN":
        db[chat_id].update({"min_buy": txt, "step": "DONE"})
        await update.message.reply_text(f"✅ Min Buy: ${txt}", reply_markup=get_settings_buttons(chat_id))

if __name__ == '__main__':
    Thread(target=run_web, daemon=True).start()
    app_tg = Application.builder().token(TOKEN).build()
    app_tg.add_handler(CommandHandler("start", start))
    app_tg.add_handler(CommandHandler("add", add_command))
    app_tg.add_handler(CommandHandler(["fiyat", "p"], price_command))
    app_tg.add_handler(CommandHandler(["ciz", "draw"], draw_command))
    app_tg.add_handler(CallbackQueryHandler(handle_callback))
    app_tg.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app_tg.job_queue.run_repeating(track_buys, interval=30, first=10)
    app_tg.run_polling(drop_pending_updates=True)
            
