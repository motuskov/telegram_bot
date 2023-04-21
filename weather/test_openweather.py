import asyncio
import pytest

from . import openweather


TEST_API_KEY = 'b5ea7a64dc1c5450e68c809c8fda159b'

def test_get_locality_weather_output():
    boston_weather = asyncio.run(
        openweather.get_locality_weather('Boston', TEST_API_KEY)
    )
    assert 173 < boston_weather['temp']['value'] < 373
    assert boston_weather['temp']['units'] == 'K'
    assert 800 < boston_weather['pressure']['value'] < 1100
    assert boston_weather['pressure']['units'] == 'hPa'
    assert 0 < boston_weather['humidity']['value'] < 100
    assert boston_weather['humidity']['units'] == '%'

def test_get_locality_weather_exceptions():
    # Bad locality name
    with pytest.raises(openweather.UnknownLocality):
        asyncio.run(
            openweather.get_locality_weather('___', TEST_API_KEY)
        )

    # Bad API_KEY
    with pytest.raises(openweather.AccessDenied):
        asyncio.run(
            openweather.get_locality_weather('Boston', '___')
        )

    # Service is not available
    base_url = openweather.BASE_URL
    openweather.BASE_URL = 'https://api.openweathermap.org/data/2.5/___'
    with pytest.raises(openweather.ServiceUnavailable):
        asyncio.run(
            openweather.get_locality_weather('Boston', TEST_API_KEY)
        )
    openweather.BASE_URL = base_url
