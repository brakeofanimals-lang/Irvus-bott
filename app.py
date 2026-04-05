import os
import requests
from flask import Flask
from threading import Thread
from telegram import Update, ParseMode
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Render için web sunucusu
app = Flask(__name__)
@app.route('/')
def home(): return "IRVUS CORE AKTIF", 200

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- AYARLAR ---
TOKEN = "8621050385:AAESXIZLT6HbS3CGeT-sT-HJcgvFuJF8ff0"
IRVUS_CA = "0x31EDA2dfd01c9C65385cCE6099B24b06ef3aE831"
filtered_words = []

# --- KOMUTLAR ---

def fiyat(update: Update, context: CallbackContext):
    try:
        r = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{IRVUS_CA}").json()
        f = r['pairs'][0]['priceUsd']
        update.message.reply_text(f"💎 **$IRVUS Fiyat:** `${f}`", parse_mode=ParseMode.MARKDOWN)
    except:
        update.message.reply_text("❌ Fiyat şu an alınamadı.")

def ciz(update: Update, context: CallbackContext):
    prompt = " ".join(context.args)
    if not prompt:
        update.message.reply_text("❌ Örn: /ciz warrior")
        return
    update.message.reply_text(f"🎨 **'{prompt}'** çiziliyor...")
    url = f"https://image.pollinations.ai/prompt/{prompt.replace(' ', '%20')}?nologo=true"
    update.message.reply_photo(photo=url, caption=f"🖼 AI: {prompt}")

def filter_cmd(update: Update, context: CallbackContext):
    word = " ".join(context.args).lower()
    if word and word not in filtered_words:
        filtered_words.append(word)
        update.message.reply_text(f"✅ Filtreye eklendi: {word}")

def message_check(update: Update, context: CallbackContext):
    if not update.message or not update.message.text: return
    text = update.message.text.lower()
    for w in filtered_words:
        if w in text:
            update.message.delete()
            break

# --- ANA ÇALIŞTIRICI ---
if __name__ == '__main__':
    Thread(target=run_web, daemon=True).start()
    
    # Eski nesil Updater yapısı (v13.15 için)
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    
    dp.add_handler(CommandHandler(["fiyat", "p"], fiyat))
    dp.add_handler(CommandHandler(["ciz", "draw"], ciz))
    dp.add_handler(CommandHandler("filter", filter_cmd))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, message_check))
    
    print(">>> BOT SIFIRLANDI VE AKTIF")
    updater.start_polling(drop_pending_updates=True)
    updater.idle()
    
