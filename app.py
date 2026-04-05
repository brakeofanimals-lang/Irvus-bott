import os, requests, asyncio
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Render Portu için Web Sunucusu
app = Flask(__name__)
@app.route('/')
def home(): return "IRVUS AKTIF", 200

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# AYARLAR
TOKEN = "8621050385:AAESXIZLT6HbS3CGeT-sT-HJcgvFuJF8ff0"
IRVUS_CA = "0x31EDA2dfd01c9C65385cCE6099B24b06ef3aE831"

async def fiyat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        r = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{IRVUS_CA}", timeout=10).json()
        f = r['pairs'][0]['priceUsd']
        await update.message.reply_text(f"💎 **$IRVUS Fiyat:** `${f}`", parse_mode='Markdown')
    except: await update.message.reply_text("❌ Fiyat şu an çekilemiyor.")

async def ciz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    p = " ".join(context.args)
    if not p: return await update.message.reply_text("❌ Örn: /ciz aslan")
    await update.message.reply_text(f"🎨 **'{p}'** çiziliyor...")
    url = f"https://image.pollinations.ai/prompt/{p.replace(' ', '%20')}?nologo=true"
    await update.message.reply_photo(photo=url, caption=f"🖼 AI: {p}")

if __name__ == '__main__':
    Thread(target=run_web, daemon=True).start()
    
    # Modern Application Yapısı
    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler(["fiyat", "p"], fiyat))
    application.add_handler(CommandHandler(["ciz", "draw"], ciz))
    
    print(">>> BOT BASLATILDI")
    application.run_polling(drop_pending_updates=True)
    
