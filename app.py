import sys, sqlite3, requests, os, asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- AYARLAR ---
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
        return pair.get('url'), f"💎 **$IRVUS**\n💰 Fiyat: ${fiyat}\n{emoji} Değişim: %{degisim}"
    except: return None, "❌ Veri hatası."

async def fiyat_gonder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url, msg = await get_token_data()
    if url: await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📈 Grafik", url=url)]]), parse_mode='Markdown')
    else: await update.message.reply_text(msg)

# --- ANA MOTOR (MODERN YÖNTEM) ---
async def run_bot():
    print(">>> BOT HAZIRLANIYOR...")
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("fiyat", fiyat_gonder))
    
    print(">>> BOT RENDER ÜZERİNDE BAŞLATILDI!")
    
    # Python 3.14 için en güvenli başlatma:
    async with application:
        await application.initialize()
        await application.start()
        await application.updater.start_polling(drop_pending_updates=True)
        # Botu sonsuza kadar açık tut:
        while True:
            await asyncio.sleep(3600)

if __name__ == '__main__':
    # Render'daki 'no current event loop' hatasını çözen kısım:
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    loop.run_until_complete(run_bot())
    
