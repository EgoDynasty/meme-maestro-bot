import os
import asyncio
import re
import random
import yt_dlp
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from firebase_admin import credentials, db, initialize_app
from dotenv import load_dotenv
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

initialize_app(cred, {
    'databaseURL': os.getenv("FIREBASE_DATABASE_URL")
})

ref = db.reference('/memes')

# Дамми-сервер
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

# Функция для скачивания YouTube Shorts
async def download_youtube_shorts(url: str, output_path: str = "video.mp4") -> str:
    ydl_opts = {
        'format': 'best',
        'outtmpl': output_path,
        'quiet': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return output_path
    except Exception as e:
        print(f"Ошибка скачивания видео: {e}")
        return None

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Я Meme Maestro! Кидай рилсы/шортсы или видео с подписью 'save', я сохраню через пару минут. Пиши 'Скука' для случайного мема!")

# Команда !get meme
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
                    forwarded_message = await context.bot.forward_message(
                        chat_id=update.message.chat_id,
                        from_chat_id=chat_id,
                        message_id=message_id
                    )
                    forwarded_text = forwarded_message.caption or forwarded_message.text or ""
                    shorts_url = None
                    for domain in ["https://www.youtube.com/shorts", "https://youtube.com/shorts"]:
                        match = re.search(rf"({domain}/[^\s]+)", forwarded_text)
                        if match:
                            shorts_url = match.group(1)
                            break

                    if shorts_url:
                        loading_message = await update.message.reply_text("Загрузка... 😎")
                        video_path = f"video_{message_id}.mp4"
                        downloaded_path = await download_youtube_shorts(shorts_url, video_path)
                        if downloaded_path and os.path.exists(downloaded_path):
                            with open(downloaded_path, 'rb') as video_file:
                                await context.bot.send_video(
                                    chat_id=update.message.chat_id,
                                    video=video_file,
                                    caption=f"Мем от @{meme['author']}!\nID: {message_id}"
                                )
                            await context.bot.delete_message(
                                chat_id=update.message.chat_id,
                                message_id=forwarded_message.message_id
                            )
                            await context.bot.delete_message(
                                chat_id=update.message.chat_id,
                                message_id=loading_message.message_id
                            )
                            os.remove(downloaded_path)
                        else:
                            await context.bot.delete_message(
                                chat_id=update.message.chat_id,
                                message_id=loading_message.message_id
                            )
                            await update.message.reply_text(
                                f"Не удалось скачать видео. Мем от @{meme['author']}!\nID: {message_id}"
                            )
                    else:
                        # Если нет Shorts, оставляем форвард
                        await update.message.reply_text(f"Мем от @{meme['author']}!\nID: {message_id}")
                    return
                except Exception as e:
                    await update.message.reply_text(f"Не смог переслать мем: {str(e)}")
                    return
    await update.message.reply_text("Мем не найден в базе!")

# Команда !del meme
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

# Обработка сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    allowed_domains = ["https://www.ddinstagram", "https://www.youtube.com/shorts", "https://youtube.com/shorts"]
    text = update.message.text or update.message.caption or ""

    savememe_found = re.search(r"save", text, re.IGNORECASE) is not None
    domain_found = any(domain in text for domain in allowed_domains)
    has_video = update.message.video is not None

    if (domain_found or (savememe_found and has_video)):
        meme_data = {
            "chat_id": update.message.chat_id,
            "message_id": update.message.message_id,
            "author": update.message.from_user.username or update.message.from_user.first_name
        }
        await asyncio.sleep(10)

        bot_chat_id = -1002639508484
        try:
            copied_message = await context.bot.copy_message(
                chat_id=bot_chat_id,
                from_chat_id=meme_data["chat_id"],
                message_id=meme_data["message_id"],
                disable_notification=True
            )
            try:
                ref.push(meme_data)
                print(f"Мем сохранен: {meme_data}")
            except Exception as e:
                print(f"Ошибка при сохранении в Firebase: {e}")
            await context.bot.delete_message(
                chat_id=bot_chat_id,
                message_id=copied_message.message_id
            )
        except Exception as e:
            print(f"Сообщение удалено или недоступно: {e}")
            return

    if "скука" in text.lower():
        snapshot = ref.get()
        if snapshot:
            memes = list(snapshot.values())
            meme = random.choice(memes)
            try:
                # Пересылаем мем
                forwarded_message = await context.bot.forward_message(
                    chat_id=update.message.chat_id,
                    from_chat_id=meme["chat_id"],
                    message_id=meme["message_id"]
                )
                # Проверяем, есть ли YouTube Shorts
                forwarded_text = forwarded_message.caption or forwarded_message.text or ""
                shorts_url = None
                for domain in ["https://www.youtube.com/shorts", "https://youtube.com/shorts"]:
                    match = re.search(rf"({domain}/[^\s]+)", forwarded_text)
                    if match:
                        shorts_url = match.group(1)
                        break

                if shorts_url:
                    loading_message = await update.message.reply_text("Загрузка... 😎")
                    video_path = f"video_{meme['message_id']}.mp4"
                    downloaded_path = await download_youtube_shorts(shorts_url, video_path)
                    if downloaded_path and os.path.exists(downloaded_path):
                        with open(downloaded_path, 'rb') as video_file:
                            await context.bot.send_video(
                                chat_id=update.message.chat_id,
                                video=video_file,
                                caption=f"Мем от @{meme['author']}!\nID: {meme['message_id']}"
                            )
                        # Удаляем форвард и сообщение о загрузке
                        await context.bot.delete_message(
                            chat_id=update.message.chat_id,
                            message_id=forwarded_message.message_id
                        )
                        await context.bot.delete_message(
                            chat_id=update.message.chat_id,
                            message_id=loading_message.message_id
                        )
                        os.remove(downloaded_path)
                    else:
                        await context.bot.delete_message(
                            chat_id=update.message.chat_id,
                            message_id=loading_message.message_id
                        )
                        await update.message.reply_text(
                            f"Не удалось скачать видео. Мем от @{meme['author']}!\nID: {meme['message_id']}"
                        )
                else:
                    await update.message.reply_text(f"Мем от @{meme['author']}!\nID: {meme['message_id']}")
            except Exception as e:
                await update.message.reply_text(f"Не смог переслать мем: {str(e)}")
        else:
            await update.message.reply_text("Мемов нет, увы! 😢")

def main():
    app = Application.builder().token(os.getenv("TOKEN")).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Regex(r'^!get meme\s+-?\d+\s+\d+'), get_meme))
    app.add_handler(MessageHandler(filters.Regex(r'^!del meme\s+-?\d+\s+\d+'), del_meme))
    app.add_handler(MessageHandler(filters.TEXT | filters.VIDEO, handle_message))
    app.run_polling()

if __name__ == "__main__":
    import threading
    threading.Thread(target=run_dummy_server, daemon=True).start()
    main()