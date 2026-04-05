import os
import requests
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes

# --- WEB SUNUCUSU ---
app = Flask(__name__)
@app.route('/')
def home(): return "OK", 200

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- AYARLAR ---
TOKEN = "8621050385:AAGA6wcxbFY2rqJ9gjXVK_JNqsebJvTv_Jo"
TOKEN_ADRESI = "0x31EDA2dfd01c9C65385cCE6099B24b06ef3aE831"
HF_TOKEN = "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"
API_URL = "https://api-inference.huggingface.co/models/prompthero/openjourney"

# --- KOMUTLAR ---

async def fiyat_gonder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        res = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{TOKEN_ADRESI}", timeout=10).json()
        pair = res['pairs'][0]
        fiyat = pair.get('priceUsd', '0.00')
        degisim = pair.get('priceChange', {}).get('h24', '0.00')
        msg = f"💎 **$IRVUS**\n💰 Fiyat: ${fiyat}\n📈 24s Değişim: %{degisim}"
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("📈 Grafik", url=pair.get('url'))]])
        await update.message.reply_text(msg, reply_markup=kb, parse_mode='Markdown')
    except:
        await update.message.reply_text("❌ Fiyat verisi çekilemedi.")

async def ciz_komutu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = " ".join(context.args)
    if not prompt:
        await update.message.reply_text("❌ Örn: /ciz araba")
        return
    
    durum = await update.message.reply_text("🎨 Çiziliyor...")
    try:
        headers = {"Authorization": f"Bearer {HF_TOKEN}"}
        response = requests.post(API_URL, headers=headers, json={"inputs": prompt}, timeout=90)
        if response.status_code == 200:
            await update.message.reply_photo(photo=response.content, caption=f"🖼 {prompt}")
        else:
            await update.message.reply_text("💤 AI şu an meşgul, birazdan tekrar deneyin.")
    except:
        await update.message.reply_text("❌ Hata oluştu.")
    finally:
        try: await durum.delete()
        except: pass

# --- MOTOR ---
if __name__ == '__main__':
    Thread(target=run_web, daemon=True).start()
    
    application = Application.builder().token(TOKEN).build()
    
    # Sadece İngilizce karakterli komutlar (Çakışmayı önlemek için)
    application.add_handler(CommandHandler("fiyat", fiyat_gonder))
    application.add_handler(CommandHandler("ciz", ciz_komutu))
    
    print(">>> BOT AKTIF")
    application.run_polling(drop_pending_updates=True)
    
