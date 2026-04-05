import os, requests, asyncio
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters

app = Flask(__name__)
@app.route('/')
def home(): return "IRVUS ULTIMATE V16 ONLINE", 200

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

TOKEN = "8621050385:AAGA6wcxbFY2rqJ9gjXVK_JNqsebJvTv_Jo"
db = {} # Hafıza: { chat_id: {"ca": "...", "lang": "tr", "emoji": "🟢", "media": True, "step": None} }

# --- BUTONLAR ---
def get_start_buttons():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🇹🇷 Türkçe", callback_data="lang_tr"), InlineKeyboardButton("🇺🇸 English", callback_data="lang_en")],
        [InlineKeyboardButton("🌐 Web Site", url="https://www.irvustoken.xyz"), InlineKeyboardButton("🐦 Twitter (X)", url="https://x.com/IRVUSTOKEN")]
    ])

def get_settings_buttons(chat_id):
    data = db.get(chat_id, {})
    emoji = data.get("emoji", "🟢")
    media_status = "🚫" if not data.get("media", True) else "🖼"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"{media_status} Gif / Image", callback_data="toggle_media"), InlineKeyboardButton("⬆️ Min Buy $0", callback_data="set_minbuy")],
        [InlineKeyboardButton(f"{emoji} Buy Emoji", callback_data="set_emoji"), InlineKeyboardButton("💰 Buy Step $10", callback_data="set_step")],
        [InlineKeyboardButton("⚙️ Group Settings", callback_data="group_sets")],
        [InlineKeyboardButton("🎟 Premium (Ad-Free)", url="https://www.irvustoken.xyz")]
    ])

# --- KOMUTLAR (FIYAT VE CIZ DAHIL) ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚀 **Irvus Pro Bot Aktif!**\n\n🖼 `/ciz` -> AI Çizim\n💰 `/fiyat` -> Fiyat Bilgisi\n⚙️ `/add` -> Kurulum", reply_markup=get_start_buttons(), parse_mode='Markdown')

async def price_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    ca = db.get(chat_id, {}).get("ca")
    if not ca:
        await update.message.reply_text("❌ Önce `/add` ile botu kurmalısın.")
        return
    try:
        r = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{ca}").json()
        p = r['pairs'][0]
        msg = f"💎 **{p['baseToken']['symbol']} Güncel Durum**\n\n💰 Fiyat: `${p['priceUsd']}`\n📈 24s: `%{p['priceChange']['h24']}`"
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("📈 Grafik", url=p['url'])]])
        await update.message.reply_text(msg, reply_markup=kb, parse_mode='Markdown')
    except: await update.message.reply_text("❌ Veri çekilemedi.")

async def draw_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = " ".join(context.args)
    if not prompt:
        await update.message.reply_text("❌ Lütfen çizilecek şeyi yazın: `/ciz kedi` gibi.")
        return
    await update.message.reply_text("🎨 **Resim hazırlanıyor...**")
    img = f"https://image.pollinations.ai/prompt/{prompt.replace(' ', '%20')}?width=1024&height=1024&nologo=true"
    await update.message.reply_photo(photo=img, caption=f"🖼 AI Görsel: {prompt}")

async def add_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    db[chat_id] = {"step": "WAIT_NET", "emoji": "🟢", "media": True}
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("Ethereum", callback_data="net_ETH"), InlineKeyboardButton("BSC", callback_data="net_BSC"), InlineKeyboardButton("Base", callback_data="net_BASE")]])
    await update.message.reply_text("➡️ **Select Chain**", reply_markup=kb)

# --- CALLBACK VE MESAJ YÖNETİMİ ---

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    chat_id = str(query.message.chat_id)
    await query.answer()

    if "net_" in query.data:
        db[chat_id]["step"] = "WAIT_CA"
        await query.edit_message_text(f"🟡 **{query.data.split('_')[1]} Token address?**")

    elif "pair_" in query.data:
        p_addr = query.data.split("_")[1]
        p_name = query.data.split("_")[2]
        db[chat_id].update({"pair_id": p_addr, "ca": p_addr, "step": "DONE"})
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("🟢 Buy Bot Settings", callback_data="open_settings")]])
        await query.edit_message_text(f"✅ **{p_name}** başarıyla kuruldu!", reply_markup=kb)

    elif query.data == "open_settings":
        await query.edit_message_text("⚙️ **Buy Bot Settings**", reply_markup=get_settings_buttons(chat_id))

    elif query.data == "toggle_media":
        db[chat_id]["media"] = not db[chat_id].get("media", True)
        await query.edit_message_reply_markup(reply_markup=get_settings_buttons(chat_id))

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    if db.get(chat_id, {}).get("step") == "WAIT_CA":
        ca = update.message.text.strip()
        try:
            r = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{ca}").json()
            pairs = r.get('pairs', [])[:3]
            buttons = [[InlineKeyboardButton(f"✅ {p['baseToken']['symbol']}", callback_data=f"pair_{p['baseToken']['address']}_{p['baseToken']['symbol']}")] for p in pairs]
            db[chat_id]["step"] = "SELECT_PAIR"
            await update.message.reply_text("ℹ️ **Select Pair**", reply_markup=InlineKeyboardMarkup(buttons))
        except: await update.message.reply_text("❌ Hata oluştu.")

if __name__ == '__main__':
    Thread(target=run_web, daemon=True).start()
    app_tg = Application.builder().token(TOKEN).build()
    app_tg.add_handler(CommandHandler("start", start))
    app_tg.add_handler(CommandHandler(["fiyat", "price", "p"], price_command))
    app_tg.add_handler(CommandHandler(["ciz", "draw", "ai"], draw_command))
    app_tg.add_handler(CommandHandler("add", add_command))
    app_tg.add_handler(CallbackQueryHandler(handle_callback))
    app_tg.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app_tg.run_polling(drop_pending_updates=True)
    
