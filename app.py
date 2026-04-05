import os, requests, asyncio
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters

app = Flask(__name__)
@app.route('/')
def home(): return "IRVUS DESTROYER V21 ONLINE", 200

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

TOKEN = "8621050385:AAGA6wcxbFY2rqJ9gjXVK_JNqsebJvTv_Jo"
db = {} # { chat_id: {"pairs": [], "ca": "...", "step": "..."} }

# --- AYARLAR PANELİ ---
def get_settings_buttons(chat_id):
    data = db.get(chat_id, {})
    emoji = data.get("emoji", "🟢")
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🖼 Gif / Image", callback_data="set_media"), InlineKeyboardButton("⬆️ Min Buy $0", callback_data="set_min")],
        [InlineKeyboardButton(f"{emoji} Buy Emoji", callback_data="set_emoji"), InlineKeyboardButton("💰 Buy Step $10", callback_data="set_step")],
        [InlineKeyboardButton("⚙️ Group Settings", callback_data="set_group")]
    ])

# --- ANA KOMUTLAR ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("🌐 Web Site", url="https://www.irvustoken.xyz"), InlineKeyboardButton("🐦 Twitter", url="https://x.com/IRVUSTOKEN")]])
    await update.message.reply_text("🚀 **Irvus Pro Aktif!**\n\n🖼 `/ciz` -> AI Çizim\n💰 `/fiyat` -> Fiyat\n⚙️ `/add` -> Kurulum", reply_markup=kb)

async def add_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    db[chat_id] = {"step": "WAIT_NET", "emoji": "🟢", "pairs": []}
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("Ethereum", callback_data="n_eth"), InlineKeyboardButton("BSC", callback_data="n_bsc"), InlineKeyboardButton("Base", callback_data="n_base")]])
    await update.message.reply_text("➡️ **Lütfen Ağ Seçin:**", reply_markup=kb)

async def price_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    ca = db.get(chat_id, {}).get("ca")
    if not ca:
        await update.message.reply_text("❌ Önce `/add` yapmalısın.")
        return
    try:
        r = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{ca}").json()
        p = r['pairs'][0]
        await update.message.reply_text(f"💎 **{p['baseToken']['symbol']}**\n💰 Fiyat: `${p['priceUsd']}`\n📊 24h: %{p['priceChange']['h24']}")
    except: await update.message.reply_text("❌ Veri çekilemedi.")

async def draw_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    p = " ".join(context.args)
    if not p: return
    await update.message.reply_text("🎨 Çiziliyor...")
    img = f"https://image.pollinations.ai/prompt/{p.replace(' ', '%20')}?width=1024&height=1024&nologo=true"
    await update.message.reply_photo(photo=img, caption=f"🖼 AI: {p}")

# --- CALLBACK YÖNETİMİ ---
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    chat_id = str(query.message.chat_id)
    await query.answer()

    if query.data.startswith("n_"):
        db[chat_id]["step"] = "WAIT_CA"
        await query.edit_message_text(f"🟡 **{query.data[2:].upper()} Kontrat Adresini (CA) Gönderin:**")

    elif query.data.startswith("idx_"):
        idx = int(query.data.split("_")[1])
        pair_data = db[chat_id]["pairs"][idx]
        db[chat_id].update({"ca": pair_data['addr'], "symbol": pair_data['sym'], "step": "DONE"})
        await query.edit_message_text(f"✅ **{pair_data['sym']}** başarıyla kuruldu!", reply_markup=get_settings_buttons(chat_id))

# --- MESAJ YÖNETİMİ ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    if db.get(chat_id, {}).get("step") == "WAIT_CA":
        ca = update.message.text.strip()
        try:
            r = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{ca}", timeout=10).json()
            pairs = r.get('pairs', [])
            if not pairs:
                await update.message.reply_text("❌ Havuz bulunamadı.")
                return
            
            db[chat_id]["pairs"] = []
            btns = []
            for i, p in enumerate(pairs[:5]):
                # Veriyi hafızaya alıyoruz, butona sadece INDEX (0,1,2..) koyuyoruz
                db[chat_id]["pairs"].append({"addr": p['pairAddress'], "sym": p['baseToken']['symbol']})
                btns.append([InlineKeyboardButton(f"✅ {p['baseToken']['symbol']} / {p['quoteToken']['symbol']}", callback_data=f"idx_{i}")])
            
            db[chat_id]["step"] = "SELECT_PAIR"
            await update.message.reply_text("ℹ️ **Havuz Seçin:**", reply_markup=InlineKeyboardMarkup(btns))
        except: await update.message.reply_text("❌ DexScreener bağlantı hatası.")

if __name__ == '__main__':
    Thread(target=run_web, daemon=True).start()
    app_tg = Application.builder().token(TOKEN).build()
    app_tg.add_handler(CommandHandler("start", start))
    app_tg.add_handler(CommandHandler("add", add_command))
    app_tg.add_handler(CommandHandler(["fiyat", "p", "price"], price_command))
    app_tg.add_handler(CommandHandler(["ciz", "draw", "ai"], draw_command))
    app_tg.add_handler(CallbackQueryHandler(handle_callback))
    app_tg.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app_tg.run_polling(drop_pending_updates=True)
        
