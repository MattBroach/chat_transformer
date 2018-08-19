import asyncio
import logging
import time

import aiohttp
import jwt

from .base import BaseOutput

logger = logging.getLogger(__name__)


class HTTPOutput(BaseOutput):
    def __init__(
        self,
        base_url='http://localhost:8000/',
        headers={},
        loop=None,
        jwt_secret='',
        jwt_token_length=30,
    ):
        self.base_url = base_url
        self.headers = headers
        self.jwt_secret = jwt_secret
        self.jwt_token_length = jwt_token_length
        self.loop = loop if loop is not None else asyncio.get_event_loop()

        asyncio.ensure_future(self.initialize_session())

    def get_headers(self):
        """
        Hook for dynamic headers.  Primarily used for JWT tokens currently,
        but can be overridden for custom behavior
        """
        headers = self.headers

        if self.jwt_secret:
            current = int(time.time())
            params = {'exp': current + self.jwt_token_length}
            token = jwt.encode(params, self.jwt_secret)
            headers = {
                **headers,
                'Authorization': 'Bearer {}'.format(token.decode('utf-8')),
            }

        return headers

    async def initialize_session(self):
        self.session = aiohttp.ClientSession()

    def send(self, value, command_name='', endpoint='', **kwargs):
        """
        POST the data to the target endpoint
        """
        data = {
            'value': value,
            'name': command_name,
            **kwargs,
        }

        url = self.base_url + endpoint

        asyncio.ensure_future(self._send(url, data))

    async def _send(self, url, data):
        """
        Posts to target. Avoids using aiohttp context manager for easier testing
        """
        r = await self.session.post(url, json=data, headers=self.get_headers())

        if r.status < 200 or r.status >= 300:
            text = await r.text()
            logger.error(
                'Error posting {} value of {} to {}: {} '.format(
                    data['name'], data['value'], url, text
                )
            )

        r.release()

    def send_full(self, value, **kwargs):
        self.send(
            value,
            command_name=kwargs.get('command_name', ''),
            endpoint=kwargs.get('endpoint', ''),
            min=kwargs.get('min', 0.0),
            max=kwargs.get('max', 1.0),
        )

    def cleanup(self):
        """
        Close the session
        """
        asyncio.ensure_future(self._cleanup())

    async def _cleanup(self):
        await self.session.close()
        await asyncio.sleep(0)
