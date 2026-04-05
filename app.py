import os
import asyncio
import requests
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes

# --- 1. WEB SUNUCUSU (RENDER KAPISI) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "OK", 200

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- 2. AYARLAR ---
TOKEN = "8621050385:AAGA6wcxbFY2rqJ9gjXVK_JNqsebJvTv_Jo"
TOKEN_ADRESI = "0x31EDA2dfd01c9C65385cCE6099B24b06ef3aE831"
HF_TOKEN = "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"
API_URL = "https://api-inference.huggingface.co/models/prompthero/openjourney"

# --- 3. KOMUTLAR ---

async def fiyat_gonder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        res = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{TOKEN_ADRESI}", timeout=10).json()
        pair = res['pairs'][0]
        msg = f"💎 **$IRVUS**\n💰 Fiyat: ${pair.get('priceUsd')}\n📈 24s: %{pair.get('priceChange', {}).get('h24')}"
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("📈 Grafik", url=pair.get('url'))]])
        await update.message.reply_text(msg, reply_markup=kb, parse_mode='Markdown')
    except:
        await update.message.reply_text("❌ Veri hatası.")

async def ciz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = " ".join(context.args)
    if not prompt:
        await update.message.reply_text("❌ Örn: `/ciz car`")
        return

    durum = await update.message.reply_text("🎨 AI Çizime Başladı...")
    
    try:
        headers = {"Authorization": f"Bearer {HF_TOKEN}"}
        response = requests.post(API_URL, headers=headers, json={"inputs": prompt}, timeout=90)
        
        if response.status_code == 200:
            # Resim başarıyla gelirse gönder
            await update.message.reply_photo(photo=response.content, caption=f"🖼 **Sonuç:** {prompt}")
        else:
            await update.message.reply_text("💤 AI şu an meşgul, 30 saniye sonra tekrar deneyin.")
    except Exception as e:
        await update.message.reply_text("❌ Hata oluştu.")
    finally:
        await durum.delete()

# --- 4. ANA ÇALIŞTIRICI ---
if __name__ == '__main__':
    # Flask sunucusunu hemen başlat
    Thread(target=run_web, daemon=True).start()
    
    print(">>> BOT BASLATILIYOR...")
    
    # Bot kurulumu (En basit ve güncel haliyle)
    application = Application.builder().token(TOKEN).build()
    
    # Komutları ekle
    application.add_handler(CommandHandler("fiyat", fiyat_gonder))
    application.add_handler(CommandHandler(["ciz", "çiz"], ciz))
    
    # Botu çalıştır
    application.run_polling(drop_pending_updates=True)
    
