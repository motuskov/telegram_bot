'''
Represents functions for work with the OpenWeather service.
'''
import aiohttp


URL = 'https://api.openweathermap.org/data/2.5/weather'

WeatherDataType = dict[str, dict[str, int|float|str]]

class UnknownLocality(Exception):
    '''
    Represents an exception that means the OpenWeather service couldn't find a locality with given
    name.
    '''
    pass

class ServiceUnavailable(Exception):
    '''
    Represents an exception that means the OpenWeather service hasn't answered or returned some
    error.
    '''
    pass

class AccessDenied(Exception):
    '''
    Represents an exception that means the OpenWeather service has returned code 401.
    '''
    pass

async def get_locality_weather(locality_name: str, api_key: str) -> WeatherDataType:
    '''
    Requests weather information from the OpenWeather service by name of locality 'locality_name'
    using service API_KEY 'api_key'. Returns a dictionary containing information about temperature,
    pressure and humidity in the locality.
    Can raise exceptions 'UnknownLocality', 'ServiceUnavailable' and 'AccessDenied'.
    '''
    # Set request parameters
    params = {
        'q': locality_name,
        'appid': api_key
    }

    # Request and parse data
    async with aiohttp.ClientSession() as session:
        async with session.get(URL, params=params) as response:
            # Get response data
            try:
                data = await response.json()
            except:
                raise ServiceUnavailable('Bad or absent JSON data in the response.')

            # Parse the data
            if response.status == 200:
                try:
                    weather_data = {
                        'temp': {
                            'value': data['main']['temp'],
                            'units': 'K',
                        },
                        'pressure': {
                            'value': data['main']['pressure'],
                            'units': 'hPa',
                        },
                        'humidity': {
                            'value': data['main']['humidity'],
                            'units': '%',
                        },
                    }
                    return weather_data
                except KeyError:
                    raise ServiceUnavailable('Bad data has received from the service.')
            elif response.status == 404:
                try:
                    message = data['message']
                except KeyError:
                    raise ServiceUnavailable('The OpenWeather service has returned code 404.')
                if message == 'city not found':
                    raise UnknownLocality(
                        f'Locality with name "{locality_name}" has not been found.'
                    )
                else:
                    raise ServiceUnavailable(
                        f'The OpenWeather service has returned code 404: {message}'
                    )
            elif response.status == 401:
                raise AccessDenied(
                    'Access to the OpenWeather service is denied with given API_KEY.'
                )
            else:
                raise ServiceUnavailable(
                    f'The OpenWeather service has returned code {response.status}'
                )
