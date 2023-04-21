import logging
from aiogram import (
    Bot,
    Dispatcher,
    executor,
    types,
)
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import (
    State,
    StatesGroup,
)
from aiogram.dispatcher import FSMContext

from weather import openweather


# API keys
TELEGRAM_BOT_API_TOKEN = '5914526270:AAFgP6yYwbK01guf9NLVgUBWaGOc8zrizYA'
OPENWEATHER_API_KEY = 'b5ea7a64dc1c5450e68c809c8fda159b'

# Messages templates
MENU = (
    'Choose an action:\n'
    '  /help - to show this list of commands\n'
    '  /weather - to check current weather in a given locality\n'
    '  /cancel - to cancel a command process'
)

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=TELEGRAM_BOT_API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

# States
class WeatherStates(StatesGroup):
    '''
    Represents a group of states for requesting weather.
    '''
    locality = State()

@dp.message_handler(state='*', commands=['cancel'])
async def cancel(message: types.Message, state: FSMContext):
    '''
    Resets current state if any.
    '''
    # Get and check current state 
    current_state = await state.get_state()
    if current_state is None:
        return

    # Cancel the state and output the menu
    await state.finish()
    await message.answer(MENU)

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    '''
    Welcomes a user and outputs the menu.
    '''
    await message.answer(
        'Hi!\n'
        'I\'m MotuskovBot!'
    )
    await message.answer(MENU)

@dp.message_handler(commands=['help'])
async def start(message: types.Message):
    '''
    Outputs the menu.
    '''
    await message.answer(MENU)

@dp.message_handler(commands=['weather'])
async def weather_start(message: types.Message):
    '''
    Starts a dialog about weather.
    '''
    # Set state
    await WeatherStates.locality.set()

    # Ask locality name
    await message.answer('Where would you like to know the weather in?')

@dp.message_handler(state=WeatherStates.locality)
async def weather_locality(message: types.Message, state: FSMContext):
    '''
    Processes locality.
    '''
    # Save locality
    locality_name = message.text
    async with state.proxy() as data:
        data['locality'] = locality_name

    # Get and output weather information
    try:
        # Get weather information
        locality_weather = await openweather.get_locality_weather(
            locality_name,
            OPENWEATHER_API_KEY
        )

        # Send the weather information to the user
        await message.answer(
            f'Weather in {locality_name}:\n'
            f'  Temperature: {locality_weather["temp"]["value"]} '
            f'{locality_weather["temp"]["units"]}\n'
            f'  Pressure: {locality_weather["pressure"]["value"]} '
            f'{locality_weather["pressure"]["units"]}\n'
            f'  Humidity: {locality_weather["humidity"]["value"]} '
            f'{locality_weather["humidity"]["units"]}'
        )
        await message.answer('Choose another locality or /cancel the command.')
    except openweather.UnknownLocality:
        # Given locality hasn't found
        await message.answer(
            f'Locality with name "{locality_name}" hasn\'t been found. Try again or /cancel the '
            f'command.'
        )
    except (openweather.AccessDenied, openweather.ServiceUnavailable):
        # Some error has occured
        await message.answer(
            'Something went wrong. We\'re working on that. Try again later.'
        )
        await state.finish()

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
