import os, requests, asyncio
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes

app = Flask(__name__)
@app.route('/')
def home(): return "OK", 200

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# AYARLAR
TOKEN = "8621050385:AAGA6wcxbFY2rqJ9gjXVK_JNqsebJvTv_Jo"
TOKEN_ADRESI = "0x31EDA2dfd01c9C65385cCE6099B24b06ef3aE831"

async def fiyat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        r = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{TOKEN_ADRESI}", timeout=5).json()
        p = r['pairs'][0]
        msg = f"💎 **$IRVUS Güncel Durum**\n\n💰 Fiyat: `${p.get('priceUsd')}`\n📈 24s: `%{p.get('priceChange', {}).get('h24')}`"
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("📈 Grafik", url=p.get('url'))]])
        await update.message.reply_text(msg, reply_markup=kb, parse_mode='Markdown')
    except: await update.message.reply_text("❌ Fiyat şu an çekilemiyor.")

async def ciz_arka_plan(update, prompt):
    try:
        # Daha hızlı ve sorunsuz servis: Pollinations
        image_url = f"https://image.pollinations.ai/prompt/{prompt.replace(' ', '%20')}?width=1024&height=1024&nologo=true"
        
        # Resmi Telegram'a gönder
        await update.message.reply_photo(photo=image_url, caption=f"🖼 **AI Sonucu:** {prompt}")
    except Exception as e:
        await update.message.reply_text("❌ Çizim sırasında bir hata oluştu.")

async def ciz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = " ".join(context.args)
    if not prompt:
        await update.message.reply_text("❌ Kullanım: /ciz araba")
        return
    
    await update.message.reply_text(f"🎨 **'{prompt}'** çiziliyor... Saniyeler içinde geliyor!")
    asyncio.create_task(ciz_arka_plan(update, prompt))

if __name__ == '__main__':
    Thread(target=run_web, daemon=True).start()
    bot = Application.builder().token(TOKEN).build()
    bot.add_handler(CommandHandler("fiyat", fiyat))
    bot.add_handler(CommandHandler("ciz", ciz))
    bot.run_polling(drop_pending_updates=True)
    
