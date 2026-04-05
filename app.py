import sys, sqlite3, requests, time, os
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- HUGGING FACE/RENDER CANLI TUTMA ---
app = Flask('')
@app.route('/')
def home(): return "Bot Aktif!"

def run(): app.run(host='0.0.0.0', port=10000)

# --- AYARLAR ---
TOKEN = "8621050385:AAGFTwrCTwa-Ai-ywmzO6BOqo2J2wLTRHdg"
TOKEN_ADRESI = "0x31EDA2dfd01c9C65385cCE6099B24b06ef3aE831"

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
    except: return None, "❌ Veri hatası."

async def fiyat_gonder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url, msg = await get_token_data()
    if url:
        kb = [[InlineKeyboardButton("📈 Grafik", url=url)]]
        await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')
    else: await update.message.reply_text(msg)

async def mesaj_kontrol(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    text = update.message.text.lower()
    res = cursor.execute('SELECT anahtar, cevap FROM filtreler').fetchall()
    for anahtar, cevap in res:
        if anahtar in text:
            await update.message.reply_text(cevap)
            break

def main():
    Thread(target=run).start()
    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("fiyat", fiyat_gonder))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, mesaj_kontrol))
    
    print(">>> BOT BASLATILDI!")
    application.run_polling()

if __name__ == '__main__':
    main()
    
