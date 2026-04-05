import os, requests, asyncio
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Render'ın botu kapatmaması için web sunucusu
app = Flask(__name__)
@app.route('/')
def home(): return "IRVUS BOT YAYINDA", 200

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- AYARLAR ---
# Yeni Token'ın buraya eklendi
TOKEN = "8621050385:AAESXIZLT6HbS3CGeT-sT-HJcgvFuJF8ff0"
IRVUS_CA = "0x31EDA2dfd01c9C65385cCE6099B24b06ef3aE831"

# --- KOMUTLAR ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🛡 **Irvus Bot Yeni Token ile Aktif!**\n\n"
        "💰 /fiyat - Güncel Irvus fiyatı\n"
        "🎨 /ciz [kelime] - AI Çizim yapar"
    )

async def fiyat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        r = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{IRVUS_CA}", timeout=10).json()
        if not r.get('pairs'):
            await update.message.reply_text("❌ DexScreener verisi bulunamadı.")
            return
        f = r['pairs'][0]['priceUsd']
        await update.message.reply_text(f"💎 **IRVUS Fiyat:** `${f}`", parse_mode='Markdown')
    except Exception as e:
        await update.message.reply_text("❌ Fiyat şu an çekilemiyor.")

async def ciz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = " ".join(context.args)
    if not prompt:
        await update.message.reply_text("❌ Örn: `/ciz yeşil savaşçı` yazmalısın.")
        return
    
    await update.message.reply_text(f"🎨 **'{prompt}'** çiziliyor, lütfen bekleyin...")
    try:
        # Pollinations AI motoru
        url = f"https://image.pollinations.ai/prompt/{prompt.replace(' ', '%20')}?nologo=true"
        await update.message.reply_photo(photo=url, caption=f"🖼 AI: {prompt}")
    except:
        await update.message.reply_text("❌ Çizim motoru şu an meşgul.")

# --- ANA ÇALIŞTIRICI ---
if __name__ == '__main__':
    # Web sunucusunu başlat
    Thread(target=run_web, daemon=True).start()
    
    # Botu modern sistemle kur
    application = Application.builder().token(TOKEN).build()
    
    # Komutları tanımla
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler(["fiyat", "p"], fiyat))
    application.add_handler(CommandHandler(["ciz", "draw"], ciz))
    
    print(">>> BOT YENI TOKEN ILE DINLEMEDE...")
    # Eski bekleyen mesajları temizleyerek başla
    application.run_polling(drop_pending_updates=True)
    
