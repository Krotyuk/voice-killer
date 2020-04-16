from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
import subprocess
from io import BytesIO
from files_handler import save_file
import os
from config import TOKEN
from to_wav import oga_to_wav_convert
import speech_recognition as speech_recog


bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

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
        await message.reply(recog.recognize_google(audio_content,  language="ru-RU"))
        os.remove(wav_path)
    except Exception as e:
        await message.reply("Непонятно( " + str(e))
        os.remove(wav_path)




if __name__ == '__main__':
    executor.start_polling(dp)