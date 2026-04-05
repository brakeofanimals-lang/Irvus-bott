async def draw_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Kullanıcı sadece /ciz yazarsa uyar
    if not context.args:
        return await update.message.reply_text("❌ **Eksik Kullanım!**\nÖrnek: `/ciz yeşil bir ejderha` yazmalısın.")
    
    prompt = " ".join(context.args)
    await update.message.reply_text(f"🎨 **'{prompt}'** için resim çiziliyor, lütfen bekleyin...")
    
    try:
        # AI Servis Linki (Boşlukları %20 ile dolduruyoruz ki hata vermesin)
        encoded_prompt = prompt.replace(' ', '%20')
        img_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true"
        
        # Resmi gönder
        await update.message.reply_photo(
            photo=img_url, 
            caption=f"🖼 **AI Çizimi Tamamlandı!**\n🎨 Komut: `{prompt}`",
            parse_mode='Markdown'
        )
    except Exception as e:
        await update.message.reply_text(f"❌ **Çizim Hatası:** AI şu an meşgul veya bir sorun oluştu. Hata: {e}")
        
