import os, requests, asyncio
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes

# --- 1. RENDER WEB KAPI ---
app = Flask(__name__)
@app.route('/')
def home(): return "IRVUS BOT ONLINE", 200

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- 2. AYARLAR ---
TOKEN = "8621050385:AAGA6wcxbFY2rqJ9gjXVK_JNqsebJvTv_Jo"
TOKEN_ADRESI = "0x31EDA2dfd01c9C65385cCE6099B24b06ef3aE831"
HF_TOKEN = "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"

# En az 'meşgul' hatası veren ve hızlı uyanan model:
API_URL = "https://api-inference.huggingface.co/models/Lykon/dreamshaper-8"

# --- 3. FONKSİYONLAR ---

async def fiyat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fiyatı botu dondurmadan çeker."""
    try:
        # Dexscreener'dan veri çek
        r = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{TOKEN_ADRESI}", timeout=5).json()
        p = r['pairs'][0]
        fiyat_usd = p.get('priceUsd', '0.00')
        degisim = p.get('priceChange', {}).get('h24', '0.00')
        
        msg = f"💎 **$IRVUS Güncel Durum**\n\n💰 Fiyat: `${fiyat_usd}`\n📈 24s Değişim: `%{degisim}`"
        
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("📈 Grafik (DexScreener)", url=p.get('url'))]])
        await update.message.reply_text(msg, reply_markup=kb, parse_mode='Markdown')
    except Exception:
        await update.message.reply_text("❌ Fiyat verisi şu an çekilemedi, lütfen tekrar deneyin.")

async def ciz_arka_plan(update, prompt):
    """Resmi arka planda çizer, fiyat komutunu engellemez."""
    try:
        headers = {"Authorization": f"Bearer {HF_TOKEN}"}
        # wait_for_model: True ile Hugging Face'in uyanmasını bekliyoruz
        payload = {"inputs": prompt, "options": {"wait_for_model": True}}
        
        res = requests.post(API_URL, headers=headers, json=payload, timeout=120)
        
        if res.status_code == 200:
            await update.message.reply_photo(photo=res.content, caption=f"🖼 **AI Sonucu:** {prompt}")
        else:
            # Hugging Face hala meşgul yanıtı verirse
            await update.message.reply_text("💤 AI şu an çok yoğun veya uyanamadı. 1-2 dakika sonra tekrar deneyin.")
    except Exception:
        await update.message.reply_text("❌ Çizim işlemi zaman aşımına uğradı (AI uyanamadı).")

async def ciz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Kullanıcıdan gelen çizim isteğini karşılar."""
    prompt = " ".join(context.args)
    if not prompt:
        await update.message.reply_text("❌ Lütfen çizilecek bir şey yazın. Örn: `/ciz space cat`")
        return
    
    await update.message.reply_text(f"🎨 **'{prompt}'** isteği alındı!\nArka planda hazırlanıyor, bu sırada /fiyat bakabilirsiniz...")
    
    # Çizim işlemini ayrı bir görev (task) olarak başlat, botu kilitleme
    asyncio.create_task(ciz_arka_plan(update, prompt))

# --- 4. ANA ÇALIŞTIRICI ---
def main():
    # Render'ın portunu açık tutmak için Flask'ı ayrı bir kanalda başlat
    Thread(target=run_web, daemon=True).start()
    
    # Telegram bot uygulamasını kur
    application = Application.builder().token(TOKEN).build()
    
    # Komutları tanımla
    application.add_handler(CommandHandler("fiyat", fiyat))
    application.add_handler(CommandHandler("ciz", ciz))
    
    print(">>> IRVUS BOT RENDER ÜZERİNDE BAŞLATILDI!")
    
    # Botu çalıştır (drop_pending_updates: bot kapalıyken gelen eski mesajları siler)
    application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
    
