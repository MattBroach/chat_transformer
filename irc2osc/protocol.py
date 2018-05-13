import asyncio
import logging

logger = logging.getLogger(__name__)


class OSCProtocol(asyncio.DatagramProtocol):
    def error_Received(self, exc):
        logger.error('Protocol Error: {}'.format(exc))
