import asyncio
import logging

import aiohttp

from .base import BaseOutput

logger = logging.getLogger(__name__)


class HTTPOutput(BaseOutput):
    def __init__(self, base_url='http://localhost:8000/', headers={}, loop=None):
        self.base_url = base_url
        self.headers = headers
        self.loop = loop if loop is not None else asyncio.get_event_loop()

        asyncio.ensure_future(self.initialize_session())

    async def initialize_session(self):
        self.session = aiohttp.ClientSession(headers=self.headers)

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
        async with self.session.post(url, json=data) as r:
            if r.status < 200 or r.status >= 300:
                text = await r.text()
                logger.error(
                    'Error posting {} value of {} to {}: {} '.format(
                        data['name'], data['value'], url, text
                    )
                )

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
