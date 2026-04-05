import os, requests, asyncio, time
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters

app = Flask(__name__)
@app.route('/')
def home(): return "IRVUS FIXER V19 ONLINE", 200

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

TOKEN = "8621050385:AAGA6wcxbFY2rqJ9gjXVK_JNqsebJvTv_Jo"
db = {} 

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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("🌐 Web Site", url="https://www.irvustoken.xyz"),
                                 InlineKeyboardButton("🐦 Twitter", url="https://x.com/IRVUSTOKEN")]])
    await update.message.reply_text("🚀 **Irvus Pro Aktif!**\n\n⚙️ `/add` -> Kurulum\n💰 `/fiyat` -> Fiyat", reply_markup=kb)

async def add_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    db[chat_id] = {"step": "WAIT_NET", "emoji": "🟢", "min_buy": 0, "media": True}
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("Ethereum", callback_data="net_ethereum"), 
                                 InlineKeyboardButton("BSC", callback_data="net_bsc"),
                                 InlineKeyboardButton("Base", callback_data="net_base")]])
    await update.message.reply_text("➡️ **Lütfen Ağ Seçin:**", reply_markup=kb)

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    chat_id = str(query.message.chat_id)
    await query.answer()

    if "net_" in query.data:
        db[chat_id]["step"] = "WAIT_CA"
        net_val = query.data.split('_')[1]
        await query.edit_message_text(f"🟡 **{net_val.upper()} Kontrat Adresini (CA) Gönderin:**")
    
    elif "pair_" in query.data:
        _, p_addr, p_sym = query.data.split("_")
        db[chat_id].update({"ca": p_addr, "step": "DONE", "symbol": p_sym})
        await query.edit_message_text(f"✅ **{p_sym}** başarıyla kuruldu!", reply_markup=get_settings_buttons(chat_id))

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    if db.get(chat_id, {}).get("step") == "WAIT_CA":
        ca = update.message.text.strip()
        await update.message.reply_text("🔍 Veriler kontrol ediliyor, lütfen bekleyin...")
        
        try:
            # DexScreener sorgusu (Hata payını azaltmak için timeout ve kontrol eklendi)
            url = f"https://api.dexscreener.com/latest/dex/tokens/{ca}"
            r = requests.get(url, timeout=15)
            if r.status_code != 200:
                await update.message.reply_text("❌ DexScreener'a ulaşılamıyor. Daha sonra tekrar deneyin.")
                return
            
            data = r.json()
            pairs = data.get('pairs', [])
            
            if not pairs:
                await update.message.reply_text("❌ Bu CA için havuz bulunamadı. Adresi doğru ağda gönderdiğinizden emin olun.")
                return
            
            btns = []
            for p in pairs[:5]: # En popüler 5 havuzu getir
                p_addr = p['pairAddress']
                p_sym = p['baseToken']['symbol']
                quote = p['quoteToken']['symbol']
                btns.append([InlineKeyboardButton(f"✅ {p_sym} / {quote}", callback_data=f"pair_{p_addr}_{p_sym}")])
            
            db[chat_id]["step"] = "SELECT_PAIR"
            await update.message.reply_text("ℹ️ **Lütfen Takip Edilecek Havuzu Seçin:**", reply_markup=InlineKeyboardMarkup(btns))
            
        except Exception as e:
            await update.message.reply_text(f"❌ Bağlantı hatası: {str(e)[:50]}")

async def price_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    ca = db.get(chat_id, {}).get("ca")
    if not ca:
        await update.message.reply_text("❌ Önce `/add` ile kurulum yapmalısınız.")
        return
    try:
        r = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{ca}").json()
        p = r['pairs'][0]
        await update.message.reply_text(f"💎 **{p['baseToken']['symbol']}**\n💰 Fiyat: `${p['priceUsd']}`")
    except: pass

if __name__ == '__main__':
    Thread(target=run_web, daemon=True).start()
    app_tg = Application.builder().token(TOKEN).build()
    app_tg.add_handler(CommandHandler("start", start))
    app_tg.add_handler(CommandHandler("add", add_command))
    app_tg.add_handler(CommandHandler(["fiyat", "p"], price_command))
    app_tg.add_handler(CallbackQueryHandler(handle_callback))
    app_tg.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app_tg.run_polling(drop_pending_updates=True)
    
