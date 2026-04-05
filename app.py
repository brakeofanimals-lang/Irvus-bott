import os, requests, asyncio, json
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters

app = Flask(__name__)
@app.route('/')
def home(): return "IRVUS V29 ONLINE", 200

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

TOKEN = "8621050385:AAGA6wcxbFY2rqJ9gjXVK_JNqsebJvTv_Jo"
# Senin gönderdiğin Irvus logosu
BUY_IMAGE = "https://raw.githubusercontent.com/IrvusToken/Logo/main/1000077361.png" 

# Basit bir dosya tabanlı hafıza
def load_db():
    try:
        with open("db.json", "r") as f: return json.load(f)
    except: return {}

def save_db(data):
    with open("db.json", "w") as f: json.dump(data, f)

db = load_db()

# --- ALIM TAKİPÇİSİ (SNIPER) ---
async def track_buys(context: ContextTypes.DEFAULT_TYPE):
    global db
    if not db.get("ca") or not db.get("chat_id"): return
    
    try:
        url = f"https://api.dexscreener.com/latest/dex/tokens/{db['ca']}"
        r = requests.get(url, timeout=10).json()
        if not r.get('pairs'): return
        
        p = r['pairs'][0]
        vol = float(p.get('volume', {}).get('h24', 0))
        
        if db.get("last_vol", 0) > 0 and vol > db["last_vol"]:
            diff = vol - db["last_vol"]
            if diff > 10: # 10$ üstü alımları göster
                msg = f"🟢 **YENİ ALIM (NEW BUY)!**\n\n💰 Miktar: `${int(diff):,}`\n💵 Fiyat: `${p['priceUsd']}`\n💎 Market Cap: `${int(p.get('fdv', 0)):,}`"
                # Senin attığın logoyu mesajla gönderiyoruz
                await context.bot.send_photo(chat_id=db["chat_id"], photo=BUY_IMAGE, caption=msg, parse_mode='Markdown')
        
        db["last_vol"] = vol
        save_db(db)
    except Exception as e:
        print(f"Sniper Hatası: {e}")

# --- KOMUTLAR ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🇹🇷 Türkçe", callback_data="l_tr"), InlineKeyboardButton("🇺🇸 English", callback_data="l_en")],
        [InlineKeyboardButton("🌐 Web", url="https://www.irvustoken.xyz"), InlineKeyboardButton("🐦 X", url="https://x.com/IRVUSTOKEN")]
    ])
    await update.message.reply_text("🚀 **Irvus Pro Aktif!**\n\n⚙️ `/add` | 💰 `/fiyat` | 🖼 `/ciz`", reply_markup=kb)

async def add_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    db.update({"chat_id": chat_id, "step": "WAIT_NET", "pairs": []})
    save_db(db)
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("ETH", callback_data="n_eth"), InlineKeyboardButton("BSC", callback_data="n_bsc"), InlineKeyboardButton("BASE", callback_data="n_base")]])
    await update.message.reply_text("➡️ **Ağ Seçin (Select Chain):**", reply_markup=kb)

async def price_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not db.get("ca"): return await update.message.reply_text("❌ Önce `/add` yapın.")
    try:
        r = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{db['ca']}").json()
        p = r['pairs'][0]
        await update.message.reply_text(f"💎 **{p['baseToken']['symbol']}**\n💰 Fiyat: `${p['priceUsd']}`\n📊 24s: %{p['priceChange']['h24']}")
    except: await update.message.reply_text("❌ Hata!")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data.startswith("l_"):
        await query.edit_message_text("✅ Dil ayarlandı. Kurulum için `/add` yazın.")
    elif query.data.startswith("n_"):
        db["step"] = "WAIT_CA"
        save_db(db)
        await query.edit_message_text(f"🟡 **{query.data[2:].upper()} Kontrat Adresini Atın:**")
    elif query.data.startswith("idx_"):
        idx = int(query.data.split("_")[1])
        pair = db["pairs"][idx]
        db.update({"ca": pair['addr'], "step": "DONE", "last_vol": 0})
        save_db(db)
        await query.edit_message_text(f"✅ **{pair['sym']}** Başarıyla kuruldu! Alımlar takip ediliyor.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if db.get("step") == "WAIT_CA":
        ca = update.message.text.strip()
        try:
            r = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{ca}").json()
            pairs = r.get('pairs', [])
            db["pairs"] = [{"addr": p['pairAddress'], "sym": p['baseToken']['symbol']} for p in pairs[:3]]
            save_db(db)
            btns = [[InlineKeyboardButton(f"✅ {p['baseToken']['symbol']}", callback_data=f"idx_{i}")] for i, p in enumerate(db["pairs"])]
            db["step"] = "SELECT_PAIR"
            save_db(db)
            await update.message.reply_text("ℹ️ Havuz seçin:", reply_markup=InlineKeyboardMarkup(btns))
        except: pass

if __name__ == '__main__':
    Thread(target=run_web, daemon=True).start()
    app_tg = Application.builder().token(TOKEN).build()
    app_tg.add_handler(CommandHandler("start", start))
    app_tg.add_handler(CommandHandler("add", add_command))
    app_tg.add_handler(CommandHandler(["fiyat", "p"], price_command))
    app_tg.add_handler(CallbackQueryHandler(handle_callback))
    app_tg.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    if app_tg.job_queue:
        app_tg.job_queue.run_repeating(track_buys, interval=30, first=10)
        
    app_tg.run_polling(drop_pending_updates=True)
    
