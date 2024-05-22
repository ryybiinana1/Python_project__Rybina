import aiohttp
import asyncio
from asyncio import AbstractEventLoop
from concurrent.futures import Future
from typing import Callable


from bs4 import BeautifulSoup
URL = r'https://www.flickr.com/search/?text='
PHOTO_CONTAINER = 'div'
PHOTO_CLASS = 'photo-list-photo-container'


class Image_Parser:
    def __init__(self, loop: AbstractEventLoop,
                 add_links: Callable, search_word: str) -> None:
        self._get_links: Future = None
        self._loop: AbstractEventLoop = loop
        self.add_links: Callable = add_links
        self.url: str = rf'{URL + search_word}'

    def start(self) -> None:
        links1 = asyncio.run_coroutine_threadsafe(
            self._make_request(), self._loop
            )
        self._get_links = links1

    def cancel(self) -> None:
        if self._get_links:
            self._loop.call_soon_threadsafe(self._get_links.cancel)

    def _add_links_main(self, html: str) -> None:
        b_soup = BeautifulSoup(html, 'lxml')
        box = b_soup.find_all(PHOTO_CONTAINER, class_=PHOTO_CLASS)
        for tag in box:
            img_tag = tag.find('img')
            src_value = img_tag.get('src')
            self.add_links('https:' + src_value)

    async def _make_request(self) -> None:
        async with aiohttp.ClientSession() as session:
            async with session.get(self.url) as response:
                html = await response.text()
        self._add_links_main(html)
