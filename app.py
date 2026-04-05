import os, requests, asyncio
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes

# --- WEB SUNUCUSU (Render İçin) ---
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
        image_url = f"https://image.pollinations.ai/prompt/{prompt.replace(' ', '%20')}?width=1024&height=1024&nologo=true"
        await update.message.reply_photo(photo=image_url, caption=f"🖼 **AI Çizimi:** {prompt}")
    except:
        await update.message.reply_text("❌ Çizim motoruna şu an ulaşılamıyor.")

async def ciz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = " ".join(context.args)
    if not prompt:
        await update.message.reply_text("❌ Örn: `/ciz blue dragon` yazmalısın.")
        return
    await update.message.reply_text(f"🎨 **'{prompt}'** çiziliyor...")
    asyncio.create_task(ciz_arka_plan(update, prompt))

# --- ANA ÇALIŞTIRICI (MODERN YAPI) ---
def main():
    # Web sunucusunu başlat
    Thread(target=run_web, daemon=True).start()
    
    # Yeni nesil Application başlatma
    application = Application.builder().token(TOKEN).build()
    
    # Komutları ekle
    application.add_handler(CommandHandler(["fiyat", "p", "price"], fiyat))
    application.add_handler(CommandHandler(["ciz", "draw"], ciz))
    
    print(">>> BOT BAŞLATILDI")
    application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
    
