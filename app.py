import sys, sqlite3, requests, os, asyncio, io
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- WEB SUNUCUSU (KESİN ÇÖZÜM) ---
app = Flask(__name__)

@app.route('/')
def health_check():
    return "ALIVE", 200

def run():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- AYARLAR ---
TOKEN = "8621050385:AAGA6wcxbFY2rqJ9gjXVK_JNqsebJvTv_Jo"
TOKEN_ADRESI = "0x31EDA2dfd01c9C65385cCE6099B24b06ef3aE831"
HF_TOKEN = "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"
API_URL = "https://api-inference.huggingface.co/models/runwayml/stable-diffusion-v1-5"

# --- FONKSİYONLAR ---
async def get_token_data():
    try:
        url = f"https://api.dexscreener.com/latest/dex/tokens/{TOKEN_ADRESI}"
        res = requests.get(url, timeout=10).json()
        pair = res['pairs'][0]
        fiyat = pair.get('priceUsd', '0.00')
        degisim = pair.get('priceChange', {}).get('h24', '0.00')
        return f"💎 **$IRVUS**\n💰 Fiyat: ${fiyat}\n📈 Değişim: %{degisim}", pair.get('url')
    except: return "❌ Veri hatası.", None

async def fiyat_gonder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg, url = await get_token_data()
    if url:
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("📈 Grafik", url=url)]])
        await update.message.reply_text(msg, reply_markup=kb, parse_mode='Markdown')
    else: await update.message.reply_text(msg)

async def ciz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = " ".join(context.args)
    if not prompt:
        await update.message.reply_text("❌ Kullanım: `/ciz araba`", parse_mode='Markdown')
        return
    
    status_msg = await update.message.reply_text("🎨 Resim çiziliyor, lütfen bekleyin...")
    
    try:
        headers = {"Authorization": f"Bearer {HF_TOKEN}"}
        # Timeout süresini 80 saniyeye çıkardım (AI uyanırken vakit ister)
        response = requests.post(API_URL, headers=headers, json={"inputs": prompt}, timeout=80)
        
        if response.status_code == 200:
            await update.message.reply_photo(photo=response.content, caption=f"🖼 **Sonuç:** {prompt}")
        else:
            await update.message.reply_text("💤 AI şu an meşgul (Hugging Face uyanıyor), 30 saniye sonra tekrar deneyin.")
    except Exception as e:
        await update.message.reply_text("❌ Çizim hatası oluştu.")
    finally:
        await status_msg.delete()

async def main():
    # Flask'ı ayrı bir kanalda hemen başlatıyoruz
    Thread(target=run, daemon=True).start()
    
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("fiyat", fiyat_gonder))
    application.add_handler(CommandHandler(["ciz", "çiz"], ciz))
    
    print(">>> BOT AKTİF!")
    async with application:
        await application.initialize()
        await application.start()
        await application.updater.start_polling(drop_pending_updates=True)
        while True: await asyncio.sleep(3600)

if __name__ == '__main__':
    asyncio.run(main())
    
