import logging
import redis.asyncio as redis
from aiogram import (
    Bot,
    Dispatcher,
    executor,
    types,
)
from aiogram.contrib.fsm_storage.redis import RedisStorage2
from aiogram.dispatcher import FSMContext
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiohttp import ClientError

from weather import openweather
from exchangerates import exchangerates
from images import giphy
import keys
import settings
import messages
import states


####################################################################################################
########################################## Configure logging #######################################
####################################################################################################

logging.basicConfig(level=logging.INFO)


####################################################################################################
#################################### Initialize bot and dispatcher #################################
####################################################################################################

bot = Bot(token=keys.TELEGRAM_BOT_API_TOKEN)
bot_ds = RedisStorage2(
    settings.DATA_STORAGE_HOST,
    db=settings.DATA_STORAGE_BOT_DB,
    prefix=settings.DATA_STORAGE_BOT_PREFIX
)
dp = Dispatcher(bot, storage=bot_ds)


####################################################################################################
######################################### General handlers #########################################
####################################################################################################

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
    await message.answer(messages.MENU)

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    '''
    Welcomes a user and outputs the menu.
    '''
    await message.answer(messages.WELCOME)
    await message.answer(messages.MENU)

@dp.message_handler(commands=['help'])
async def start(message: types.Message):
    '''
    Outputs the menu.
    '''
    await message.answer(messages.MENU)


####################################################################################################
######################################### Weather handlers #########################################
####################################################################################################

@dp.message_handler(commands=['weather'])
async def weather_start(message: types.Message):
    '''
    Starts a dialog about weather.
    '''
    # Set state
    await states.WeatherStates.locality.set()

    # Ask locality name
    await message.answer(messages.WEATHER_ASK_LOCALITY)

@dp.message_handler(state=states.WeatherStates.locality)
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
        await message.answer(messages.WEATHER_WEATHER.format(
            locality_name=locality_name,
            temp_value=locality_weather['temp']['value'],
            temp_units=locality_weather['temp']['units'],
            pressure_value=locality_weather['pressure']['value'],
            pressure_units=locality_weather['pressure']['units'],
            humidity_value=locality_weather['humidity']['value'],
            humidity_units=locality_weather['humidity']['units']
        ))
        await message.answer(messages.WEATHER_ASK_ANOTHER_LOCALITY)
    except openweather.UnknownLocality:
        # Given locality hasn't found
        await message.answer(messages.WEATHER_BAD_LOCALITY.format(locality_name=locality_name))
    except (openweather.AccessDenied, openweather.ServiceUnavailable, ClientError):
        # Some error has occured
        await message.answer(messages.SERVICE_UNAVAILABLE)
        await state.finish()


####################################################################################################
####################################### Currencies handlers ########################################
####################################################################################################

@dp.message_handler(commands=['currencies'])
async def currencies_start(message: types.Message):
    '''
    Starts currencies converter.
    '''
    # Set initial state
    await states.CurrenciesStates.from_currency.set()

    # Ask currency code to convert from
    await message.answer(messages.CURRENCIES_ASK_FROM_CURRENCY)

@dp.message_handler(state=states.CurrenciesStates.from_currency)
async def currencies_from_currency(message: types.Message, state: FSMContext):
    '''
    Processes 'from' currency.
    '''
    # Save from currency
    from_currency = message.text
    if not exchangerates.check_currency_code(from_currency):
        await message.answer(messages.CURRENCIES_BAD_CURRENCY_CODE)
        return
    async with state.proxy() as data:
        data['from_currency'] = from_currency.upper()

    # Go to the next state
    await states.CurrenciesStates.next()

    # Ask currency code to convert to
    await message.answer(messages.CURRENCIES_ASK_TO_CURRENCY)

@dp.message_handler(state=states.CurrenciesStates.to_currency)
async def currencies_to_currency(message: types.Message, state: FSMContext):
    '''
    Processes 'to' currency.
    '''
    # Save to currency
    to_currency = message.text
    if not exchangerates.check_currency_code(to_currency):
        await message.answer(messages.CURRENCIES_BAD_CURRENCY_CODE)
        return
    async with state.proxy() as data:
        data['to_currency'] = to_currency.upper()

    # Go to the next state
    await states.CurrenciesStates.next()

    # Ask amount to convert
    await message.answer(messages.CURRENCIES_ASK_AMOUNT)

@dp.message_handler(state=states.CurrenciesStates.amount)
async def currencies_amount(message: types.Message, state: FSMContext):
    '''
    Converts currency.
    '''
    async with state.proxy() as data:
        try:
            data['amount'] = float(message.text)
        except ValueError:
            await message.answer(messages.CURRENCIES_BAD_AMOUNT)
            return

        # Convert currency and output
        try:
            result = await exchangerates.convert_currency(
                data['from_currency'],
                data['to_currency'],
                data['amount'],
                keys.EXCHANGE_RATES_API_KEY
            )
            await message.answer(messages.CURRENCIES_OUTPUT.format(
                amount=data['amount'],
                from_currency=data['from_currency'],
                result=result,
                to_currency=data["to_currency"]
            ))
        except exchangerates.ConversionError:
            await message.answer(messages.CURRENCIES_CONVERSION_ERROR)
        except (exchangerates.AccessDenied, exchangerates.ServiceUnavailable, ClientError):
            await message.answer(messages.SERVICE_UNAVAILABLE)
        finally:
            await state.finish()


####################################################################################################
####################################### Funny image handler ########################################
####################################################################################################

@dp.message_handler(commands=['funny'])
async def funny_image(message: types.Message):
    '''
    Replies with a funny image
    '''
    # Send notification (due to the long waiting period)
    await message.answer(messages.WAIT_MOMENT)

    # Get image and send to the chat
    try:
        image = await giphy.get_random_image_by_tag('funny animals', keys.GIPHY_API_KEY)
        await message.answer_photo(image)
    except (giphy.AccessDenied, giphy.ServiceUnavailable, ClientError):
        await message.answer(messages.SERVICE_UNAVAILABLE)


####################################################################################################
########################################## Poll handlers ###########################################
####################################################################################################

async def get_group_chats(host: str = 'localhost', db: str | int = 0) -> list[tuple[str, str]]:
    '''
    Retrieves bot's group chat list from a Redis data storage.
    '''
    # Open connection to a data storage
    group_chats_ds = redis.Redis(host=host, db=db)

    # Retrieve 
    group_chat_keys = await group_chats_ds.keys()
    group_chats = []
    for group_chat_key in group_chat_keys:
        group_chats.append((
            (await group_chats_ds.get(group_chat_key)).decode(),
            group_chat_key.decode()
        ))

    # Close data storage connection
    await group_chats_ds.close()

    return group_chats

@dp.message_handler(commands=['poll'])
async def poll_start(message: types.Message):
    '''
    Starts polls creator.
    '''
    # Get group chats
    group_chats = await get_group_chats(
        host=settings.DATA_STORAGE_HOST,
        db=settings.DATA_STORAGE_CHAT_LIST_DB
    )

    # Check if there are any group chats where the bot is present
    if not group_chats:
        await message.answer(messages.POLL_NO_GROUP_CHATS)
        return

    # Set initial state
    await states.PollStates.group_chat.set()

    # Ask user to choose a chat group
    answer_buttons = [InlineKeyboardButton(group_chat[0], callback_data=group_chat[1])
                      for group_chat in group_chats]
    answer_buttons.append(InlineKeyboardButton(messages.POLL_NO_DESIRED_CHAT_BTN, callback_data=0))
    answer_markup = InlineKeyboardMarkup(row_width=1)
    answer_markup.add(*answer_buttons)
    await message.answer(messages.POLL_ASK_GROUP_CHAT, reply_markup=answer_markup)

@dp.callback_query_handler(state=states.PollStates.group_chat)
async def poll_group_chat(callback_query: types.CallbackQuery, state: FSMContext):
    '''
    Processes selected group chat.
    '''
    # Check selected group chat ID
    if callback_query.data == '0' :
        await callback_query.message.answer(messages.POLL_NO_DESIRED_CHAT)
        await state.finish()
        return

    # Save selected group chat ID
    async with state.proxy() as data:
        data['group_chat_id'] = callback_query.data

    # Go to the next state
    await states.PollStates.next()

    # Ask user to put a poll question
    await callback_query.message.answer(messages.POLL_ASK_QUESTION)

@dp.message_handler(state=states.PollStates.question)
async def poll_question(message: types.Message, state: FSMContext):
    '''
    Processes poll question.
    '''
    # Save given poll question
    async with state.proxy() as data:
        data['question'] = message.text

    # Go to the next state
    await states.PollStates.next()

    # Ask user to put a poll answer
    await message.answer(messages.POLL_ASK_ANSWER)

@dp.message_handler(state=states.PollStates.answer)
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
    if len(answers) < settings.POLL_ANSWERS_MIN_NUMBER:
        await message.answer(messages.POLL_ASK_NEXT_ANSWER)
    else:
        answer_buttons = [InlineKeyboardButton('finish', callback_data='finish')]
        answer_markup = InlineKeyboardMarkup(row_width=1)
        answer_markup.add(*answer_buttons)
        await message.answer(
            messages.POLL_ASK_NEXT_ANSWER_OR_FINISH,
            reply_markup=answer_markup
        )

@dp.callback_query_handler(
        lambda callback_query: callback_query.data == 'finish',
        state=states.PollStates.answer
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
        await callback_query.message.answer(messages.POLL_READY)

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

    # Open connection to a data storage for keeping the list of group chats
    group_chats_ds = redis.Redis(
        host=settings.DATA_STORAGE_HOST,
        db=settings.DATA_STORAGE_CHAT_LIST_DB
    )

    # Manage the list of group chats
    if my_chat_member.new_chat_member.status == 'left':
        #group_chats.pop(my_chat_member.chat.id, None)
        await group_chats_ds.delete(str(my_chat_member.chat.id))
    else:
        #group_chats[my_chat_member.chat.id] = my_chat_member.chat.title
        await group_chats_ds.set(str(my_chat_member.chat.id), my_chat_member.chat.title)

    # Close connection to the data storage
    await group_chats_ds.close()


if __name__ == '__main__':
    executor.start_polling(dp)
