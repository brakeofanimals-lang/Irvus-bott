import os, requests, asyncio
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes

app = Flask(__name__)
@app.route('/')
def home(): return "OK", 200

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# AYARLAR
TOKEN = "8621050385:AAGA6wcxbFY2rqJ9gjXVK_JNqsebJvTv_Jo"
TOKEN_ADRESI = "0x31EDA2dfd01c9C65385cCE6099B24b06ef3aE831"
HF_TOKEN = "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"

# DAHA HIZLI VE KARARLI MODEL
API_URL = "https://api-inference.huggingface.co/models/runwayml/stable-diffusion-v1-5"

async def fiyat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        r = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{TOKEN_ADRESI}", timeout=5).json()
        p = r['pairs'][0]
        msg = f"💎 **$IRVUS Güncel Durum**\n\n💰 Fiyat: `${p.get('priceUsd')}`\n📈 24s: `%{p.get('priceChange', {}).get('h24')}`"
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("📈 Grafik", url=p.get('url'))]])
        await update.message.reply_text(msg, reply_markup=kb, parse_mode='Markdown')
    except: await update.message.reply_text("❌ Fiyat hatası.")

async def ciz_arka_plan(update, prompt):
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    payload = {"inputs": prompt, "options": {"wait_for_model": True}}
    
    # 3 KEZ DENEME DÖNGÜSÜ (Model uyanana kadar pes etmez)
    for i in range(3):
        try:
            res = requests.post(API_URL, headers=headers, json=payload, timeout=60)
            if res.status_code == 200:
                await update.message.reply_photo(photo=res.content, caption=f"🖼 **AI Sonucu:** {prompt}")
                return
            elif res.status_code == 503: # Model uyanıyor demektir
                if i < 2:
                    await asyncio.sleep(10) # 10 saniye bekle ve tekrar dene
                    continue
        except: pass
    
    await update.message.reply_text("💤 AI şu an gerçekten çok yoğun, lütfen 1 dakika sonra tekrar /ciz yazın.")

async def ciz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = " ".join(context.args)
    if not prompt: return
    await update.message.reply_text(f"🎨 **'{prompt}'** hazırlanıyor... Lütfen bekleyin.")
    asyncio.create_task(ciz_arka_plan(update, prompt))

if __name__ == '__main__':
    Thread(target=run_web, daemon=True).start()
    bot = Application.builder().token(TOKEN).build()
    bot.add_handler(CommandHandler("fiyat", fiyat))
    bot.add_handler(CommandHandler("ciz", ciz))
    bot.run_polling(drop_pending_updates=True)
    
