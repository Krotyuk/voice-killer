from aiogram import Bot, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher import Dispatcher
from aiohttp import web
from io import BytesIO
from aiogram.dispatcher.webhook import get_new_configured_app

import os
import ssl
import logging

import speech_recognition as speech_recog

from config import API_TOKEN, WEBHOOK_PORT, WEBHOOK_URL_BASE, WEBHOOK_URL_PATH, WEBHOOK_SSL_CERT, \
WEBHOOK_LISTEN, WEBHOOK_SSL_PRIV
from to_wav import oga_to_wav_convert
from files_handler import save_file

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())
app = web.Application()

@dp.message_handler(commands=['start'])
async def process_start_command(message: types.Message):
    await message.reply("Привет!\nОтправь мне голосовуху, а я тебе скину текст!")

@dp.message_handler(content_types=["voice"])
async def voice_safe(message: types.Message):
    template_file = BytesIO()
    file_for_download = await message.voice.get_file()
    await file_for_download.download(template_file)
    template_file.seek(0)

    user_id = message.from_user.id
    file_id = message.voice.file_unique_id

    file_extension = file_for_download['file_path'].split('.')[-1]
    save_path = os.path.join('voice_files', f'{user_id}', f'{file_id}.{file_extension}')
    save_file(template_file, save_path)

    wav_path = os.path.join('voice_wav_files', f'{user_id}', f'{file_id}.wav')
    oga_to_wav_convert(save_path, wav_path)
    os.remove(save_path)
    sample_audio = speech_recog.AudioFile(wav_path)
    recog = speech_recog.Recognizer()

    with sample_audio as audio_file:
        recog.adjust_for_ambient_noise(audio_file)
        audio_content = recog.record(audio_file)

    try:
        await message.reply(recog.recognize_google(audio_content, language="ru-RU"))
        os.remove(wav_path)
    except Exception as e:
        await  message.reply("Непонятно( " + str(e))
        os.remove(wav_path)

async def on_startup(dp):
    webhook = await bot.get_webhook_info()
    if webhook.url != WEBHOOK_URL_BASE:
        if not webhook.url:
            await bot.delete_webhook()
        await bot.set_webhook(WEBHOOK_URL_BASE, certificate=open(WEBHOOK_SSL_CERT, 'rb'))

async def on_shutdown(dp):
    logging.warning('Хм неполадки..')
    await bot.delete_webhook()
    logging.warning('Пока!')

if __name__ == '__main__':

    app = get_new_configured_app(dispatcher=dp, path=WEBHOOK_URL_PATH)

    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)


    context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    context.load_cert_chain(WEBHOOK_SSL_CERT, WEBHOOK_SSL_PRIV)

    web.run_app(app, host=WEBHOOK_LISTEN, port=WEBHOOK_PORT, ssl_context=context)