import os, requests, asyncio, json
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters

app = Flask(__name__)
@app.route('/')
def home(): return "IRVUS PRO V31 ONLINE", 200

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

TOKEN = "8621050385:AAGA6wcxbFY2rqJ9gjXVK_JNqsebJvTv_Jo"
BUY_IMAGE = "https://raw.githubusercontent.com/IrvusToken/Logo/main/1000077361.png"

db = {"ca": None, "chat_id": None, "last_vol": 0, "step": None, "pairs": []}

async def track_buys(context: ContextTypes.DEFAULT_TYPE):
    if not db["ca"] or not db["chat_id"]: return
    try:
        r = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{db['ca']}", timeout=5).json()
        p = r['pairs'][0]
        vol = float(p.get('volume', {}).get('h24', 0))
        if db["last_vol"] > 0 and vol > db["last_vol"]:
            diff = vol - db["last_vol"]
            if diff > 10:
                txt = f"🟢 **YENİ ALIM!**\n\n💰 Miktar: `${int(diff):,}`\n💵 Fiyat: `${p['priceUsd']}`"
                await context.bot.send_photo(chat_id=db["chat_id"], photo=BUY_IMAGE, caption=txt)
        db["last_vol"] = vol
    except: pass

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("🇹🇷 Türkçe", callback_data="l_tr"), InlineKeyboardButton("🇺🇸 English", callback_data="l_en")],
                               [InlineKeyboardButton("🌐 Web", url="https://www.irvustoken.xyz"), InlineKeyboardButton("🐦 X", url="https://x.com/IRVUSTOKEN")]])
    await update.message.reply_text("🚀 **Irvus Pro v31 Aktif!**\n\n⚙️ `/add` | 💰 `/fiyat` | 🖼 `/ciz`", reply_markup=kb)

async def price_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not db["ca"]: return await update.message.reply_text("❌ Önce `/add` yapmalısın.")
    try:
        r = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{db['ca']}").json()
        p = r['pairs'][0]
        await update.message.reply_text(f"💎 **{p['baseToken']['symbol']}**\n💰 Fiyat: `${p['priceUsd']}`")
    except: await update.message.reply_text("❌ Hata.")

async def draw_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args: return await update.message.reply_text("❌ Örn: `/ciz aslan` yaz.")
    prompt = " ".join(context.args)
    await update.message.reply_text("🎨 Çiziliyor...")
    img_url = f"https://image.pollinations.ai/prompt/{prompt.replace(' ', '%20')}?nologo=true"
    await update.message.reply_photo(photo=img_url, caption=f"🖼 AI: {prompt}")

async def add_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db["chat_id"] = str(update.effective_chat.id)
    db["step"] = "WAIT_NET"
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("BASE", callback_data="n_base"), InlineKeyboardButton("BSC", callback_data="n_bsc")]])
    await update.message.reply_text("➡️ **Ağ Seçin:**", reply_markup=kb)

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data.startswith("n_"):
        db["step"] = "WAIT_CA"
        await query.edit_message_text("🟡 **Kontrat Adresini (CA) Gönderin:**")
    elif query.data.startswith("idx_"):
        idx = int(query.data.split("_")[1])
        db["ca"] = db["pairs"][idx]["addr"]
        db["step"] = "DONE"
        await query.edit_message_text("✅ **Kurulum Tamamlandı!**")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if db.get("step") == "WAIT_CA":
        ca = update.message.text.strip()
        try:
            r = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{ca}").json()
            pairs = r.get('pairs', [])
            db["pairs"] = [{"addr": p['pairAddress'], "sym": p['baseToken']['symbol']} for p in pairs[:3]]
            btns = [[InlineKeyboardButton(f"✅ {p['baseToken']['symbol']}", callback_data=f"idx_{i}")] for i, p in enumerate(db["pairs"])]
            db["step"] = "SELECT_PAIR"
            await update.message.reply_text("ℹ️ Havuz seçin:", reply_markup=InlineKeyboardMarkup(btns))
        except: pass

if __name__ == '__main__':
    Thread(target=run_web, daemon=True).start()
    app_tg = Application.builder().token(TOKEN).build()
    app_tg.add_handler(CommandHandler("start", start))
    app_tg.add_handler(CommandHandler("add", add_command))
    app_tg.add_handler(CommandHandler(["fiyat", "p"], price_command))
    app_tg.add_handler(CommandHandler(["ciz", "draw"], draw_command))
    app_tg.add_handler(CallbackQueryHandler(handle_callback))
    app_tg.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    if app_tg.job_queue:
        app_tg.job_queue.run_repeating(track_buys, interval=30, first=10)
    app_tg.run_polling(drop_pending_updates=True)
