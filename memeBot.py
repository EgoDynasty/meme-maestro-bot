from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import random
import asyncio
import re
import os
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, db
from http.server import BaseHTTPRequestHandler, HTTPServer

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

class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

def run_dummy_server():
    port = int(os.getenv("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), DummyHandler)
    print(f"Dummy server running on port {port}")
    server.serve_forever()

if __name__ == "__main__":
    import threading
    threading.Thread(target=run_dummy_server, daemon=True).start()

# Получаем токен
TOKEN = os.getenv("TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Я Meme Maestro! Кидай рилсы/шортсы или видео с подписью 'save', я сохраню через пару минут. Пиши 'Скука' для случайного мема!")

async def get_meme(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text
    match = re.match(r"!get meme (-?\d+) (\d+)", text)
    if not match:
        await update.message.reply_text("Используйте: !get meme <chat_id> <message_id>")
        return
    
    chat_id, message_id = map(int, match.groups())
    snapshot = ref.get()
    
    if snapshot:
        for meme_id, meme in snapshot.items():
            if meme["chat_id"] == chat_id and meme["message_id"] == message_id:
                try:
                    await context.bot.forward_message(
                        chat_id=update.message.chat_id,
                        from_chat_id=chat_id,
                        message_id=message_id
                    )
                    await update.message.reply_text(f"Мем от @{meme['author']}!\nID: {message_id}")
                    return
                except Exception as e:
                    await update.message.reply_text(f"Не смог переслать мем: {str(e)}")
                    return
    await update.message.reply_text("Мем не найден в базе!")

async def del_meme(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text
    match = re.match(r"!del meme (-?\d+) (\d+)", text)
    if not match:
        await update.message.reply_text("Используйте: !del meme <chat_id> <message_id>")
        return
    
    chat_id, message_id = map(int, match.groups())
    snapshot = ref.get()
    
    if snapshot:
        for meme_id, meme in snapshot.items():
            if meme["chat_id"] == chat_id and meme["message_id"] == message_id:
                try:
                    ref.child(meme_id).delete()
                    await update.message.reply_text(f"Мем с ID {message_id} удален из базы!")
                    return
                except Exception as e:
                    await update.message.reply_text(f"Ошибка при удалении мема: {str(e)}")
                    return
    await update.message.reply_text("Мем не найден в базе!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    allowed_domains = ["https://www.ddinstagram", "https://www.youtube.com/shorts", "https://youtube.com/shorts"]
    text = update.message.text or update.message.caption or ""  # Проверяем текст и подпись к видео

    savememe_found = re.search(r"save", text, re.IGNORECASE) is not None
    domain_found = any(domain in text for domain in allowed_domains)

    has_video = update.message.video is not None
    
    if (domain_found or (savememe_found and has_video)):
        meme_data = {
            "chat_id": update.message.chat_id,
            "message_id": update.message.message_id,
            "author": update.message.from_user.username or update.message.from_user.first_name
        }
        await asyncio.sleep(120)  # Задержка перед сохранением

        bot_chat_id = -1002639508484  # ID вашей группы для логов
        try:
            copied_message = await context.bot.copy_message(
                chat_id=bot_chat_id,
                from_chat_id=meme_data["chat_id"],
                message_id=meme_data["message_id"],
                disable_notification=True
            )
            # Если копирование удалось, сообщение существует, сохраняем в Firebase
            try:
                ref.push(meme_data)
                print(f"Мем сохранен: {meme_data}")
            except Exception as e:
                print(f"Ошибка при сохранении в Firebase: {e}")
            # Удаляем скопированное сообщение
            await context.bot.delete_message(
                chat_id=bot_chat_id,
                message_id=copied_message.message_id
            )
        except Exception as e:
            print(f"Сообщение удалено или недоступно: {e}")
            return  # Прерываем выполнение, если сообщение удалено

    if "скука" in text.lower(): # "Реакция на сообщение"
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
                await update.message.reply_text(f"Мем от @{meme['author']}!\nID: {meme['message_id']}")
            except Exception as e:
                await update.message.reply_text(f"Не смог переслать мем: {str(e)}")
        else:
            await update.message.reply_text("Мемов нет, увы! 😢")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Regex(r'^!get meme\s+-?\d+\s+\d+'), get_meme))
    app.add_handler(MessageHandler(filters.Regex(r'^!del meme\s+-?\d+\s+\d+'), del_meme))
    app.add_handler(MessageHandler(filters.TEXT | filters.VIDEO, handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()