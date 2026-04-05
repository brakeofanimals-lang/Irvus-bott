import os, requests, asyncio, time
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler

app = Flask(__name__)
@app.route('/')
def home(): return "IRVUS TRANSACTION SNIPER ACTIVE", 200

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- AYARLAR ---
TOKEN = "8621050385:AAGA6wcxbFY2rqJ9gjXVK_JNqsebJvTv_Jo"
db = {} # { chat_id: {"ca": "...", "last_txn": None} }
BUY_IMAGE = "https://i.ibb.co/vz6mXq0/new-buy.jpg" # Buraya kendi 'New Buy' resim linkini koyabilirsin

# --- ALIM TARAYICI (PROFESYONEL) ---
async def track_transactions(context: ContextTypes.DEFAULT_TYPE):
    for chat_id, data in db.items():
        ca = data.get("ca")
        if not ca: continue
        
        try:
            # DexScreener API'den en güncel çift verisini çek
            r = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{ca}", timeout=10).json()
            pair = r['pairs'][0]
            
            # API bazen son işlemleri 'txns' içinde verir. 
            # Ücretsiz API kısıtlı olduğu için biz 'h24' hacim ve fiyat değişimini anlık izliyoruz.
            # Gerçek bir 'Transaction' takibi için ücretli API veya Web3 kütüphanesi gerekir.
            # Ama biz burada 'Volume Spike' (Hacim Sıçraması) mantığını mükemmelleştirdik.
            
            current_vol = float(pair.get('volume', {}).get('h24', 0))
            
            if data.get("last_vol") and current_vol > data["last_vol"]:
                # Alım miktarını hesapla (Tahmini)
                diff = current_vol - data["last_vol"]
                if diff < 1: continue # 1 dolardan küçük 'toz' alımları gösterme
                
                price = pair['priceUsd']
                mcap = f"{int(pair.get('fdv', 0)):,}"
                symbol = pair['baseToken']['symbol']
                
                # Mesajı Skeleton Bot tarzında hazırla
                text = (
                    f"✨ **{symbol} [ {symbol} ] 🔵 Buy!**\n\n"
                    f"🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢\n\n"
                    f"💵 **Spent:** `${diff:.2f} USDC`\n"
                    f"🛍 **Got:** `{int(diff / float(price)):,} {symbol}`\n"
                    f"👤 **Buyer:** [Link](https://etherscan.io/address/{ca})\n"
                    f"📊 **Market Cap:** `${mcap}`"
                )
                
                kb = InlineKeyboardMarkup([
                    [InlineKeyboardButton("📈 Chart", url=pair['url']), InlineKeyboardButton("🛒 Buy", url=pair['url'])]
                ])
                
                await context.bot.send_photo(
                    chat_id=chat_id,
                    photo=BUY_IMAGE,
                    caption=text,
                    reply_markup=kb,
                    parse_mode='Markdown'
                )
            
            db[chat_id]["last_vol"] = current_vol
        except: continue

# --- KOMUTLAR ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🌐 Web Site", url="https://www.irvustoken.xyz"), 
         InlineKeyboardButton("🐦 Twitter", url="https://x.com/IRVUSTOKEN")]
    ])
    await update.message.reply_text("🚀 **Irvus Sniper Bot Aktif!**\n\nKurulum için: `/kur [Kontrat]`", reply_markup=kb)

async def set_token(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args: return
    ca = context.args[0].strip()
    db[str(update.effective_chat.id)] = {"ca": ca, "last_vol": 0}
    await update.message.reply_text(f"✅ **Takip Başladı!**\nToken: `{ca}`", parse_mode='Markdown')

if __name__ == '__main__':
    Thread(target=run_web, daemon=True).start()
    app_tg = Application.builder().token(TOKEN).build()
    app_tg.add_handler(CommandHandler("start", start))
    app_tg.add_handler(CommandHandler(["kur", "setup", "set_token"], set_token))
    
    # 15 saniyede bir kontrol et (Daha agresif takip)
    app_tg.job_queue.run_repeating(track_transactions, interval=15, first=5)
    
    app_tg.run_polling(drop_pending_updates=True)
    
