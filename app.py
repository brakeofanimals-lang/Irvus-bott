import os, requests, asyncio
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler

app = Flask(__name__)
@app.route('/')
def home(): return "IRVUS PRO V6 ONLINE", 200

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- AYARLAR ---
TOKEN = "8621050385:AAGA6wcxbFY2rqJ9gjXVK_JNqsebJvTv_Jo"
db = {}

# --- DİL PAKETLERİ ---
STRINGS = {
    "tr": {
        "welcome": "🚀 **Irvus Pro Bot'a Hoş Geldiniz!**\n\nSeni ve topluluğunu kripto dünyasında asistanın olarak desteklemeye geldim.",
        "help": "🖼 `/ciz` veya `/draw` -> Resim çizer.\n💰 `/fiyat` veya `/price` -> Verileri getirir.\n⚙️ `/set_token` -> Botu bu gruba kurar.",
        "set_ok": "✅ **Başarılı!** Bu grup için token ayarlandı.",
        "no_token": "❌ Önce `/set_token [kontrat]` ile kurulum yapmalısın.",
        "drawing": "🎨 Hazırlanıyor, saniyeler içinde geliyor...",
        "chart_btn": "📈 Grafiği Gör"
    },
    "en": {
        "welcome": "🚀 **Welcome to Irvus Pro Bot!**\n\nI am here to support you and your community as a crypto assistant.",
        "help": "🖼 `/draw` or `/ai` -> Generates image.\n💰 `/price` or `/p` -> Fetch market data.\n⚙️ `/set_token` -> Setup the bot for this group.",
        "set_ok": "✅ **Success!** Token has been set for this group.",
        "no_token": "❌ Please setup first using `/set_token [CA]`.",
        "drawing": "🎨 Generating image, coming in seconds...",
        "chart_btn": "📈 View Chart"
    }
}

# --- START BUTONLARI (KESİN GÜNCEL LİNK) ---
def get_start_buttons():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🇹🇷 Türkçe", callback_data="lang_tr"), 
         InlineKeyboardButton("🇺🇸 English", callback_data="lang_en")],
        [InlineKeyboardButton("🌐 Web Site", url="https://www.irvustoken.xyz"),
         InlineKeyboardButton("🐦 Twitter (X)", url="https://x.com/IRVUSTOKEN")]
    ])

# --- KOMUTLAR ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Please select your language / Lütfen dil seçiniz:",
        reply_markup=get_start_buttons()
    )

async def handle_lang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = query.data.split("_")[1]
    chat_id = str(query.message.chat_id)
    
    if chat_id not in db: db[chat_id] = {"lang": lang, "ca": None}
    else: db[chat_id]["lang"] = lang
    
    txt = STRINGS[lang]["welcome"] + "\n\n" + STRINGS[lang]["help"]
    await query.edit_message_text(txt, parse_mode='Markdown', reply_markup=get_start_buttons())

async def set_token(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    lang = db.get(chat_id, {}).get("lang", "en")
    if not context.args: return
    
    ca = context.args[0].strip()
    if chat_id not in db: db[chat_id] = {"lang": lang}
    db[chat_id].update({"ca": ca})
    await update.message.reply_text(STRINGS[lang]["set_ok"], parse_mode='Markdown')

async def price_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    lang = db.get(chat_id, {}).get("lang", "en")
    
    if chat_id not in db or not db[chat_id].get("ca"):
        await update.message.reply_text(STRINGS[lang]["no_token"])
        return
    
    try:
        ca = db[chat_id]["ca"]
        r = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{ca}").json()
        p = r['pairs'][0]
        symbol = p['baseToken']['symbol']
        msg = f"💎 **{symbol} Güncel Durum**\n\n💰 Fiyat: `${p['priceUsd']}`\n📈 24s Değişim: `%{p['priceChange']['h24']}`"
        
        kb = InlineKeyboardMarkup([[InlineKeyboardButton(STRINGS[lang]["chart_btn"], url=p['url'])]])
        await update.message.reply_text(msg, reply_markup=kb, parse_mode='Markdown')
    except: await update.message.reply_text("❌ Error.")

async def draw_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    lang = db.get(chat_id, {}).get("lang", "en")
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
    app_tg.add_handler(CommandHandler(["set_token", "setup", "kur"], set_token))
    app_tg.add_handler(CallbackQueryHandler(handle_lang, pattern="^lang_"))
    
    app_tg.run_polling(drop_pending_updates=True)
