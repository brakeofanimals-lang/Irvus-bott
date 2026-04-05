import os, requests, asyncio, json
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters

app = Flask(__name__)
@app.route('/')
def home(): return "IRVUS TANK V40 ONLINE", 200

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- AYARLAR ---
TOKEN = "8621050385:AAGA6wcxbFY2rqJ9gjXVK_JNqsebJvTv_Jo"
IRVUS_CA = "0x31EDA2dfd01c9C65385cCE6099B24b06ef3aE831"
BUY_IMAGE = "https://raw.githubusercontent.com/IrvusToken/Logo/main/1000077361.png"
CHAT_ID = "-1002488344186"

vol_cache = {"last": 0}

async def track_buys(context: ContextTypes.DEFAULT_TYPE):
    global vol_cache
    try:
        r = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{IRVUS_CA}", timeout=4).json()
        if not r.get('pairs'): return
        p = r['pairs'][0]
        current_vol = float(p.get('volume', {}).get('h24', 0))
        
        if vol_cache["last"] == 0:
            vol_cache["last"] = current_vol
            return

        if current_vol > vol_cache["last"]:
            diff = current_vol - vol_cache["last"]
            if diff > 0.1:
                price = float(p['priceUsd'])
                mcap = p.get('fdv', 0)
                got = int(diff / price) if price > 0 else 0
                msg = (
                    f"📈 **IRVUS [IRVUS] 🔵 YENİ ALIM!**\n"
                    f"🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢\n\n"
                    f"💵 | Tutar: **{diff:.2f} USD**\n"
                    f"💰 | Alınan: **{got:,} IRVUS**\n"
                    f"💠 | Market Cap: **${int(mcap):,}**\n"
                    f"📊 | [Grafiği Gör]({p['url']})"
                )
                await context.bot.send_photo(chat_id=CHAT_ID, photo=BUY_IMAGE, caption=msg, parse_mode='Markdown')
            vol_cache["last"] = current_vol
    except: pass

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🌐 Web Site", url="https://www.irvustoken.xyz"), InlineKeyboardButton("🐦 Twitter (X)", url="https://x.com/IRVUSTOKEN")],
        [InlineKeyboardButton("🛠 Komutlar", callback_data="cmds")]
    ])
    await update.message.reply_text("🛡 **Irvus Warrior v40 Online!**\n\nHoş geldiniz! Alımlar otomatik takip ediliyor.", reply_markup=kb)

async def price_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        r = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{IRVUS_CA}").json()
        p = r['pairs'][0]
        await update.message.reply_text(f"💎 **IRVUS FİYAT**\n\n💰 `${p['priceUsd']}`\n📊 24s: %{p['priceChange']['h24']}")
    except: pass

async def draw_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args: return await update.message.reply_text("❌ Örn: `/ciz warrior` yaz.")
    prompt = " ".join(context.args)
    await update.message.reply_text("🎨 **AI Çiziyor...**")
    url = f"https://image.pollinations.ai/prompt/{prompt.replace(' ', '%20')}?nologo=true"
    await update.message.reply_photo(photo=url, caption=f"🖼 AI: {prompt}")

async def cb_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "cmds":
        await query.edit_message_text("🛠 **Komutlar:**\n\n💰 `/fiyat` | 🎨 `/ciz [metin]`", 
                                     reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Geri", callback_data="back")]]))
    elif query.data == "back":
        await query.edit_message_text("🛡 **Irvus Warrior Bot**", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🌐 Web Site", url="https://www.irvustoken.xyz"), InlineKeyboardButton("🐦 Twitter (X)", url="https://x.com/IRVUSTOKEN")],
            [InlineKeyboardButton("🛠 Komutlar", callback_data="cmds")]
        ]))

def main():
    Thread(target=run_web, daemon=True).start()
    
    # Yeni tip Application başlatma (Döngü hatasını önler)
    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler(["fiyat", "p"], price_cmd))
    application.add_handler(CommandHandler(["ciz", "draw"], draw_cmd))
    application.add_handler(CallbackQueryHandler(cb_handler))
    
    if application.job_queue:
        application.job_queue.run_repeating(track_buys, interval=10, first=5)
    
    print("--- BOT STARTING ---")
    application.run_polling(drop_pending_updates=True, close_loop=False)

if __name__ == '__main__':
    main()
                
