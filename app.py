import os, requests
from flask import Flask
from threading import Thread
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler

app = Flask(__name__)
@app.route('/')
def home(): return "IRVUS V43 ONLINE", 200

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- AYARLAR ---
TOKEN = "8621050385:AAGA6wcxbFY2rqJ9gjXVK_JNqsebJvTv_Jo"
IRVUS_CA = "0x31EDA2dfd01c9C65385cCE6099B24b06ef3aE831"

# --- KOMUTLAR ---
def start(update, context):
    kb = [[InlineKeyboardButton("🌐 Web Site", url="https://www.irvustoken.xyz")],
          [InlineKeyboardButton("🐦 Twitter (X)", url="https://x.com/IRVUSTOKEN")]]
    update.message.reply_text(
        "🛡 **Irvus Token Bot Aktif!**\n\n"
        "💰 `/fiyat` - Güncel Irvus fiyatını gösterir.\n"
        "🎨 `/ciz` - Yazdığınız şeyi resme dönüştürür.",
        reply_markup=InlineKeyboardMarkup(kb)
    )

def price(update, context):
    try:
        r = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{IRVUS_CA}", timeout=10).json()
        p = r['pairs'][0]
        msg = f"💎 **IRVUS FİYAT**\n\n💰 `${p['priceUsd']}`\n📊 24s: %{p['priceChange']['h24']}\n💠 MCap: `${int(p.get('fdv', 0)):,}`"
        update.message.reply_text(msg, parse_mode='Markdown')
    except:
        update.message.reply_text("❌ Veri şu an alınamıyor, az sonra tekrar deneyin.")

def draw(update, context):
    prompt = " ".join(context.args)
    if not prompt:
        return update.message.reply_text("❌ Örnek kullanım: `/ciz yeşil savaşçı` (Yanına ne çizeceğinizi yazın).")
    
    update.message.reply_text("🎨 **AI Çiziyor...**")
    try:
        url = f"https://image.pollinations.ai/prompt/{prompt.replace(' ', '%20')}?nologo=true"
        update.message.reply_photo(photo=url, caption=f"🖼 **Görsel:** {prompt}")
    except:
        update.message.reply_text("❌ Çizim başarısız oldu.")

if __name__ == '__main__':
    # Web sunucusu Render'ın botu kapatmasını önler
    Thread(target=run_web, daemon=True).start()
    
    # En stabil sürüm olan v13 yapısıyla botu başlatıyoruz
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler(["fiyat", "p", "price"], price))
    dp.add_handler(CommandHandler(["ciz", "draw"], draw))
    
    print("Bot yayında!")
    updater.start_polling()
    updater.idle()
    
