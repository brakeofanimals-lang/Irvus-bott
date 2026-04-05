import sys, sqlite3, requests, time, os, asyncio
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- WEB SUNUCUSU (BOTU CANLI TUTAR) ---
app = Flask('')
@app.route('/')
def home(): return "Bot Aktif!"

def run():
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

# --- AYARLAR ---
TOKEN = "8621050385:AAGFTwrCTwa-Ai-ywmzO6BOqo2J2wLTRHdg"
TOKEN_ADRESI = "0x31EDA2dfd01c9C65385cCE6099B24b06ef3aE831"

# Veritabanı bağlantısı
conn = sqlite3.connect('filtreler.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS filtreler (anahtar TEXT PRIMARY KEY, cevap TEXT)')
conn.commit()

async def get_token_data():
    try:
        url = f"https://api.dexscreener.com/latest/dex/tokens/{TOKEN_ADRESI}"
        res = requests.get(url, timeout=10).json()
        pair = res['pairs'][0]
        fiyat = pair.get('priceUsd', '0.00')
        degisim = pair.get('priceChange', {}).get('h24', '0.00')
        emoji = "🚀" if float(degisim) > 0 else "📉"
        msg = f"💎 **$IRVUS Güncel Durum**\n\n💰 **Fiyat:** ${fiyat}\n{emoji} **24s Değişim:** %{degisim}"
        return pair.get('url'), msg
    except:
        return None, "❌ Veri hatası (DexScreener)."

async def fiyat_gonder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url, msg = await get_token_data()
    if url:
        kb = [[InlineKeyboardButton("📈 Grafik", url=url)]]
        await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')
    else:
        await update.message.reply_text(msg)

async def mesaj_kontrol(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    text = update.message.text.lower()
    res = cursor.execute('SELECT anahtar, cevap FROM filtreler').fetchall()
    for anahtar, cevap in res:
        if anahtar in text:
            await update.message.reply_text(cevap)
            break

def main():
    # Flask sunucusunu ayrı bir kanalda başlat
    Thread(target=run, daemon=True).start()
    
    # Bot kurulumu
    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("fiyat", fiyat_gonder))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, mesaj_kontrol))
    
    print(">>> BOT RENDER ÜZERİNDE BAŞLATILDI!")
    
    # Render'da çakışma olmaması için döngüyü açık tutuyoruz
    application.run_polling(close_loop=False)

if __name__ == '__main__':
    main()
    
