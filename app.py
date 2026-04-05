import os, requests, asyncio
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters

app = Flask(__name__)
@app.route('/')
def home(): return "IRVUS GOLD V18 ONLINE", 200

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

TOKEN = "8621050385:AAGA6wcxbFY2rqJ9gjXVK_JNqsebJvTv_Jo"
db = {} 

# --- AYARLAR PANELİ ---
def get_settings_buttons(chat_id):
    data = db.get(chat_id, {})
    emoji = data.get("emoji", "🟢")
    min_buy = data.get("min_buy", "0")
    media = "🚫" if not data.get("media", True) else "🖼"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"{media} Gif / Image", callback_data="toggle_media"),
         InlineKeyboardButton(f"⬆️ Min Buy ${min_buy}", callback_data="ask_minbuy")],
        [InlineKeyboardButton(f"{emoji} Buy Emoji", callback_data="ask_emoji"),
         InlineKeyboardButton("💰 Buy Step $10", callback_data="set_step")],
        [InlineKeyboardButton("⚙️ Group Settings", callback_data="group_sets")],
        [InlineKeyboardButton("🎟 Premium (Ad-Free)", url="https://www.irvustoken.xyz")]
    ])

# --- ANA MENÜ ---
def get_start_buttons():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🌐 Web Site", url="https://www.irvustoken.xyz"),
         InlineKeyboardButton("🐦 Twitter", url="https://x.com/IRVUSTOKEN")],
        [InlineKeyboardButton("⚙️ Kurulum (Add)", callback_data="start_add")]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚀 **Irvus Pro Bot Aktif!**\n\n🖼 `/ciz` -> AI Çizim\n💰 `/fiyat` -> Fiyat\n⚙️ `/add` -> Kurulum",
        reply_markup=get_start_buttons(),
        parse_mode='Markdown'
    )

async def add_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    db[chat_id] = {"step": "WAIT_NET", "emoji": "🟢", "min_buy": 0, "media": True}
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("Ethereum", callback_data="net_ETH"), 
                                 InlineKeyboardButton("BSC", callback_data="net_BSC"),
                                 InlineKeyboardButton("Base", callback_data="net_BASE")]])
    await update.message.reply_text("➡️ **Lütfen Ağ Seçin (Select Chain):**", reply_markup=kb)

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    chat_id = str(query.message.chat_id)
    await query.answer()

    if query.data == "start_add":
        await add_command(query, context)
    elif "net_" in query.data:
        db[chat_id]["step"] = "WAIT_CA"
        await query.edit_message_text(f"🟡 **{query.data.split('_')[1]} Kontrat Adresi (CA) Gönderin:**")
    elif "pair_" in query.data:
        p_addr = query.data.split("_")[1]
        db[chat_id].update({"ca": p_addr, "step": "DONE"})
        await query.edit_message_text("⚙️ **Kurulum Tamamlandı! Ayarlar:**", reply_markup=get_settings_buttons(chat_id))
    elif query.data == "toggle_media":
        db[chat_id]["media"] = not db[chat_id].get("media", True)
        await query.edit_message_reply_markup(reply_markup=get_settings_buttons(chat_id))
    elif query.data == "ask_emoji":
        db[chat_id]["step"] = "SET_EMOJI"
        await query.message.reply_text("✨ Yeni emojiyi gönderin:")
    elif query.data == "ask_minbuy":
        db[chat_id]["step"] = "SET_MINBUY"
        await query.message.reply_text("💰 Min dolar miktarını yazın:")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    user_data = db.get(chat_id, {})
    txt = update.message.text.strip()

    if user_data.get("step") == "WAIT_CA":
        try:
            r = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{txt}", timeout=10).json()
            pairs = r.get('pairs', [])[:3]
            if not pairs:
                await update.message.reply_text("❌ CA bulunamadı veya havuz yok.")
                return
            btns = [[InlineKeyboardButton(f"✅ {p['baseToken']['symbol']}", callback_data=f"pair_{p['pairAddress']}_{p['baseToken']['symbol']}")] for p in pairs]
            db[chat_id]["step"] = "SELECT_PAIR"
            await update.message.reply_text("ℹ️ **Havuz Seçin (Select Pair):**", reply_markup=InlineKeyboardMarkup(btns))
        except: await update.message.reply_text("❌ DexScreener hatası.")
    elif user_data.get("step") == "SET_EMOJI":
        db[chat_id]["emoji"] = txt
        db[chat_id]["step"] = "DONE"
        await update.message.reply_text("✅ Güncellendi.", reply_markup=get_settings_buttons(chat_id))
    elif user_data.get("step") == "SET_MINBUY":
        db[chat_id]["min_buy"] = txt
        db[chat_id]["step"] = "DONE"
        await update.message.reply_text("✅ Güncellendi.", reply_markup=get_settings_buttons(chat_id))

async def price_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    ca = db.get(chat_id, {}).get("ca")
    if not ca:
        await update.message.reply_text("❌ Önce `/add` yapmalısın.")
        return
    try:
        r = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{ca}").json()
        p = r['pairs'][0]
        msg = f"💎 **{p['baseToken']['symbol']}**\n💰 Fiyat: `${p['priceUsd']}`\n📈 24s: `%{p['priceChange']['h24']}`"
        await update.message.reply_text(msg, parse_mode='Markdown')
    except: pass

async def draw_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = " ".join(context.args)
    if not prompt: return
    await update.message.reply_text("🎨 Çiziliyor...")
    img = f"https://image.pollinations.ai/prompt/{prompt.replace(' ', '%20')}?width=1024&height=1024&nologo=true"
    await update.message.reply_photo(photo=img)

if __name__ == '__main__':
    Thread(target=run_web, daemon=True).start()
    app_tg = Application.builder().token(TOKEN).build()
    app_tg.add_handler(CommandHandler("start", start))
    app_tg.add_handler(CommandHandler("add", add_command))
    app_tg.add_handler(CommandHandler(["fiyat", "p"], price_command))
    app_tg.add_handler(CommandHandler(["ciz", "draw"], draw_command))
    app_tg.add_handler(CallbackQueryHandler(handle_callback))
    app_tg.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app_tg.run_polling(drop_pending_updates=True)
