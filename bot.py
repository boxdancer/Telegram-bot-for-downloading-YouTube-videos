import asyncio
import re
import aiohttp
import yt_dlp
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import FSInputFile


class YouTubeBot:
    def __init__(self, token):
        self.bot = Bot(token=token)
        self.dp = Dispatcher()
        self.setup_handlers()

    def setup_handlers(self):
        self.dp.message.register(self.start_cmd, Command('start'))
        self.dp.message.register(self.download_audio, Command('audio'))
        self.dp.message.register(self.download_video, Command('video'))
        self.dp.message.register(self.default_response)

    async def start_cmd(self, message: types.Message):
        await message.answer(
            'Привет! Присылай ссылку на YouTube видео.'
            ' \n Для получения аудиофайла используй команду: \n  /audio(пробел)"Ссылка на видео"'
            ' \n Для получения видеофайла используй команду: \n  /video(пробел)"Ссылка на видео"'
        )

    async def check_youtube_link(self, url):
        youtube_regex = r'(https?://www\.youtube\.com/(watch\?v=|shorts/)|https?://youtu\.be/)([a-zA-Z0-9_-]{11})'
        if not re.match(youtube_regex, url):
            return False, "Некорректный формат ссылки."

        async with aiohttp.ClientSession() as session:
            async with session.head(url, allow_redirects=True) as response:
                if response.status == 200:
                    return True, "Ссылка корректна, пробую скачать контент."
                else:
                    return False, "Видео не найдено или ссылка недоступна."

    async def download_content(self, url, is_audio=True):
        output_dir = 'YouTube_downloaded_videos'
        os.makedirs(output_dir, exist_ok=True)

        if is_audio:
            ydl_opts = {
                'ratelimit': 10 * 1024 * 1024,  # Максимальная скорость загрузки 10 Мб/с
                'max_filesize': 700 * 1024 * 1024,  # Максимальный размер файла 700 Мб
                'format': 'bestaudio/best',  # Загрузка лучшего доступного аудио
                'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),  # Шаблон имени файла и директории сохранения
                'retries': 5,  # Количество повторных попыток
                'http_chunk_size': 10485760,  # Размер куска (10MB)
                'socket_timeout': 30,  # Тайм-аут сокета (в секундах)
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': 192,
                }],
            }
        else:
            ydl_opts = {
                'ratelimit': 10 * 1024 * 1024,
                'max_filesize': 700 * 1024 * 1024,
                'format': 'bestvideo[height<=144]+bestaudio/best',
                'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
                'retries': 5,  # Количество повторных попыток
                'http_chunk_size': 10485760,  # Размер куска (10MB)
                'socket_timeout': 30,  # Тайм-аут сокета (в секундах)
                'postprocessors': [{
                    'key': 'FFmpegVideoConvertor',
                    'preferedformat': 'mp4',
                }],
            }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info_dict)
            if is_audio:
                file_path = file_path.replace('.webm', '.mp3').replace('.m4a', '.mp3')
            else:
                file_path = file_path.replace('.webm', '.mp4').replace('.mkv', '.mp4')

        return file_path

    async def download_and_send_content(self, url, chat_id, is_audio=True):
        file_path = await self.download_content(url, is_audio)
        if is_audio:
            audio = FSInputFile(file_path)
            await self.bot.send_audio(chat_id, audio)
        else:
            video = FSInputFile(file_path)
            await self.bot.send_video(chat_id, video)

    async def download_audio(self, message: types.Message):
        url = message.text.split(' ', 1)[1] if ' ' in message.text else ''
        is_valid, reply_message = await self.check_youtube_link(url)
        await message.answer(reply_message)

        if is_valid:
            asyncio.create_task(self.download_and_send_content(url, message.chat.id, is_audio=True))

    async def download_video(self, message: types.Message):
        url = message.text.split(' ', 1)[1] if ' ' in message.text else ''
        is_valid, reply_message = await self.check_youtube_link(url)
        await message.answer(reply_message)

        if is_valid:
            asyncio.create_task(self.download_and_send_content(url, message.chat.id, is_audio=False))

    async def default_response(self, message: types.Message):
        await message.answer(
            'Бот позволяет скачать видео из YouTube или его звук (аудиокнигу, музыку и.т.д)'
            ' \n    Для получения видеофайла используй команду: \n  /video(пробел)"Ссылка на видео"'
            ' \n    Для получения аудиофайла используй команду: \n  /audio(пробел)"Ссылка на видео"'
            ' \n Пример команды:\n    /video https://www.youtube.com/shorts/4sNo7A6QLoQ'
        )

    async def run(self):
        await self.dp.start_polling(self.bot, skip_updates=True)


if __name__ == '__main__':
    token = '111111111111111111111111111111111111111111111111111111111111'  # Enter your bot Token from BotFather
    youtube_bot = YouTubeBot(token)
    asyncio.run(youtube_bot.run())
