import os, requests, asyncio
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters

app = Flask(__name__)
@app.route('/')
def home(): return "IRVUS FINAL V20 ONLINE", 200

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

TOKEN = "8621050385:AAGA6wcxbFY2rqJ9gjXVK_JNqsebJvTv_Jo"
db = {}

def get_settings_buttons(chat_id):
    data = db.get(chat_id, {})
    emoji = data.get("emoji", "🟢")
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🖼 Gif / Image", callback_data="toggle_media"), InlineKeyboardButton("⬆️ Min Buy $0", callback_data="ask_minbuy")],
        [InlineKeyboardButton(f"{emoji} Buy Emoji", callback_data="ask_emoji"), InlineKeyboardButton("💰 Buy Step $10", callback_data="set_step")],
        [InlineKeyboardButton("⚙️ Group Settings", callback_data="group_sets")]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("🌐 Web Site", url="https://www.irvustoken.xyz"), InlineKeyboardButton("🐦 Twitter", url="https://x.com/IRVUSTOKEN")]])
    await update.message.reply_text("🚀 **Irvus Pro Aktif!**\n\n⚙️ `/add` -> Kurulum\n💰 `/fiyat` -> Fiyat", reply_markup=kb)

async def add_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    db[chat_id] = {"step": "WAIT_NET", "emoji": "🟢"}
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("Ethereum", callback_data="n_eth"), InlineKeyboardButton("BSC", callback_data="n_bsc"), InlineKeyboardButton("Base", callback_data="n_base")]])
    await update.message.reply_text("➡️ **Lütfen Ağ Seçin:**", reply_markup=kb)

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    chat_id = str(query.message.chat_id)
    await query.answer()

    if query.data.startswith("n_"):
        db[chat_id]["step"] = "WAIT_CA"
        await query.edit_message_text(f"🟡 **{query.data[2:].upper()} Kontrat Adresini (CA) Gönderin:**")
    
    elif query.data.startswith("p_"):
        # Veriyi çok kısa tutuyoruz (Telegram limiti için)
        pair_addr = query.data[2:]
        db[chat_id].update({"ca": pair_addr, "step": "DONE"})
        await query.edit_message_text("✅ **Kurulum Tamamlandı!**", reply_markup=get_settings_buttons(chat_id))

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
            
            btns = []
            for p in pairs[:4]:
                p_addr = p['pairAddress']
                p_name = p['baseToken']['symbol']
                # Buton verisini 64 karakteri geçmeyecek şekilde kısalttık
                btns.append([InlineKeyboardButton(f"✅ {p_name}", callback_data=f"p_{p_addr[:50]}")])
            
            db[chat_id]["step"] = "SELECT_PAIR"
            await update.message.reply_text("ℹ️ **Havuz Seçin:**", reply_markup=InlineKeyboardMarkup(btns))
        except: await update.message.reply_text("❌ Hata oluştu.")

if __name__ == '__main__':
    Thread(target=run_web, daemon=True).start()
    app_tg = Application.builder().token(TOKEN).build()
    app_tg.add_handler(CommandHandler("start", start))
    app_tg.add_handler(CommandHandler("add", add_command))
    app_tg.add_handler(CallbackQueryHandler(handle_callback))
    app_tg.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app_tg.run_polling(drop_pending_updates=True)
    
