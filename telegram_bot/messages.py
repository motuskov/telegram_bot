'''
Keeps strings and templates for the application.
'''

# General
MENU = (
    'Choose an action:\n'
    '  /help - show a list of commands\n'
    '\n'
    '  /weather - get current weather in a locality\n'
    '  /currencies - convert currencies\n'
    '  /funny - get a funny image with animals\n'
    '  /poll - create a poll\n'
    '\n'
    '  /cancel - cancel a command process'
)
WELCOME = (
    'Hi!\n'
    'I\'m a bot for testing purposes. I can inform you about current weather, convert currencies, '
    'send funny images of animals and create polls in group chats.'
)
SERVICE_UNAVAILABLE = 'Something went wrong. We\'re working on that. Try again later.'
WAIT_MOMENT = 'Sure, wait for a moment...'

# Weather
WEATHER_ASK_LOCALITY = 'Where would you like to know the weather in?'
WEATHER_ASK_ANOTHER_LOCALITY = 'Choose another locality or /cancel the command.'
WEATHER_BAD_LOCALITY = (
    'Locality with name "{locality_name}" hasn\'t been found. Try again or /cancel the command.'
)
WEATHER_WEATHER = (
    'Weather in {locality_name}:\n'
    '  Temperature: {temp_value} {temp_units}\n'
    '  Pressure: {pressure_value} {pressure_units}\n'
    '  Humidity: {humidity_value} {humidity_units}'
)

# Currencies
CURRENCIES_ASK_FROM_CURRENCY = 'What currency would you like to convert from?'
CURRENCIES_ASK_TO_CURRENCY = 'What currency would you like to convert to?'
CURRENCIES_ASK_AMOUNT = 'Enter amount for convertation.'
CURRENCIES_BAD_CURRENCY_CODE = (
    'Currency should be entered as three latin letters. Try again. For more information: '
    'https://en.wikipedia.org/wiki/ISO_4217'
)
CURRENCIES_BAD_AMOUNT = 'Amount should be an integer or a fractional number. Try again.'
CURRENCIES_CONVERSION_ERROR = 'I cannot convert. Please, check the data you\'ve entered.'
CURRENCIES_OUTPUT = '{amount:.2f} {from_currency} = {result:.2f} {to_currency}'

# Poll
POLL_NO_GROUP_CHATS = (
    'There are no active group chats I\'m included in. Add me to a group chat and try again.'
)
POLL_NO_DESIRED_CHAT_BTN = 'There are no desired chat in the list'
POLL_ASK_GROUP_CHAT = 'Choose a group chat where you want to start a poll:'
POLL_NO_DESIRED_CHAT = (
    'If a desired group chat isn\'t in the list you need to add the bot to the desired group '
    'chat. If the bot is in the desired grout chat try to remove it from the chat and add it '
    'again.'
)
POLL_ASK_QUESTION = 'What question would you like to ask in the poll?'
POLL_ASK_ANSWER = 'Enter a posible answer of the poll.'
POLL_ASK_NEXT_ANSWER = 'Enter a next posible answer of the poll.'
POLL_ASK_NEXT_ANSWER_OR_FINISH = (
    'Enter a next posible answer of the poll or finish creating the poll.'
)
POLL_READY = 'I\'ve sent the poll to chosen group chat.'
