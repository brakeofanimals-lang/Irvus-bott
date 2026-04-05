import os, requests, asyncio
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes

# --- WEB SUNUCUSU ---
app = Flask(__name__)
@app.route('/')
def home(): return "IRVUS BOT AKTIF", 200

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- AYARLAR ---
TOKEN = "8621050385:AAGA6wcxbFY2rqJ9gjXVK_JNqsebJvTv_Jo"
TOKEN_ADRESI = "0x31EDA2dfd01c9C65385cCE6099B24b06ef3aE831"

# --- FONKSİYONLAR ---

async def fiyat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        r = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{TOKEN_ADRESI}", timeout=5).json()
        p = r['pairs'][0]
        msg = f"💎 **$IRVUS Güncel Durum**\n\n💰 Fiyat: `${p.get('priceUsd')}`\n📈 24s: `%{p.get('priceChange', {}).get('h24')}`"
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("📈 Grafik", url=p.get('url'))]])
        await update.message.reply_text(msg, reply_markup=kb, parse_mode='Markdown')
    except:
        await update.message.reply_text("❌ Fiyat verisi şu an çekilemedi.")

async def ciz_arka_plan(update, prompt):
    try:
        # Hugging Face yerine doğrudan hızlı resim motoru kullanıyoruz
        image_url = f"https://image.pollinations.ai/prompt/{prompt.replace(' ', '%20')}?width=1024&height=1024&nologo=true"
        
        # Resmi gönder
        await update.message.reply_photo(photo=image_url, caption=f"🖼 **AI Çizimi:** {prompt}")
    except:
        await update.message.reply_text("❌ Çizim motoruna şu an ulaşılamıyor.")

async def ciz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = " ".join(context.args)
    if not prompt:
        await update.message.reply_text("❌ Örn: `/ciz blue dragon`")
        return
    
    await update.message.reply_text(f"🎨 **'{prompt}'** çiziliyor, saniyeler içinde grupta!")
    # Botu dondurmadan arka planda çizdir
    asyncio.create_task(ciz_arka_plan(update, prompt))

# --- ÇALIŞTIRICI ---
if __name__ == '__main__':
    Thread(target=run_web, daemon=True).start()
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("fiyat", fiyat))
    application.add_handler(CommandHandler("ciz", ciz))
    print(">>> BOT BASLATILDI")
    application.run_polling(drop_pending_updates=True)
    
