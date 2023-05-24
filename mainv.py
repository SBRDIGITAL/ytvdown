import logging
from aiogram import Bot, Dispatcher, types, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ParseMode
from pytube import *
import os
import csv

TOKEN = 'WRITE UR TOKEN'

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

class VideoStates(StatesGroup):
    waiting_for_link = State()

@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    await message.reply("Привет! Я бот для скачивания видео. Используйте /help, чтобы узнать, что я могу делать.")

@dp.message_handler(commands=['help'])
async def cmd_help(message: types.Message):
    help_text = "Вот что я могу:\n\n"\
                "/start - Перезапустить бота.\n"\
                "/help - Инструкция по использованию.\n"\
                "/download - Загрузить видео по ссылке. Отправьте ссылку, чтоб загрузить видео."
    await message.reply(help_text, parse_mode=ParseMode.MARKDOWN)

@dp.message_handler(Command('download'))
async def download_video(message: types.Message, state: FSMContext):
    await message.reply("Загрузить видео по ссылке. Отправьте ссылку, чтоб загрузить видео.")
    await VideoStates.waiting_for_link.set()
    async with state.proxy() as data:
        data['video_url'] = message.text

@dp.message_handler(state=VideoStates.waiting_for_link)
async def process_link(message: types.Message, state: FSMContext):
    try:
        video_url = str(message.text)
        yt = YouTube(video_url)
        video_title = yt.title
        # video_stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
        video_stream = yt.streams.get_highest_resolution()
        video_file_path = f"downloads/{video_title}.mp4"
        video_stream.download(output_path="downloads", filename=video_file_path)

        user_folder = f"tables/{message.from_user.id}"
        if not os.path.exists(user_folder):
            try:
                os.makedirs(user_folder)
            except OSError as e:
                print(f"Error creating directory: {e}")
                return

        csv_file_path = f"{user_folder}/загрузка_пользователя_{message.from_user.id}.csv"
        if not os.path.exists(csv_file_path):
            with open(csv_file_path, mode='w', newline='') as csvfile:
                fieldnames = ['from_user_id', 'Links']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()

        with open(csv_file_path, mode='a', newline='') as csvfile:
            fieldnames = ['from_user_id', 'Links']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writerow({'from_user_id': message.from_user.id, 'Links': video_url})

        await bot.send_video(message.chat.id, open(f"downloads/{video_file_path}", 'rb'), supports_streaming=True)
        await message.answer("Видео успешно загружено!")
    except Exception as e:
        logger.exception(e)
        await message.answer("Извините, произошла ошибка при обработке вашего запроса. Попробуйте /download заново")
    finally:
        await state.finish()

@dp.message_handler()
async def cmd_start(message: types.Message):
    await message.reply("Привет! Я бот для скачивания видео. Используйте /help, чтобы узнать, что я могу делать.")
    await message.delete()

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)

