import os
import requests
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Render için basit web sunucusu
app = Flask(__name__)
@app.route('/')
def home(): return "BOT AKTIF", 200

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# AYARLAR
TOKEN = "8621050385:AAGA6wcxbFY2rqJ9gjXVK_JNqsebJvTv_Jo"
IRVUS_CA = "0x31EDA2dfd01c9C65385cCE6099B24b06ef3aE831"

async def fiyat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        r = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{IRVUS_CA}").json()
        f = r['pairs'][0]['priceUsd']
        await update.message.reply_text(f"💎 IRVUS Fiyat: ${f}")
    except: await update.message.reply_text("❌ Hata!")

async def ciz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    p = " ".join(context.args)
    if not p: return await update.message.reply_text("❌ Örn: /ciz aslan")
    await update.message.reply_text("🎨 Çiziliyor...")
    url = f"https://image.pollinations.ai/prompt/{p.replace(' ', '%20')}?nologo=true"
    await update.message.reply_photo(photo=url)

if __name__ == '__main__':
    Thread(target=run_web, daemon=True).start()
    app_tg = Application.builder().token(TOKEN).build()
    app_tg.add_handler(CommandHandler("fiyat", fiyat))
    app_tg.add_handler(CommandHandler("ciz", ciz))
    print("BOT BASLADI")
    app_tg.run_polling(drop_pending_updates=True)
    
