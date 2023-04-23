'''
Defines states of the bot.
'''
from aiogram.dispatcher.filters.state import (
    State,
    StatesGroup,
)


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
