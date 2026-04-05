import sys, sqlite3, requests, os, asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- AYARLAR ---
TOKEN = "8621050385:AAGA6wcxbFY2rqJ9gjXVK_JNqsebJvTv_Jo"
TOKEN_ADRESI = "0x31EDA2dfd01c9C65385cCE6099B24b06ef3aE831"

async def get_token_data():
    try:
        # DexScreener API'ye daha sağlam bir istek atıyoruz
        url = f"https://api.dexscreener.com/latest/dex/tokens/{TOKEN_ADRESI}"
        headers = {'User-Agent': 'Mozilla/5.0'} # Render'ın bloklanmaması için
        res = requests.get(url, headers=headers, timeout=10).json()
        
        if 'pairs' in res and res['pairs']:
            pair = res['pairs'][0]
            fiyat = pair.get('priceUsd', '0.00')
            degisim = pair.get('priceChange', {}).get('h24', '0.00')
            emoji = "🚀" if float(degisim) > 0 else "📉"
            return pair.get('url'), f"💎 **$IRVUS Güncel Durum**\n\n💰 **Fiyat:** ${fiyat}\n{emoji} **24s Değişim:** %{degisim}"
        return None, "❌ Token verisi bulunamadı."
    except Exception as e:
        return None, f"❌ Veri hatası: {str(e)[:20]}"

async def fiyat_gonder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url, msg = await get_token_data()
    if url:
        kb = [[InlineKeyboardButton("📈 Grafik", url=url)]]
        await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')
    else:
        await update.message.reply_text(msg)

async def main():
    print(">>> BOT HAZIRLANIYOR...")
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("fiyat", fiyat_gonder))
    
    async with application:
        await application.initialize()
        await application.start()
        print(">>> BOT RENDER ÜZERİNDE AKTİF!")
        await application.updater.start_polling(drop_pending_updates=True)
        while True:
            await asyncio.sleep(3600)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
        
