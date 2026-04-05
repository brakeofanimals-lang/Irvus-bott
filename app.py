import os, requests, asyncio, json
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters

app = Flask(__name__)
@app.route('/')
def home(): return "IRVUS MASTERPIECE V28 ONLINE", 200

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

TOKEN = "8621050385:AAGA6wcxbFY2rqJ9gjXVK_JNqsebJvTv_Jo"
CONFIG_FILE = "config.json"
# Alım Mesajı Resmi
BUY_IMAGE = "https://w7.pngwing.com/pngs/341/365/png-transparent-irvus-token-logo-warrior-green.png"

# --- HAFIZA SİSTEMİ (UNUTMAZ) ---
def load_config():
    if not os.path.exists(CONFIG_FILE): return {}
    with open(CONFIG_FILE, 'r') as f: return json.load(f)

def save_config(data):
    with open(CONFIG_FILE, 'w') as f: json.dump(data, f)

db = load_config() # Açılışta dosyadan yükle

# --- ANA MENÜ BUTONLARI ---
def get_start_buttons():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🇹🇷 Türkçe", callback_data="lang_tr"), InlineKeyboardButton("🇺🇸 English", callback_data="lang_en")],
        [InlineKeyboardButton("🌐 Web Site", url="https://www.irvustoken.xyz"), InlineKeyboardButton("🐦 Twitter (X)", url="https://x.com/IRVUSTOKEN")]
    ])

# --- ALIM SNIPER ---
async def track_buys(context: ContextTypes.DEFAULT_TYPE):
    # Bu fonksiyon 30 saniyede bir arkada çalışır
    global db
    if not db.get("ca"): return # Kurulum yoksa hiçbir şey yapma
    
    try:
        r = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{db['ca']}", timeout=5).json()
        if not r.get('pairs'): return
        p = r['pairs'][0]
        vol = float(p.get('volume', {}).get('h24', 0))
        
        # Eğer hacim arttıysa yeni alım vardır
        if db.get("last_vol", 0) > 0 and vol > db["last_vol"]:
            diff = vol - db["last_vol"]
            if diff > 10: # 10 dolar üzerindeki artışları "Alım" say
                symbol = p['baseToken']['symbol']
                price = p['priceUsd']
                m_cap = p.get('fdv', 0)
                
                # Alım Mesajını Oluştur
                txt = f"🟢 **{symbol} NEW BUY!**\n{'🟢'*5}\n\n" \
                      f"💰 Buy: `${int(diff):,}`\n💵 Price: `${price}`\n💎 MCap: `${int(m_cap):,}`\n\n" \
                      f"📈 [Grafik](p['url'])"
                
                # Senin Resmi Gönder
                if db.get("chat_id"):
                    await context.bot.send_photo(db["chat_id"], photo=BUY_IMAGE, caption=txt, parse_mode='Markdown')
        
        # Yeni hacmi kaydet
        db["last_vol"] = vol
        save_config(db) # Dosyaya yaz
    except Exception: continue

# --- KOMUTLAR ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚀 **Irvus Pro Bot Online!**\n\nLütfen bir dil seçin veya kurulum yapın.\n⚙️ `/add` | 💰 `/fiyat` | 🖼 `/ciz`", reply_markup=get_start_buttons(), parse_mode='Markdown')

async def add_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Kurulumu başlat, hafızaya chat_id'yi yaz
    chat_id = str(update.effective_chat.id)
    global db
    db.update({"chat_id": chat_id, "step": "WAIT_NET", "pairs": []})
    save_config(db)
    
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("Ethereum", callback_data="net_ETH"), InlineKeyboardButton("BSC", callback_data="net_BSC"), InlineKeyboardButton("Base", callback_data="net_BASE")]])
    await update.message.reply_text("➡️ **Select Chain:**", reply_markup=kb)

async def price_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Kurulan havuzun fiyatını çek
    if not db.get("ca"): return await update.message.reply_text("❌ Önce `/add` yapmalısın.")
    try:
        r = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{db['ca']}").json()
        p = r['pairs'][0]
        msg = f"💎 **{p['baseToken']['symbol']}**\n💰 Price: `${p['priceUsd']}`\n📊 24h: %{p['priceChange']['h24']}"
        await update.message.reply_text(msg)
    except: pass

async def draw_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # AI Resim Çizme
    p = " ".join(context.args)
    if not p: return await update.message.reply_text("❌ Örn: `/ciz uzay` yazmalısın.")
    await update.message.reply_text("🎨 Drawing...")
    await update.message.reply_photo(f"https://image.pollinations.ai/prompt/{p.replace(' ','%20')}?nologo=true")

# --- CALLBACKS ---
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    global db

    if query.data.startswith("lang_"):
        l = query.data.split("_")[1]
        txt = "Daha hızlı kurulum için `/add` yazın." if l == "tr" else "Type `/add` for fast setup."
        await query.edit_message_text(f"✅ Language: {l.upper()}\n\n{txt}")

    elif query.data.startswith("net_"):
        db["step"] = "WAIT_CA"
        save_config(db)
        await query.edit_message_text(f"🟡 **{query.data[2:].upper()} Token Address?**")

    elif query.data.startswith("idx_"):
        # Havuzu seç ve betona göm
        idx = int(query.data.split("_")[1])
        pair = db["pairs"][idx]
        db.update({"ca": pair['addr'], "step": "DONE", "last_vol": 0, "pairs": []})
        save_config(db) # Dosyaya kaydet
        await query.edit_message_text(f"✅ **{pair['sym']}** Setup Done! Bot now tracks buys.")

# --- MESSAGES ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = update.message.text.strip()
    global db

    if db.get("step") == "WAIT_CA":
        try:
            r = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{txt}", timeout=10).json()
            pairs = r.get('pairs', [])
            db["pairs"] = [{"addr": p['pairAddress'], "sym": p['baseToken']['symbol']} for p in pairs[:5]]
            save_config(db)
            
            btns = [[InlineKeyboardButton(f"✅ {p['baseToken']['symbol']} / {p['quoteToken']['symbol']}", callback_data=f"idx_{i}")] for i, p in enumerate(pairs[:5])]
            db["step"] = "SELECT_PAIR"
            save_config(db)
            await update.message.reply_text("ℹ️ Select Pair Listed Below:", reply_markup=InlineKeyboardMarkup(btns))
        except: await update.message.reply_text("❌ Error.")

if __name__ == '__main__':
    Thread(target=run_web, daemon=True).start()
    app_tg = Application.builder().token(TOKEN).build()
    app_tg.add_handler(CommandHandler("start", start))
    app_tg.add_handler(CommandHandler("add", add_command))
    app_tg.add_handler(CommandHandler(["fiyat", "p"], price_command))
    app_tg.add_handler(CommandHandler(["ciz", "draw"], draw_command))
    app_tg.add_handler(CallbackQueryHandler(handle_callback))
    app_tg.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # 30 saniyede bir alımları kontrol et
    if app_tg.job_queue:
        app_tg.job_queue.run_repeating(track_buys, interval=30, first=10)
        
    app_tg.run_polling(drop_pending_updates=True)
    
