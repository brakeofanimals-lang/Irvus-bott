import sys, sqlite3, requests, os, asyncio
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- WEB SUNUCUSU ---
app = Flask('')
@app.route('/')
def home(): return "Bot Aktif!"

def run_flask():
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

# --- AYARLAR ---
TOKEN = "8621050385:AAGFTwrCTwa-Ai-ywmzO6BOqo2J2wLTRHdg"
TOKEN_ADRESI = "0x31EDA2dfd01c9C65385cCE6099B24b06ef3aE831"

async def get_token_data():
    try:
        url = f"https://api.dexscreener.com/latest/dex/tokens/{TOKEN_ADRESI}"
        res = requests.get(url, timeout=10).json()
        pair = res['pairs'][0]
        fiyat = pair.get('priceUsd', '0.00')
        degisim = pair.get('priceChange', {}).get('h24', '0.00')
        emoji = "🚀" if float(degisim) > 0 else "📉"
        return pair.get('url'), f"💎 **$IRVUS**\n💰 Fiyat: ${fiyat}\n{emoji} Değişim: %{degisim}"
    except: return None, "❌ Veri hatası."

async def fiyat_gonder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url, msg = await get_token_data()
    if url: await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📈 Grafik", url=url)]]), parse_mode='Markdown')
    else: await update.message.reply_text(msg)

# --- ANA MOTOR ---
async def start_bot():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("fiyat", fiyat_gonder))
    
    # Flask'ı arka planda başlat
    Thread(target=run_flask, daemon=True).start()
    
    print(">>> BOT HAZIR, BASLATILIYOR...")
    
    # Yeni Python sürümleri için en güvenli başlatma yolu
    async with application:
        await application.initialize()
        await application.start_polling()
        # Botu sonsuza kadar açık tut
        while True:
            await asyncio.sleep(3600)

if __name__ == '__main__':
    try:
        asyncio.run(start_bot())
    except (KeyboardInterrupt, SystemExit):
        pass
        
