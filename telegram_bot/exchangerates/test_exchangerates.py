import asyncio
import pytest

from . import exchangerates


TEST_API_KEY = '4HxWSwuMJ1Q901tAr9D4KrXqC03wadvw'

def test_convert_currency_output():
    '''
    Tests output of 'convert_currency' function.
    '''
    # USD to EUR, int amount
    usd_to_eur = asyncio.run(exchangerates.convert_currency(
        'USD',
        'EUR',
        1,
        TEST_API_KEY
    ))
    assert 0.5 < usd_to_eur < 2

    # EUR to USD, float amount
    eur_to_usd = asyncio.run(exchangerates.convert_currency(
        'EUR',
        'USD',
        1.0,
        TEST_API_KEY
    ))
    assert 0.5 < eur_to_usd < 2

def test_convert_currency_bad_cur_code():
    '''
    Tests 'convert_currency' function with bad currency codes given.
    '''
    # Bad 'from' currency
    with pytest.raises(exchangerates.ConversionError):
        asyncio.run(exchangerates.convert_currency(
            '___',
            'EUR',
            1,
            TEST_API_KEY
        ))

    # Bad 'to' currency
    with pytest.raises(exchangerates.ConversionError):
        asyncio.run(exchangerates.convert_currency(
            'USD',
            '___',
            1,
            TEST_API_KEY
        ))

    # Bad both currencies
    with pytest.raises(exchangerates.ConversionError):
        asyncio.run(exchangerates.convert_currency(
            '___',
            '___',
            1,
            TEST_API_KEY
        ))

def test_convert_currency_bad_api_key():
    '''
    Tests 'convert_currency' function with bad API key given.
    '''
    with pytest.raises(exchangerates.AccessDenied):
        asyncio.run(exchangerates.convert_currency(
            'USD',
            'EUR',
            1,
            '_'
        ))

def test_convert_currency_bad_url():
    '''
    Tests 'convert_currency' function with bad URL.
    '''
    url = exchangerates.URL
    exchangerates.URL = 'https://api.apilayer.com/___'
    with pytest.raises(exchangerates.ServiceUnavailable):
        asyncio.run(exchangerates.convert_currency(
            'USD',
            'EUR',
            1,
            TEST_API_KEY
        ))
    exchangerates.URL = url

def test_check_currency_code_output():
    '''
    Tests output of 'check_currency_code' function.
    '''
    assert exchangerates.check_currency_code('USD') == True
    assert exchangerates.check_currency_code('Russian Ruble') == False
