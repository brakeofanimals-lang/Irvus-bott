import os
import asyncio
import sqlite3
import requests
import io
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- 1. WEB SUNUCUSU (RENDER KAPISI) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Irvus Bot is Running!", 200

def run_web():
    # Render'ın PORT değişkenini buradan zorla okutuyoruz
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
        url = f"https://api.dexscreener.com/latest/dex/tokens/{TOKEN_ADRESI}"
        res = requests.get(url, timeout=10).json()
        pair = res['pairs'][0]
        msg = f"💎 **$IRVUS**\n💰 Fiyat: ${pair.get('priceUsd', '0.00')}\n📈 24s: %{pair.get('priceChange', {}).get('h24', '0.00')}"
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("📈 Grafik", url=pair.get('url'))]])
        await update.message.reply_text(msg, reply_markup=kb, parse_mode='Markdown')
    except:
        await update.message.reply_text("❌ Fiyat verisi alınamadı.")

async def ciz_komutu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = " ".join(context.args)
    if not prompt:
        await update.message.reply_text("❌ Örn: `/ciz araba`")
        return

    durum = await update.message.reply_text("🎨 AI Çizime Başladı... Lütfen bekleyin.")
    try:
        headers = {"Authorization": f"Bearer {HF_TOKEN}"}
        response = requests.post(API_URL, headers=headers, json={"inputs": prompt}, timeout=90)
        
        if response.status_code == 200:
            # Resim bytes olarak geliyor, direkt gönderiyoruz
            await update.message.reply_photo(photo=response.content, caption=f"🖼 **Sonuç:** {prompt}")
        else:
            await update.message.reply_text("💤 AI meşgul (Hugging Face uyanıyor), birazdan tekrar dene.")
    except Exception as e:
        await update.message.reply_text(f"❌ Hata: Bağlantı kurulamadı.")
    finally:
        await durum.delete()

# --- 4. ANA MOTOR ---
async def start_telegram_bot():
    application = Application.builder().token(TOKEN).build()
    
    # Komutlar
    application.add_handler(CommandHandler("fiyat", fiyat_gonder))
    application.add_handler(CommandHandler(["ciz", "çiz"], ciz_komutu))
    
    await application.initialize()
    await application.start()
    await application.updater.start_polling(drop_pending_updates=True)
    print(">>> Telegram Botu Aktif!")
    
    # Botun açık kalması için sonsuz döngü
    while True:
        await asyncio.sleep(3600)

if __name__ == '__main__':
    # ÖNCE WEB SUNUCUSUNU BAŞLAT (Render'ın hatayı kesmesi için)
    Thread(target=run_web, daemon=True).start()
    print(">>> Web Sunucusu Başlatıldı.")
    
    # SONRA TELEGRAM BOTUNU BAŞLAT
    try:
        asyncio.run(start_telegram_bot())
    except (KeyboardInterrupt, SystemExit):
        pass
        
