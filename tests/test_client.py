import os
import asyncio
from unittest import TestCase
from unittest.mock import patch, MagicMock, call

from chat_transformer.client import TransformerClient

TEST_DIR = os.path.dirname(os.path.abspath(__file__))


class MockCommand:
    """
    used to inset mock OSCCommand data into `client.commands` without relying on
    the actual OSCCommand class
    """
    def __init__(self, initial, current=None, outputs={}, min=0.0, max=1.0):
        self.initial = initial
        self.current = current
        self.outputs = outputs
        self.min = min
        self.max = max


class TransformerClientTests(TestCase):
    def create_connection_mock(self):
        fake_connection = asyncio.Future()

        # create dummy transport, protocol
        self.mock_transport = MagicMock()
        self.mock_protocol = MagicMock()

        fake_connection.set_result((self.mock_transport, self.mock_protocol))

        return fake_connection

    @patch('asyncio.base_events.BaseEventLoop.create_connection')
    @patch('asyncio.base_events.BaseEventLoop.create_datagram_endpoint')
    def setUp(self, create_connection_mock, create_datagram_mock):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        create_connection_mock.return_value = self.create_connection_mock()
        create_datagram_mock.return_value = self.create_connection_mock()

        # instantiate client
        self.client = TransformerClient(
            commands_file=os.path.join(TEST_DIR, 'test_commands_file.json'),
            output_data={'osc': {'port': 6789}},
            loop=self.loop
        )
        self.loop.run_until_complete(self.client.connect(
            'my.fake.irc.server',
            6667,
            'fake_irc_nick',
        ))

    def tearDown(self):
        self.client.outputs['osc'].transport.close()

        # Needs extra loop iteraction to actually close transport
        self.loop.run_until_complete(asyncio.sleep(0))
        self.loop.close()

    @patch('chat_transformer.outputs.osc.OSCOutput.send')
    def test_command_with_no_value(self, mock_send):
        """
        sending `parse_command` a command with an INCREMENT/DECRMENT
        value should set the new value and send the values to
        IRC and OSC
        """
        self.assertEqual(self.client.command_value('volume'), 0.5)

        self.client.parse_command('volume increment')

        self.assertEqual(self.client.command_value('volume'), 0.55)
        mock_send.assert_called_with(0.55, address='/audio/volume')

    @patch('chat_transformer.outputs.osc.OSCOutput.send')
    def test_command_with_set_value(self, mock_send):
        """
        sending `parse_command` a command with a SET value should set
        to the passed value, and send the values/message to IRC and OSC
        """
        self.assertEqual(self.client.command_value('volume'), 0.5)

        self.client.parse_command('volume set 0.73')

        self.assertEqual(self.client.command_value('volume'), 0.73)
        mock_send.assert_called_with(0.73, address='/audio/volume')

    @patch('chat_transformer.outputs.osc.OSCOutput.send')
    def test_existing_command_but_fake_command_takes_no_action(self, mock_send):
        """
        send `parse_command` a non-existing command but a valid command
        should silently register the InvalidAction and move on, not changing the command value
        or sending data to OSC or IRC
        """
        self.assertEqual(self.client.command_value('volume'), 0.5)

        with self.assertLogs() as cm:
            self.client.parse_command('volume foo')

            self.assertIn(
                ('ERROR:chat_transformer.client:"foo" is not a valid action '
                 'for command "volume"'), cm.output
            )

        self.assertEqual(self.client.command_value('volume'), 0.5)
        mock_send.assert_not_called()

    @patch('chat_transformer.outputs.osc.OSCOutput.send')
    def test_non_existing_command_produces_no_response(self, mock_send):
        """
        send `parse_command` a non-existing command should simply have no effect,
        neither calling/updating a command or sending data to OSC or IRC
        """
        self.assertIsNone(self.client.command_value('foo'))

        self.client.parse_command('foo bar')

        self.assertIsNone(self.client.command_value('foo'))
        mock_send.assert_not_called()

    def test_format_irc_channel_ensures_hashtag_for_channel_name(self):
        """
        `format_irc_channel` should always make sure the irc_channel name always starts
        with a single '#'
        """
        self.assertEqual(self.client.format_irc_channel('my_channel'), '#my_channel')
        self.assertEqual(self.client.format_irc_channel('#my_channel'), '#my_channel')

    def test_on_welcome_joins_irc_channel(self):
        """
        `on_welcome` should automatically send a join `self.irc_channel
        """
        self.client.on_welcome('', '')
        self.mock_transport.write.assert_called_with(b'JOIN #fake_irc_nick\r\n')

    @patch('chat_transformer.outputs.osc.OSCOutput.send')
    def test_send_all(self, mock_send):
        """
        `send_all` should send the current or initial value for all
        extent commands
        """
        client = TransformerClient(
            commands_file=os.path.join(TEST_DIR, 'test_commands_file.json'),
            output_data={'osc': {'port': 6789}},
            loop=self.loop
        )

        client.commands['brightness'] = MockCommand(
            1.0, outputs={'osc': {'address': '/osc/brightness/'}},
        )
        client.commands['contrast'] = MockCommand(
            0.5, outputs={'osc': {'address': '/osc/contrast/'}}, current=0.75
        )
        client.commands['hue'] = MockCommand(
            0, outputs={'osc': {'address': '/osc/hue/'}},
        )

        client.send_all()

        expected = [
            call(1.0, address='/osc/brightness/', min=0.0, max=1.0),
            call(0.75, address='/osc/contrast/', min=0.0, max=1.0),
            call(0, address='/osc/hue/', min=0.0, max=1.0),
        ]

        mock_send.assert_has_calls(expected, any_order=True)
