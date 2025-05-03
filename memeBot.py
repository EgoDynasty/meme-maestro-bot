from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import random
import asyncio
import re
import os
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, db

# Загружаем переменные окружения
load_dotenv()

# Инициализируем Firebase
cred = credentials.Certificate({
    "type": "service_account",
    "project_id": os.getenv("FIREBASE_PROJECT_ID"),
    "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
    "private_key": os.getenv("FIREBASE_PRIVATE_KEY").replace('\\n', '\n'),
    "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
    "client_id": os.getenv("FIREBASE_CLIENT_ID"),
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": os.getenv("FIREBASE_CLIENT_X509_CERT_URL") or f"https://www.googleapis.com/robot/v1/metadata/x509/{os.getenv('FIREBASE_CLIENT_EMAIL').replace('@', '%40')}"
})

firebase_admin.initialize_app(cred, {
    'databaseURL': os.getenv("FIREBASE_DATABASE_URL")
})

ref = db.reference('/memes')  # ссылка на базу данных

# Получаем токен
TOKEN = os.getenv("TOKEN")

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
    
    if (domain_found or (savememe_found and has_video)):  # Сохраняем только если есть savememe и видео или домен
        meme_data = {
            "chat_id": update.message.chat_id,
            "message_id": update.message.message_id,
            "author": update.message.from_user.username or update.message.from_user.first_name
        }
        await asyncio.sleep(5)  # Задержка перед сохранением
        try:
            ref.push(meme_data)  # Сохраняем в Firebase
        except Exception as e:
            print(f"Ошибка при сохранении в Firebase: {e}")
    
    # Реакция на "Скука"
    if "скука" in text.lower():
        snapshot = ref.get()
        if snapshot:
            memes = list(snapshot.values())
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