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
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from weather import openweather
from exchangerates import exchangerates
from images import giphy
from . import keys


# Messages templates
MENU = (
    'Choose an action:\n'
    '  /help - to show this list of commands\n'
    '  /weather - to check current weather in a given locality\n'
    '  /currencies - to convert currencies\n'
    '  /funny - to get a funny image\n'
    '  /poll - to create a poll\n'
    '  /cancel - to cancel a command process'
)

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=keys.TELEGRAM_BOT_API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

# Initialize a storage for keeping the list of group chats
group_chats = {}

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

class PollStates(StatesGroup):
    '''
    Represents a group of states for creating a poll.
    '''
    group_chat = State()
    question = State()
    answer = State()

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
            keys.OPENWEATHER_API_KEY
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
                keys.EXCHANGE_RATES_API_KEY
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

@dp.message_handler(commands=['funny'])
async def funny_image(message: types.Message):
    '''
    Replies with a funny image
    '''
    # Send notification (due to the long waiting period)
    await message.answer('Sure, wait for a moment...')

    # Get image and send to the chat
    try:
        image = await giphy.get_random_image_by_tag('funny', keys.GIPHY_API_KEY)
        await message.answer_photo(image)
    except (giphy.AccessDenied, giphy.ServiceUnavailable):
        await message.answer(
            'Something went wrong. We\'re working on that. Try again later.'
        )

@dp.message_handler(commands=['poll'])
async def poll_start(message: types.Message):
    '''
    Starts polls creator.
    '''
    # Check if there are any group chats where the bot is present
    if not group_chats:
        await message.answer(
            'There are no active group chats I\'m involved in. Add me to a group chat and try '
            'again.'
        )
        return

    # Set initial state
    await PollStates.group_chat.set()

    # Ask user to choose a chat group
    answer_buttons = [InlineKeyboardButton(group_chat[1], callback_data=group_chat[0])
               for group_chat in group_chats.items()]
    answer_buttons.append(InlineKeyboardButton('There are no desired chat in the list', callback_data=0))
    answer_markup = InlineKeyboardMarkup(row_width=1)
    answer_markup.add(*answer_buttons)
    await message.answer('Choose a group chat where you want to start a poll:', reply_markup=answer_markup)

@dp.callback_query_handler(state=PollStates.group_chat)
async def poll_group_chat(callback_query: types.CallbackQuery, state: FSMContext):
    '''
    Processes selected group chat.
    '''
    # Check selected group chat ID
    if callback_query.data == '0' :
        await callback_query.message.answer(
            'If a desired group chat isn\'t in the list you need to add the bot to the desired '
            'group chat. If the bot is in the desired grout chat try to remove it from the chat '
            'and add it again.'
        )
        await state.finish()
        return

    # Save selected group chat ID
    async with state.proxy() as data:
        data['group_chat_id'] = callback_query.data

    # Go to the next state
    await PollStates.next()

    # Ask user to put a poll question
    await callback_query.message.answer('What question would you like to ask in the poll?')

@dp.message_handler(state=PollStates.question)
async def poll_question(message: types.Message, state: FSMContext):
    '''
    Processes poll question.
    '''
    # Save given poll question
    async with state.proxy() as data:
        data['question'] = message.text

    # Go to the next state
    await PollStates.next()

    # Ask user to put a poll answer
    await message.answer('Enter a posible answer of the poll.')

@dp.message_handler(state=PollStates.answer)
async def poll_answer(message: types.Message, state: FSMContext):
    '''
    Processes poll answer.
    '''
    # Save given poll answer
    async with state.proxy() as data:
        answers = data.get('answers', [])
        answers.append(message.text)
        data['answers'] = answers

    # Ask user to put a poll answer
    if len(answers) < 2:
        await message.answer('Enter a next posible answer of the poll.')
    else:
        answer_buttons = [InlineKeyboardButton('finish', callback_data='finish')]
        answer_markup = InlineKeyboardMarkup(row_width=1)
        answer_markup.add(*answer_buttons)
        await message.answer(
            'Enter a next posible answer of the poll or finish creating the poll.',
            reply_markup=answer_markup
        )

@dp.callback_query_handler(
        lambda callback_query: callback_query.data == 'finish',
        state=PollStates.answer
)
async def poll_group_chat(callback_query: types.CallbackQuery, state: FSMContext):
    '''
    Creates a poll.
    '''
    async with state.proxy() as data:
        # Create a poll
        await bot.send_poll(
            data['group_chat_id'],
            data['question'],
            data['answers']
        )

        # Answer the user
        await callback_query.message.answer('I\'ve sent the poll to chosen group chat.')

        # Finish state
        await state.finish()

@dp.my_chat_member_handler()
async def manage_group_chat_list(my_chat_member: types.ChatMemberUpdated):
    '''
    Manages the list of group chats where the bot is present.
    '''
    # Return if the chat isn't a group
    if my_chat_member.chat.type != 'group':
        return

    # Manage the list of group chats
    if my_chat_member.new_chat_member.status == 'left':
        group_chats.pop(my_chat_member.chat.id, None)
    else:
        group_chats[my_chat_member.chat.id] = my_chat_member.chat.title

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
