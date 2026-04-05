import os, requests, asyncio
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes

app = Flask(__name__)
@app.route('/')
def home(): return "MULTI-TOKEN BUY BOT ONLINE", 200

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- AYARLAR ---
TOKEN = "8621050385:AAGA6wcxbFY2rqJ9gjXVK_JNqsebJvTv_Jo"

# Grupların hangi tokenı takip ettiğini tutan hafıza
# Format: { grup_id: {"address": "0x...", "last_vol": 0} }
group_settings = {}

# --- FONKSİYONLAR ---

async def set_token(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gruba özel token ayarlar: /set_token 0x..."""
    if not context.args:
        await update.message.reply_text("❌ Lütfen kontrat adresini yazın.\nÖrn: `/set_token 0x123...`", parse_mode='Markdown')
        return
    
    chat_id = str(update.effective_chat.id)
    token_address = context.args[0]
    
    group_settings[chat_id] = {
        "address": token_address,
        "last_vol": 0
    }
    
    await update.message.reply_text(f"✅ **Bot bu grup için ayarlandı!**\n\nTakip edilen kontrat:\n`{token_address}`", parse_mode='Markdown')

async def alimlari_tara(context: ContextTypes.DEFAULT_TYPE):
    """Tüm kayıtlı grupları tek tek gezer ve alım var mı bakar."""
    for chat_id, data in group_settings.items():
        try:
            addr = data["address"]
            url = f"https://api.dexscreener.com/latest/dex/tokens/{addr}"
            res = requests.get(url, timeout=10).json()
            p = res['pairs'][0]
            
            current_vol = float(p.get('volume', {}).get('h24', 0))
            
            if data["last_vol"] > 0 and current_vol > data["last_vol"]:
                fiyat = p.get('priceUsd', '0')
                mcap = p.get('fdv', '0')
                symbol = p.get('baseToken', {}).get('symbol', 'TOKEN')
                
                msg = (
                    f"🚀 **{symbol} YENİ ALIM!** 🚀\n"
                    f"🟢🟢🟢🟢🟢🟢🟢🟢🟢\n\n"
                    f"💰 **Fiyat:** ${fiyat}\n"
                    f"💎 **MCAP:** ${mcap:,}\n"
                    f"📊 **Hacim:** ${current_vol:,}"
                )
                kb = InlineKeyboardMarkup([[InlineKeyboardButton("📈 Grafik", url=p.get('url'))]])
                await context.bot.send_message(chat_id=chat_id, text=msg, reply_markup=kb, parse_mode='Markdown')
            
            group_settings[chat_id]["last_vol"] = current_vol
        except: continue

async def fiyat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    if chat_id not in group_settings:
        await update.message.reply_text("❌ Önce `/set_token [adres]` ile token kurmalısın.")
        return
    
    try:
        addr = group_settings[chat_id]["address"]
        r = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{addr}").json()
        p = r['pairs'][0]
        msg = f"💎 **{p['baseToken']['symbol']}**\n💰 Fiyat: `${p['priceUsd']}`\n📈 24s: `%{p['priceChange']['h24']}`"
        await update.message.reply_text(msg, parse_mode='Markdown')
    except: await update.message.reply_text("❌ Veri hatası.")

async def ciz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = " ".join(context.args)
    if not prompt: return
    img = f"https://image.pollinations.ai/prompt/{prompt.replace(' ', '%20')}?width=1024&height=1024&nologo=true"
    await update.message.reply_photo(photo=img, caption=f"🖼 **AI:** {prompt}")

# --- MOTOR ---
if __name__ == '__main__':
    Thread(target=run_web, daemon=True).start()
    app_tg = Application.builder().token(TOKEN).build()
    
    app_tg.add_handler(CommandHandler("set_token", set_token))
    app_tg.add_handler(CommandHandler("fiyat", fiyat))
    app_tg.add_handler(CommandHandler("ciz", ciz))
    
    # 30 saniyede bir tüm grupları denetle
    app_tg.job_queue.run_repeating(alimlari_tara, interval=30, first=5)
    
    app_tg.run_polling(drop_pending_updates=True)
    
