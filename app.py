import sys, sqlite3, requests, os, asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- AYARLAR ---
# Yeni Token'ını buraya eksiksiz yerleştirdim
TOKEN = "8621050385:AAGA6wcxbFY2rqJ9gjXVK_JNqsebJvTv_Jo"
TOKEN_ADRESI = "0x31EDA2dfd01c9C65385cCE6099B24b06ef3aE831"

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
    except Exception as e:
        print(f"Veri çekme hatası: {e}")
        return None, "❌ Veri şu an çekilemiyor (DexScreener)."

async def fiyat_gonder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url, msg = await get_token_data()
    if url:
        kb = [[InlineKeyboardButton("📈 Grafik", url=url)]]
        await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')
    else:
        await update.message.reply_text(msg)

def main():
    # Render ve Python 3.14 uyumlu en sade kurulum
    print(">>> BOT HAZIRLANIYOR...")
    
    application = Application.builder().token(TOKEN).build()
    
    # Komutları ekle
    application.add_handler(CommandHandler("fiyat", fiyat_gonder))
    
    print(">>> BOT RENDER ÜZERİNDE RESMEN BAŞLATILDI!")
    
    # Bekleyen mesajları temizle ve dinlemeye başla
    application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
    
