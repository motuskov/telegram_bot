'''
Tests 'giphy' module.
'''
import asyncio
import pytest

from . import giphy


TEST_API_KEY = 'E4uw37nYmIMKByCuNZqEkCDlHUopYXlW'

def test_get_random_image_by_tag_output():
    '''
    Tests output of 'get_random_image_by_tag' function.
    '''
    image = asyncio.run(giphy.get_random_image_by_tag('funny', TEST_API_KEY))
    assert len(image) > 0

def test_get_random_image_by_tag_bad_api_key():
    '''
    Tests 'get_random_image_by_tag' function with bad API key given.
    '''
    api_key = '___'
    with pytest.raises(giphy.AccessDenied):
        asyncio.run(giphy.get_random_image_by_tag('funny', api_key))

def test_get_random_image_by_tag_bad_url():
    '''
    Tests 'get_random_image_by_tag' function with bad URL.
    '''
    url = giphy.URL
    giphy.URL = 'https://api.giphy.com/v1/gifs/___'
    with pytest.raises(giphy.ServiceUnavailable):
        asyncio.run(giphy.get_random_image_by_tag('funny', TEST_API_KEY))
    giphy.URL = url
