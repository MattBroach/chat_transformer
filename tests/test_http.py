from unittest import TestCase
from unittest.mock import patch, Mock
import asyncio

from chat_transformer.outputs.http import HTTPOutput


class HTTPOutputTests(TestCase):
    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        # Needs extra loop iteraction to actually close transport
        self.loop.run_until_complete(asyncio.sleep(0))
        self.loop.close()

    @patch('time.time')
    def test_headers_creates_jwt_token_if_secret(self, mock_time):
        """
        If there's a `jwt_secret` passed to the client, it should create the appropriate
        header.
        """
        no_secret_http = HTTPOutput()
        self.assertEqual({}, no_secret_http.get_headers())
        no_secret_http.cleanup()

        mock_time.return_value = 1534659178.4787898

        secret_http = HTTPOutput(
            jwt_secret='this-is-a-fake-key-dont-use-elsewhere'
        )
        self.assertEqual(
            secret_http.get_headers(),
            {'Authorization': (
                'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJleHAiOjE1MzQ2NTkyMDh9.'
                '29n6v-JfWa7FP65hz89nsKmhUjcWnNn-vBNNimKlrTg'
            )}
        )
        secret_http.cleanup()

    @patch('aiohttp.ClientSession.post')
    def test_http_output_send(self, mock_post):
        """
        calling `send` on an `HTTPOutput` should call the session.post with the
        appropriate data/url
        """
        async def mock_response():
            mock_response = Mock()
            mock_response.status = 200
            return mock_response

        mock_post.return_value = mock_response()

        http = HTTPOutput(
            base_url='https://test.url/',
            headers={'my': 'headers'},
        )

        http.send(0.5, command_name='brightness', endpoint='update/')

        pending = asyncio.Task.all_tasks()
        self.loop.run_until_complete(asyncio.gather(*pending))

        http.cleanup()
        mock_post.assert_called_with(
            'https://test.url/update/', json={
                'value': 0.5, 'name': 'brightness',
            }, headers={'my': 'headers'}
        )

    @patch('aiohttp.ClientSession.post')
    def test_http_output_send_all(self, mock_post):
        """
        calling `send` on an `HTTPOutput` should call the session.post with the
        appropriate data/url
        """
        async def mock_response():
            mock_response = Mock()
            mock_response.status = 200
            return mock_response

        mock_post.return_value = mock_response()

        http = HTTPOutput(
            base_url='https://test.url/',
            headers={'my': 'headers'},
        )

        http.send_full(
            0.5, command_name='brightness', endpoint='update/',
            min=-2.0, max=2.0
        )

        pending = asyncio.Task.all_tasks()
        self.loop.run_until_complete(asyncio.gather(*pending))

        http.cleanup()
        mock_post.assert_called_with(
            'https://test.url/update/', json={
                'value': 0.5, 'name': 'brightness',
                'min': -2.0, 'max': 2.0,
            }, headers={'my': 'headers'}
        )
