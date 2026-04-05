import os, requests, asyncio
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Render'ın botu kapatmaması için basit web sunucusu
app = Flask(__name__)
@app.route('/')
def home(): return "BOT AKTIF", 200

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- AYARLAR ---
# Token'dan sonraki boşlukları kontrol et, tırnak içinde tam olsun
TOKEN = "8621050385:AAGA6wcxbFY2rqJ9gjXVK_JNqsebJvTv_Jo"
IRVUS_CA = "0x31EDA2dfd01c9C65385cCE6099B24b06ef3aE831"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🛡 **Irvus Bot Yayında!**\n\nKomutlar:\n💰 /fiyat\n🎨 /ciz [kelime]")

async def fiyat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        r = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{IRVUS_CA}", timeout=10).json()
        f = r['pairs'][0]['priceUsd']
        await update.message.reply_text(f"💎 **IRVUS Fiyat:** ${f}")
    except:
        await update.message.reply_text("❌ Veri çekilemedi.")

async def ciz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = " ".join(context.args)
    if not prompt:
        await update.message.reply_text("❌ Örn: /ciz aslan")
        return
    await update.message.reply_text(f"🎨 **'{prompt}'** çiziliyor...")
    url = f"https://image.pollinations.ai/prompt/{prompt.replace(' ', '%20')}?nologo=true"
    await update.message.reply_photo(photo=url, caption=f"🖼 AI: {prompt}")

# --- ANA ÇALIŞTIRICI ---
if __name__ == '__main__':
    # Web sunucusunu başlat
    Thread(target=run_web, daemon=True).start()
    
    # Botu oluştur
    application = Application.builder().token(TOKEN).build()
    
    # Komutları ekle
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler(["fiyat", "p"], fiyat))
    application.add_handler(CommandHandler(["ciz", "draw"], ciz))
    
    print(">>> BOT DINLEMEYE BASLADI")
    # drop_pending_updates=True : Bot kapalıyken gelen eski mesajları görmezden gelir, şişmeyi önler.
    application.run_polling(drop_pending_updates=True)
    
