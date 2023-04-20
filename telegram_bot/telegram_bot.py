import logging

from aiogram import (
    Bot,
    Dispatcher,
    executor,
    types,
)


API_TOKEN = '5914526270:AAFgP6yYwbK01guf9NLVgUBWaGOc8zrizYA'

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    '''This handler will be called when user sends `/start` or `/help` command
    '''
    await message.reply('Hi!\nI\'m EchoBot!\nPowered by aiogram.')

@dp.message_handler()
async def echo(message: types.Message):
    await message.answer(message.text)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
