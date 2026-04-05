import sys, types, sqlite3, requests, os
from flask import Flask, request

# --- PYTHON 3.13 YAMASI ---
m_img = types.ModuleType('imghdr'); m_img.what = lambda x, h=None: None; sys.modules['imghdr'] = m_img

from telegram import Update, Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters

# --- AYARLAR ---
TOKEN = "8621050385:AAGFTwrCTwa-Ai-ywmzO6BOqo2J2wLTRHdg"
# BURAYI DOLDUR: Senin Hugging Face Space adın (URL kısmındaki tam isim)
# Örnek: https://huggingface.co/spaces/Knclk/Irvus-bot ise URL şudur:
URL = "https://knclk-irvus-bot.hf.space" 

app = Flask(__name__)
bot = Bot(TOKEN)

# --- VERİTABANI ---
conn = sqlite3.connect('filtreler.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS filtreler (anahtar TEXT PRIMARY KEY, cevap TEXT)')
conn.commit()

# --- BOT MANTIĞI ---
def get_token_data():
    try:
        api = f"https://api.dexscreener.com/latest/dex/tokens/0x31EDA2dfd01c9C65385cCE6099B24b06ef3aE831"
        res = requests.get(api).json()
        pair = res['pairs'][0]
        fiyat = pair.get('priceUsd', '0.00')
        degisim = pair.get('priceChange', {}).get('h24', '0.00')
        emoji = "🚀" if float(degisim) > 0 else "📉"
        return pair.get('url'), f"💎 **$IRVUS**\n💰 Fiyat: ${fiyat}\n{emoji} 24s Değişim: %{degisim}"
    except: return None, "❌ Veri hatası."

def fiyat_gonder(update, context):
    link, msg = get_token_data()
    if link: update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📈 Grafik", url=link)]]), parse_mode='Markdown')
    else: update.message.reply_text(msg)

def mesaj_kontrol(update, context):
    if not update.message or not update.message.text: return
    text = update.message.text.lower()
    res = cursor.execute('SELECT anahtar, cevap FROM filtreler').fetchall()
    for anahtar, cevap in res:
        if anahtar in text:
            update.message.reply_text(cevap)
            break

# --- WEBHOOK AYARLARI ---
@app.route(f'/{TOKEN}', methods=['POST'])
def respond():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return 'ok'

@app.route('/')
def index(): return "Bot Aktif!"

# Dispatcher Kurulumu
dispatcher = Dispatcher(bot, None, workers=0, use_context=True)
dispatcher.add_handler(CommandHandler("fiyat", fiyat_gonder))
dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, mesaj_kontrol))

# Webhook'u Telegram'a Tanıt
bot.set_webhook(url=f"{URL}/{TOKEN}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7860)
