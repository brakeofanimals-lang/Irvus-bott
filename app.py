import os, requests, asyncio, json
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters

app = Flask(__name__)
@app.route('/')
def home(): return "IRVUS ULTRA V39 ONLINE", 200

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
                    f"📈 **IRVUS [IRVUS] 🔵 YENİ HAREKET!**\n"
                    f"🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢\n\n"
                    f"💵 | Tutar: **{diff:.2f} USD**\n"
                    f"💰 | Alınan: **{got:,} IRVUS**\n"
                    f"💠 | Market Cap: **${int(mcap):,}**\n"
                    f"📊 | [Grafiği Gör]({p['url']})"
                )
                await context.bot.send_photo(chat_id=CHAT_ID, photo=BUY_IMAGE, caption=msg, parse_mode='Markdown')
            vol_cache["last"] = current_vol
    except: pass

def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🌐 Web Site", url="https://www.irvustoken.xyz"), InlineKeyboardButton("🐦 Twitter (X)", url="https://x.com/IRVUSTOKEN")],
        [InlineKeyboardButton("🛠 Komutlar", callback_data="cmds")]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🛡 **Irvus Warrior v39 Online!**", reply_markup=main_menu())

async def price_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        r = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{IRVUS_CA}").json()
        p = r['pairs'][0]
        await update.message.reply_text(f"💎 **IRVUS FİYAT**\n\n💰 `${p['priceUsd']}`\n📊 24s: %{p['priceChange']['h24']}", parse_mode='Markdown')
    except: pass

async def draw_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args: return await update.message.reply_text("❌ Örn: `/ciz savaşçı` yaz.")
    prompt = " ".join(context.args)
    await update.message.reply_text("🎨 **AI Çiziyor...**")
    url = f"https://image.pollinations.ai/prompt/{prompt.replace(' ', '%20')}?nologo=true"
    await update.message.reply_photo(photo=url, caption=f"🖼 AI: {prompt}")

async def cb_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "cmds":
        await query.edit_message_text("🛠 **Komutlar:**\n\n💰 `/fiyat` | 🎨 `/ciz [metin]`", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Geri", callback_data="back")]]))
    elif query.data == "back":
        await query.edit_message_text("🛡 **Irvus Warrior Bot**", reply_markup=main_menu())

if __name__ == '__main__':
    Thread(target=run_web, daemon=True).start()
    # Event loop hatasını önlemek için modern başlatma
    builder = Application.builder().token(TOKEN).build()
    builder.add_handler(CommandHandler("start", start))
    builder.add_handler(CommandHandler(["fiyat", "p"], price_cmd))
    builder.add_handler(CommandHandler(["ciz", "draw"], draw_cmd))
    builder.add_handler(CallbackQueryHandler(cb_handler))
    
    if builder.job_queue:
        builder.job_queue.run_repeating(track_buys, interval=10, first=5)
    
    print("Bot is running...")
    builder.run_polling(drop_pending_updates=True)
    
