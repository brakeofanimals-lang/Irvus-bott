import os, requests, asyncio
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler

app = Flask(__name__)
@app.route('/')
def home(): return "IRVUS PRO V9 - BUY BOT READY", 200

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- AYARLAR ---
TOKEN = "8621050385:AAGA6wcxbFY2rqJ9gjXVK_JNqsebJvTv_Jo"
db = {} # Hafıza: { chat_id: {"ca": "...", "lang": "tr", "last_vol": 0} }

STRINGS = {
    "tr": {
        "welcome": "🚀 **Irvus Pro Bot'a Hoş Geldiniz!**\n\nSeni ve topluluğunu kripto dünyasında asistanın olarak desteklemeye geldim.",
        "help": "🖼 `/ciz` -> Resim çizer.\n💰 `/fiyat` -> Verileri getirir.\n⚙️ `/kur` -> Botu kurar.",
        "set_ok": "✅ **Başarılı!** Bu grup için token ayarlandı. Alımlar takip ediliyor!",
        "no_token": "❌ Önce `/kur [kontrat]` ile kurulum yapmalısın.",
        "drawing": "🎨 Hazırlanıyor...",
        "buy_title": "🚀 **YENİ ALIM GELDİ!** 🚀\n🟢🟢🟢🟢🟢🟢🟢🟢🟢\n\n"
    },
    "en": {
        "welcome": "🚀 **Welcome to Irvus Pro Bot!**",
        "help": "🖼 `/draw` -> AI Image.\n💰 `/price` -> Market Data.\n⚙️ `/setup` -> Setup Bot.",
        "set_ok": "✅ **Success!** Token set. Monitoring buys!",
        "no_token": "❌ Please setup first using `/setup [CA]`.",
        "drawing": "🎨 Drawing...",
        "buy_title": "🚀 **NEW BUY!** 🚀\n🟢🟢🟢🟢🟢🟢🟢🟢🟢\n\n"
    }
}

# --- ALIM TARAYICI (ARKA PLAN) ---
async def check_buys(context: ContextTypes.DEFAULT_TYPE):
    for chat_id, data in db.items():
        if not data.get("ca"): continue
        try:
            ca = data["ca"]
            r = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{ca}", timeout=10).json()
            p = r['pairs'][0]
            vol = float(p.get('volume', {}).get('h24', 0))
            
            # Eğer hacim arttıysa alım gelmiştir (Basit hacim takibi)
            if data["last_vol"] > 0 and vol > data["last_vol"]:
                lang = data.get("lang", "tr") # Varsayılan Türkçe
                price = p['priceUsd']
                mcap = f"{int(p.get('fdv', 0)):,}"
                
                text = (
                    f"{STRINGS[lang]['buy_title']}"
                    f"💰 **Fiyat:** `${price}`\n"
                    f"💎 **MCAP:** `${mcap}`\n"
                    f"📊 **24s Hacim:** `${int(vol):,}`"
                )
                kb = InlineKeyboardMarkup([[InlineKeyboardButton("📈 Chart / Grafik", url=p['url'])]])
                await context.bot.send_message(chat_id=chat_id, text=text, reply_markup=kb, parse_mode='Markdown')
            
            db[chat_id]["last_vol"] = vol
        except: continue

# --- KOMUTLAR ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🇹🇷 Türkçe", callback_data="lang_tr"), InlineKeyboardButton("🇺🇸 English", callback_data="lang_en")],
        [InlineKeyboardButton("🌐 Web Site", url="https://www.irvustoken.xyz"), InlineKeyboardButton("🐦 Twitter", url="https://x.com/IRVUSTOKEN")]
    ])
    await update.message.reply_text("Lütfen Dil Seçin / Select Language:", reply_markup=kb)

async def handle_lang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = query.data.split("_")[1]
    chat_id = str(query.message.chat_id)
    if chat_id not in db: db[chat_id] = {"lang": lang, "ca": None, "last_vol": 0}
    else: db[chat_id]["lang"] = lang
    await query.edit_message_text(STRINGS[lang]["welcome"] + "\n\n" + STRINGS[lang]["help"], parse_mode='Markdown')

async def set_token(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    if not context.args: return
    ca = context.args[0].strip()
    lang = db.get(chat_id, {}).get("lang", "tr")
    db[chat_id] = {"ca": ca, "lang": lang, "last_vol": 0}
    await update.message.reply_text(STRINGS[lang]["set_ok"], parse_mode='Markdown')

async def price_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    lang = db.get(chat_id, {}).get("lang", "tr")
    if chat_id not in db or not db[chat_id].get("ca"):
        await update.message.reply_text(STRINGS[lang]["no_token"])
        return
    try:
        ca = db[chat_id]["ca"]
        r = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{ca}").json()
        p = r['pairs'][0]
        msg = f"💎 **{p['baseToken']['symbol']}**\n💰 Fiyat: `${p['priceUsd']}`\n📈 24s: `%{p['priceChange']['h24']}`"
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("📈 Grafik", url=p['url'])]])
        await update.message.reply_text(msg, reply_markup=kb, parse_mode='Markdown')
    except: pass

async def draw_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    lang = db.get(chat_id, {}).get("lang", "tr")
    prompt = " ".join(context.args)
    if not prompt: return
    await update.message.reply_text(STRINGS[lang]["drawing"])
    img = f"https://image.pollinations.ai/prompt/{prompt.replace(' ', '%20')}?width=1024&height=1024&nologo=true"
    await update.message.reply_photo(photo=img, caption=f"🖼 AI: {prompt}")

if __name__ == '__main__':
    Thread(target=run_web, daemon=True).start()
    app_tg = Application.builder().token(TOKEN).build()
    
    app_tg.add_handler(CommandHandler("start", start))
    app_tg.add_handler(CommandHandler(["fiyat", "price", "p"], price_command))
    app_tg.add_handler(CommandHandler(["ciz", "draw", "ai"], draw_command))
    app_tg.add_handler(CommandHandler(["kur", "setup", "set_token"], set_token))
    app_tg.add_handler(CallbackQueryHandler(handle_lang, pattern="^lang_"))
    
    # 30 saniyede bir alımları kontrol et
    app_tg.job_queue.run_repeating(check_buys, interval=30, first=10)
    
    app_tg.run_polling(drop_pending_updates=True)
    
