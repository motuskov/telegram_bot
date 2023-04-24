'''
Represents functions for getting images from the Giphy service.
'''
import aiohttp


URL = 'https://api.giphy.com/v1/gifs/random'

class ServiceUnavailable(Exception):
    '''
    Represents an exception that means the Giphy service hasn't answered or returned some
    error.
    '''
    pass

class AccessDenied(Exception):
    '''
    Represents an exception that means the Giphy service has returned code 401.
    '''
    pass

async def get_random_image_by_tag(tag: str, api_key: str) -> bytes:
    '''
    Retrieves a random image from the Giphy service by tag 'tag' and API key 'api_key'.
    Can raise exceptions 'AccessDenied', 'ServiceUnavailable' and 'aiohttp.ClientError'.
    '''
    # Set request parameters
    params = {
        'tag': tag,
        'api_key': api_key
    }

    # Get an image URL
    async with aiohttp.ClientSession() as session:
        async with session.get(URL, params=params) as response:
            # Get response data
            try:
                data = await response.json()
            except:
                raise ServiceUnavailable('Bad or absent JSON data in the response.')

            # Get the image URL
            if response.status == 200:
                try:
                    image_url = data['data']['images']['downsized_large']['url']
                except KeyError:
                    raise ServiceUnavailable('Bad data has received from the service.')
            elif response.status == 401:
                try:
                    message = data['meta']['msg']
                except KeyError:
                    message = 'There is no any message in the service response.'
                raise AccessDenied(message)
            else:
                raise ServiceUnavailable(f'The Giphy service has returned code {response.status}')

    # Download the image
    async with aiohttp.ClientSession() as session:
        async with session.get(image_url) as response:
            if response.status == 200:
                try:
                    return await response.read()
                except:
                    raise ServiceUnavailable('Some bad image data has received.')
            else:
                raise ServiceUnavailable(
                    f'During an image downloading next status code has returned {response.status}'
                )
