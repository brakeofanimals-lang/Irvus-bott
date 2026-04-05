import os, requests, asyncio
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

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
filtered_words = []

async def fiyat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        r = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{IRVUS_CA}", timeout=10).json()
        f = r['pairs'][0]['priceUsd']
        await update.message.reply_text(f"💎 **$IRVUS Fiyat:** `${f}`", parse_mode='Markdown')
    except: await update.message.reply_text("❌ Fiyat çekilemedi.")

async def ciz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    p = " ".join(context.args)
    if not p: return await update.message.reply_text("❌ Örn: /ciz aslan")
    await update.message.reply_text(f"🎨 **'{p}'** çiziliyor...")
    url = f"https://image.pollinations.ai/prompt/{p.replace(' ', '%20')}?nologo=true"
    await update.message.reply_photo(photo=url, caption=f"🖼 AI: {p}")

async def filter_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    w = " ".join(context.args).lower()
    if w and w not in filtered_words:
        filtered_words.append(w)
        await update.message.reply_text(f"✅ Filtreye eklendi: {w}")

async def msg_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    for w in filtered_words:
        if w in update.message.text.lower():
            try: await update.message.delete()
            except: pass

if __name__ == '__main__':
    # Web sunucusunu başlat
    Thread(target=run_web, daemon=True).start()
    
    # Modern Application Yapısı (Hata veren yer burasıydı, düzeldi)
    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler(["fiyat", "p"], fiyat))
    application.add_handler(CommandHandler(["ciz", "draw"], ciz))
    application.add_handler(CommandHandler("filter", filter_cmd))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, msg_handler))
    
    print(">>> BOT BASLATILDI")
    application.run_polling(drop_pending_updates=True)
    
