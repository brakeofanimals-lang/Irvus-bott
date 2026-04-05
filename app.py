import os, requests, asyncio, json
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters

app = Flask(__name__)
@app.route('/')
def home(): return "IRVUS FULL-RADAR V38 ONLINE", 200

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- AYARLAR ---
TOKEN = "8621050385:AAGA6wcxbFY2rqJ9gjXVK_JNqsebJvTv_Jo"
IRVUS_CA = "0x31EDA2dfd01c9C65385cCE6099B24b06ef3aE831"
BUY_IMAGE = "https://raw.githubusercontent.com/IrvusToken/Logo/main/1000077361.png" 
CHAT_ID = "-1002488344186"

# Takip Hafızası
vol_cache = {"last": 0}

# --- ALIM MOTORU (10 Saniyede Bir - SINIRSIZ) ---
async def track_buys(context: ContextTypes.DEFAULT_TYPE):
    global vol_cache
    try:
        # DexScreener'dan en güncel veriyi çek
        r = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{IRVUS_CA}", timeout=4).json()
        if not r.get('pairs'): return
        p = r['pairs'][0]
        
        current_vol = float(p.get('volume', {}).get('h24', 0))
        
        # İlk çalışma için hacmi kaydet
        if vol_cache["last"] == 0:
            vol_cache["last"] = current_vol
            return

        # Hacim artışı varsa (ALIM SINIRI YOK - 0.1$ bile olsa yakalar)
        if current_vol > vol_cache["last"]:
            diff = current_vol - vol_cache["last"]
            
            # Sadece çok küçük küsurat hatalarını engellemek için 0.1$ sınırı (aslında sınırsız)
            if diff > 0.1: 
                price = float(p['priceUsd'])
                mcap = p.get('fdv', 0)
                got = int(diff / price) if price > 0 else 0
                
                msg = (
                    f"📈 **IRVUS [IRVUS] 🔵 YENİ HAREKET!**\n"
                    f"🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢\n\n"
                    f"💵 | Tutar: **{diff:.2f} USD**\n"
                    f"💰 | Alınan: **{got:,} IRVUS**\n"
                    f"💠 | Market Cap: **${int(mcap):,}**\n"
                    f"📊 | [Grafiği Gör]({p['url']})"
                )
                
                await context.bot.send_photo(
                    chat_id=CHAT_ID, 
                    photo=BUY_IMAGE, 
                    caption=msg, 
                    parse_mode='Markdown'
                )
            
            vol_cache["last"] = current_vol
            
    except Exception as e:
        print(f"Hata: {e}")

# --- MENÜ VE KOMUTLAR ---
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🌐 Web Site", url="https://www.irvustoken.xyz"), InlineKeyboardButton("🐦 Twitter (X)", url="https://x.com/IRVUSTOKEN")],
        [InlineKeyboardButton("🛠 Komutları Göster", callback_data="show_cmds")]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🛡 **Irvus Warrior Bot Görevde!**\n\nTüm alımlar sınırsız olarak 10 saniyede bir raporlanıyor.", reply_markup=main_menu())

async def draw_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args: return await update.message.reply_text("❌ Örn: `/ciz warrior` yaz.")
    prompt = " ".join(context.args)
    await update.message.reply_text("🎨 **AI Çiziyor...**")
    url = f"https://image.pollinations.ai/prompt/{prompt.replace(' ', '%20')}?nologo=true"
    await update.message.reply_photo(photo=url, caption=f"🖼 Görsel: {prompt}")

async def price_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        r = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{IRVUS_CA}").json()
        p = r['pairs'][0]
        msg = f"💎 **IRVUS FİYAT**\n\n💰 `${p['priceUsd']}`\n📊 24s: `%{p['priceChange']['h24']}`"
        await update.message.reply_text(msg, parse_mode='Markdown')
    except: pass

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "show_cmds":
        await query.edit_message_text("🛠 **Komutlar:**\n\n💰 `/fiyat` - Market Verisi\n🎨 `/ciz [metin]` - AI Çizim", 
                                     reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Geri", callback_data="back")]]))
    elif query.data == "back":
        await query.edit_message_text("🛡 **Irvus Warrior Bot**", reply_markup=main_menu())

if __name__ == '__main__':
    Thread(target=run_web, daemon=True).start()
    app_tg = Application.builder().token(TOKEN).build()
    
    app_tg.add_handler(CommandHandler("start", start))
    app_tg.add_handler(CommandHandler(["fiyat", "p"], price_command))
    app_tg.add_handler(CommandHandler(["ciz", "draw"], draw_command))
    app_tg.add_handler(CallbackQueryHandler(handle_callback))
    
    if app_tg.job_queue:
        app_tg.job_queue.run_repeating(track_buys, interval=10, first=5)
    
    app_tg.run_polling(drop_pending_updates=True)
    
