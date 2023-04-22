'''
Represents functions for work with the ExchangeRates service.
'''
import aiohttp


URL = 'https://api.apilayer.com/exchangerates_data/convert'

class ConversionError(Exception):
    '''
    Represents an exception that means an error has occured during the conversion process.
    '''
    pass

class ServiceUnavailable(Exception):
    '''
    Represents an exception that means the ExchangeRates service hasn't answered or returned some
    error.
    '''
    pass

class AccessDenied(Exception):
    '''
    Represents an exception that means the ExchangeRates service has returned code 401.
    '''
    pass

async def convert_currency(
        from_cur_code: str,
        to_cur_code: str,
        amount: int|float,
        api_key: str
    ) -> float:
    '''
    Converts 'amount' from currency with code 'from_cur_code' to currency with code 'to_cur_code'
    using the ExchangeRates service and API key 'api_key'.
    '''
    # Set request headers
    headers = {'apikey': api_key}

    # Set request parameters
    params = {
        'from': from_cur_code,
        'to': to_cur_code,
        'amount': amount
    }

    # Request and parse data
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(URL, params=params) as response:
            # Get response data
            try:
                data = await response.json()
            except:
                raise ServiceUnavailable('Bad or absent JSON data in the response.')

            # Parse the data
            if response.status == 200:
                if data.get('success', None) and data.get('result', None):
                    return data['result']
                else:
                    raise ServiceUnavailable('Bad data has received from the service.')
            elif response.status == 400:
                if data.get('error', None):
                    raise ConversionError(data['error']['message'])
                else:
                    raise ConversionError('An unknown conversion error has occured.')
            elif response.status == 401:
                raise AccessDenied(data.get(
                    'message',
                    'There is no any message in the service response.'
                ))
            else:
                raise ServiceUnavailable(f'Status code: {response.status}')
