import os, requests, asyncio
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes

# --- WEB SUNUCUSU (Render'ın botu kapatmaması için) ---
app = Flask(__name__)
@app.route('/')
def home(): return "IRVUS BOT ONLINE", 200

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- AYARLAR ---
TOKEN = "8621050385:AAGA6wcxbFY2rqJ9gjXVK_JNqsebJvTv_Jo"
TOKEN_ADRESI = "0x31EDA2dfd01c9C65385cCE6099B24b06ef3aE831"

# --- FONKSİYONLAR ---

async def fiyat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # DexScreener'dan veri çekme
        r = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{TOKEN_ADRESI}", timeout=8).json()
        if not r.get('pairs'):
            await update.message.reply_text("❌ DexScreener üzerinde veri bulunamadı.")
            return
            
        p = r['pairs'][0]
        fiyat_usd = p.get('priceUsd', '0')
        degisim = p.get('priceChange', {}).get('h24', '0')
        mcap = p.get('fdv', 0)
        
        msg = (f"💎 **$IRVUS Güncel Durum**\n\n"
               f"💰 Fiyat: `${fiyat_usd}`\n"
               f"📈 24s Değişim: `%{degisim}`\n"
               f"💠 Market Cap: `${int(mcap):,}`")
        
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("📈 Grafiği Gör", url=p.get('url'))]])
        await update.message.reply_text(msg, reply_markup=kb, parse_mode='Markdown')
    except Exception as e:
        await update.message.reply_text(f"❌ Fiyat şu an çekilemiyor.")

async def ciz_arka_plan(update, prompt):
    try:
        # Hızlı resim motoru (Pollinations)
        image_url = f"https://image.pollinations.ai/prompt/{prompt.replace(' ', '%20')}?width=1024&height=1024&nologo=true"
        await update.message.reply_photo(photo=image_url, caption=f"🖼 **AI Çizimi:** {prompt}")
    except:
        await update.message.reply_text("❌ Çizim motoru yanıt vermedi.")

async def ciz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = " ".join(context.args)
    if not prompt:
        await update.message.reply_text("❌ Lütfen ne çizmem gerektiğini yazın.\nÖrn: `/ciz savaşçı bir aslan`")
        return
    
    await update.message.reply_text(f"🎨 **'{prompt}'** çiziliyor, lütfen bekleyin...")
    # Çizimi botu dondurmadan arka planda yap
    asyncio.create_task(ciz_arka_plan(update, prompt))

# --- ANA ÇALIŞTIRICI ---
def main():
    # 1. Web sunucusunu başlat
    Thread(target=run_web, daemon=True).start()
    
    # 2. Botu yeni sistemle (Application) kur
    application = Application.builder().token(TOKEN).build()
    
    # 3. Komutları ekle
    application.add_handler(CommandHandler(["fiyat", "p", "price"], fiyat))
    application.add_handler(CommandHandler(["ciz", "draw"], ciz))
    application.add_handler(CommandHandler("start", fiyat)) # Start basınca fiyat gelsin
    
    # 4. Botu çalıştır
    print(">>> IRVUS BOT YAYINDA!")
    application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
    
