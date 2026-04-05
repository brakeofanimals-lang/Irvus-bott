import os, requests, asyncio
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# --- WEB SUNUCUSU ---
app = Flask(__name__)
@app.route('/')
def home(): return "IRVUS BOT ONLINE", 200

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- AYARLAR ---
TOKEN = "8621050385:AAESXIZLT6HbS3CGeT-sT-HJcgvFuJF8ff0"
IRVUS_CA = "0x31EDA2dfd01c9C65385cCE6099B24b06ef3aE831"

# --- KOMUTLAR ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🛡 **Irvus Bot Aktif!**\n\n💰 /fiyat\n🎨 /ciz [kelime]")

async def fiyat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        r = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{IRVUS_CA}", timeout=8).json()
        f = r['pairs'][0]['priceUsd']
        await update.message.reply_text(f"💎 **Fiyat:** `${f}`", parse_mode='Markdown')
    except:
        await update.message.reply_text("❌ Fiyat şu an çekilemedi.")

async def ciz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = " ".join(context.args)
    if not prompt:
        await update.message.reply_text("❌ Örn: /ciz aslan")
        return
    await update.message.reply_text(f"🎨 **'{prompt}'** çiziliyor...")
    try:
        url = f"https://image.pollinations.ai/prompt/{prompt.replace(' ', '%20')}?nologo=true"
        await update.message.reply_photo(photo=url, caption=f"🖼 AI: {prompt}")
    except:
        await update.message.reply_text("❌ Çizim hatası.")

# --- ANA ÇALIŞTIRICI ---
if __name__ == '__main__':
    # 1. Web sunucusunu başlat (Render kapanmasın)
    Thread(target=run_web, daemon=True).start()
    
    # 2. Bot uygulamasını kur (Modern ve En Sade Yapı)
    application = Application.builder().token(TOKEN).build()
    
    # 3. Komutları ekle
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler(["fiyat", "p"], fiyat))
    application.add_handler(CommandHandler(["ciz", "draw"], ciz))
    
    # 4. Botu başlat
    print(">>> BOT DINLEMEYE BASLADI")
    # run_polling() kendi içinde döngüyü otomatik yönetir, hata vermez.
    application.run_polling(drop_pending_updates=True)
    
