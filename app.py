import os, requests, asyncio
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

app = Flask(__name__)
@app.route('/')
def home(): return "IRVUS AKTIF", 200

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- AYARLAR ---
TOKEN = "8621050385:AAESXIZLT6HbS3CGeT-sT-HJcgvFuJF8ff0"
IRVUS_CA = "0x31EDA2dfd01c9C65385cCE6099B24b06ef3aE831"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🛡 **BOT UYANDI!**\n\n💰 /fiyat\n🎨 /ciz")

async def fiyat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        r = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{IRVUS_CA}").json()
        f = r['pairs'][0]['priceUsd']
        await update.message.reply_text(f"💎 **Fiyat:** ${f}")
    except: await update.message.reply_text("❌ Hata")

async def ciz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    p = " ".join(context.args)
    if not p: return await update.message.reply_text("❌ Kelime yaz.")
    url = f"https://image.pollinations.ai/prompt/{p.replace(' ', '%20')}?nologo=true"
    await update.message.reply_photo(photo=url, caption=f"🖼 AI: {p}")

async def wake_up():
    """Botun üzerindeki tüm eski takılmaları siler ve başlatır"""
    application = Application.builder().token(TOKEN).build()
    
    # KRİTİK: Eski webhook varsa siler
    await application.bot.delete_webhook(drop_pending_updates=True)
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler(["fiyat", "p"], fiyat))
    application.add_handler(CommandHandler(["ciz", "draw"], ciz))
    
    print(">>> BOT DINLEMEYE BASLADI")
    await application.initialize()
    await application.start()
    await application.updater.start_polling(drop_pending_updates=True)

if __name__ == '__main__':
    Thread(target=run_web, daemon=True).start()
    # Botu asenkron döngüde başlat
    loop = asyncio.get_event_loop()
    loop.run_until_complete(wake_up())
    loop.run_forever()
    
