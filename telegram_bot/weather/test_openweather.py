'''
Tests 'openweather' module.
'''
import asyncio
import pytest

from . import openweather


TEST_API_KEY = 'b5ea7a64dc1c5450e68c809c8fda159b'

def test_get_locality_weather_output():
    '''
    Tests the output of 'get_locality_weather' function.
    '''
    boston_weather = asyncio.run(
        openweather.get_locality_weather('Boston', TEST_API_KEY)
    )
    assert 173 < boston_weather['temp']['value'] < 373
    assert boston_weather['temp']['units'] == 'K'
    assert 800 < boston_weather['pressure']['value'] < 1100
    assert boston_weather['pressure']['units'] == 'hPa'
    assert 0 < boston_weather['humidity']['value'] < 100
    assert boston_weather['humidity']['units'] == '%'

def test_get_locality_weather_bad_locality():
    '''
    Tests raising exception in case of a non-existent locality given.
    '''
    locality_name = '___'
    with pytest.raises(openweather.UnknownLocality):
        asyncio.run(
            openweather.get_locality_weather(locality_name, TEST_API_KEY)
        )

def test_get_locality_weather_bad_api_key():
    '''
    Tests raising exception in case of an invalid API key given.
    '''
    api_key = '___'
    with pytest.raises(openweather.AccessDenied):
        asyncio.run(
            openweather.get_locality_weather('Boston', api_key)
        )

def test_get_locality_weather_bad_url():
    '''
    Tests raising exception during imitation of service unavailability.
    '''
    url = openweather.URL
    openweather.URL = 'https://api.openweathermap.org/data/2.5/___'
    with pytest.raises(openweather.ServiceUnavailable):
        asyncio.run(
            openweather.get_locality_weather('Boston', TEST_API_KEY)
        )
    openweather.URL = url
