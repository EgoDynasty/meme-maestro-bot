from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import json
import random
import asyncio
import re

TOKEN = "8042122102:AAFF_vIYx-HoUPxhhbyH_Y3cADF_CC1nYmI"

memes = []
try:
    with open("memes.json", "r") as f:
        memes = json.load(f)
except FileNotFoundError:
    memes = []
except json.JSONDecodeError:
    print("Ошибка чтения JSON, начинаем с пустого списка")
    memes = []

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Я Meme Maestro! Кидай рилсы/шортсы или видео с подписью 'savememe', я сохраню через 5 сек. Пиши 'Скука' для случайного мема!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    allowed_domains = ["https://www.ddinstagram", "https://www.youtube.com/shorts", "https://youtube.com/shorts"]
    text = update.message.text or update.message.caption or ""  # Проверяем текст и подпись к видео
    
    # Проверка на savememe или домены
    savememe_found = re.search(r"save", text, re.IGNORECASE) is not None
    domain_found = any(domain in text for domain in allowed_domains)
    
    # Проверяем наличие видео
    has_video = update.message.video is not None
    
    if (domain_found) or (savememe_found and has_video):  # Сохраняем только если есть savememe и видео или домен
        meme_data = {
            "chat_id": update.message.chat_id,
            "message_id": update.message.message_id,
            "author": update.message.from_user.username or update.message.from_user.first_name
        }
        await asyncio.sleep(120)  # Задержка 120 секунд
        try:
            memes.append(meme_data)
            with open("memes.json", "w", encoding="utf-8") as f:
                json.dump(memes, f, indent=2, ensure_ascii=False)
        except:
            pass
    
    # Реакция на "Скука"
    if "скука" in text.lower():
        if memes:
            meme = random.choice(memes)
            try:
                await context.bot.forward_message(
                    chat_id=update.message.chat_id,
                    from_chat_id=meme["chat_id"],
                    message_id=meme["message_id"]
                )
                await update.message.reply_text(f"Мем от @{meme['author']}!")
            except Exception as e:
                await update.message.reply_text(f"Не смог переслать мем: {str(e)}")
        else:
            await update.message.reply_text("Мемов нет, увы! 😢")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT | filters.VIDEO, handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()