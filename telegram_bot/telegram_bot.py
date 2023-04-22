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
from exchangerates import exchangerates


# API keys
TELEGRAM_BOT_API_TOKEN = '5914526270:AAFgP6yYwbK01guf9NLVgUBWaGOc8zrizYA'
OPENWEATHER_API_KEY = 'b5ea7a64dc1c5450e68c809c8fda159b'
EXCHANGE_RATES_API_KEY = '4HxWSwuMJ1Q901tAr9D4KrXqC03wadvw'

# Messages templates
MENU = (
    'Choose an action:\n'
    '  /help - to show this list of commands\n'
    '  /weather - to check current weather in a given locality\n'
    '  /currencies - to convert currencies\n'
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

class CurrenciesStates(StatesGroup):
    '''
    Represents a group of states for converting currencies.
    '''
    from_currency = State()
    to_currency = State()
    amount = State()

# Message handlers
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

@dp.message_handler(commands=['currencies'])
async def currencies_start(message: types.Message):
    '''
    Starts currencies converter.
    '''
    # Set initial state
    await CurrenciesStates.from_currency.set()

    # Ask currency code to convert from
    await message.answer('What currency would you like to convert from?')

@dp.message_handler(state=CurrenciesStates.from_currency)
async def currencies_from_currency(message: types.Message, state: FSMContext):
    '''
    Processes from currency.
    '''
    # Save from currency
    from_currency = message.text
    if not exchangerates.check_currency_code(from_currency):
        await message.answer('Currency should be entered as three latin letters. Try again.')
        return
    async with state.proxy() as data:
        data['from_currency'] = from_currency

    # Go to the next state
    await CurrenciesStates.next()

    # Ask currency code to convert to
    await message.answer('What currency would you like to convert to?')

@dp.message_handler(state=CurrenciesStates.to_currency)
async def currencies_to_currency(message: types.Message, state: FSMContext):
    '''
    Processes to currency.
    '''
    # Save to currency
    to_currency = message.text
    if not exchangerates.check_currency_code(to_currency):
        await message.answer('Currency should be entered as three latin letters. Try again.')
        return
    async with state.proxy() as data:
        data['to_currency'] = to_currency

    # Go to the next state
    await CurrenciesStates.next()

    # Ask amount to convert
    await message.answer('Enter amount for convertation.')

@dp.message_handler(state=CurrenciesStates.amount)
async def currencies_amount(message: types.Message, state: FSMContext):
    '''
    Converts currency.
    '''
    async with state.proxy() as data:
        try:
            data['amount'] = float(message.text)
        except ValueError:
            await message.answer('Amount should be an integer or a fractional number. Try again.')
            return

        # Convert currency and output
        try:
            result = await exchangerates.convert_currency(
                data['from_currency'],
                data['to_currency'],
                data['amount'],
                EXCHANGE_RATES_API_KEY
            )
            await message.answer(
                f'{data["amount"]} {data["from_currency"]} = {result} {data["to_currency"]}'
            )
        except exchangerates.ConversionError:
            await message.answer('I cannot convert. Please, check the data you\'ve entered.')
        except (exchangerates.AccessDenied, exchangerates.ServiceUnavailable):
            await message.answer(
                'Something went wrong. We\'re working on that. Try again later.'
            )
        finally:
            await state.finish()

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
