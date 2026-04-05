import os, requests, asyncio
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

# --- WEB SUNUCUSU ---
app = Flask(__name__)
@app.route('/')
def home(): return "IRVUS CORE V1 ONLINE", 200

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- AYARLAR ---
TOKEN = "8621050385:AAGA6wcxbFY2rqJ9gjXVK_JNqsebJvTv_Jo"
IRVUS_CA = "0x31EDA2dfd01c9C65385cCE6099B24b06ef3aE831"

# Yasaklı kelimeler (Başlangıçta boş)
filtered_words = []

# --- KOMUTLAR ---

async def fiyat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        r = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{IRVUS_CA}", timeout=8).json()
        if not r.get('pairs'): return
        p = r['pairs'][0]
        msg = (f"💎 **$IRVUS Güncel Durum**\n\n"
               f"💰 Fiyat: `${p.get('priceUsd')}`\n"
               f"📈 24s Değişim: `%{p.get('priceChange', {}).get('h24')}`\n"
               f"💠 Market Cap: `${int(p.get('fdv', 0)):,}`")
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("📈 Grafik", url=p.get('url'))]])
        await update.message.reply_text(msg, reply_markup=kb, parse_mode='Markdown')
    except:
        await update.message.reply_text("❌ Fiyat verisi şu an çekilemedi.")

async def ciz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = " ".join(context.args)
    if not prompt:
        await update.message.reply_text("❌ Örn: `/ciz warrior` yazmalısın.")
        return
    await update.message.reply_text(f"🎨 **'{prompt}'** çiziliyor, lütfen bekleyin...")
    try:
        url = f"https://image.pollinations.ai/prompt/{prompt.replace(' ', '%20')}?nologo=true"
        await update.message.reply_photo(photo=url, caption=f"🖼 AI: {prompt}")
    except:
        await update.message.reply_text("❌ Çizim motoru hatası.")

async def filter_word(update: Update, context: ContextTypes.DEFAULT_TYPE):
    word = " ".join(context.args).lower()
    if not word:
        await update.message.reply_text("❌ Örn: `/filter kelime` yazmalısın.")
        return
    if word not in filtered_words:
        filtered_words.append(word)
        await update.message.reply_text(f"✅ **'{word}'** kelimesi filtreye eklendi.")

async def message_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    text = update.message.text.lower()
    for word in filtered_words:
        if word in text:
            try:
                await update.message.delete()
            except: pass

# --- ANA ÇALIŞTIRICI ---
def main():
    # Portu dinlemek için sunucuyu başlat
    Thread(target=run_web, daemon=True).start()
    
    # Modern bot sistemi
    application = Application.builder().token(TOKEN).build()
    
    # Komutları ekle
    application.add_handler(CommandHandler(["fiyat", "p"], fiyat))
    application.add_handler(CommandHandler(["ciz", "draw"], ciz))
    application.add_handler(CommandHandler("filter", filter_word))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_check))
    
    print(">>> BOT BASLATILDI")
    application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
    
