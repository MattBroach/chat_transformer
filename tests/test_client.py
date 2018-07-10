import os
import asyncio
from unittest import TestCase
from unittest.mock import patch, MagicMock, call

from irc2osc.client import Irc2OscClient

TEST_DIR = os.path.dirname(os.path.abspath(__file__))


class MockTarget:
    """
    used to inset mock OSCTarget data into `client.targets` without relying on
    the actual OSCTarget class
    """
    def __init__(self, address, initial, current=None):
        self.initial = initial
        self.current = current
        self.address = address


class Irc2OscClientTests(TestCase):
    @patch('asyncio.base_events.BaseEventLoop.create_connection')
    def setUp(self, create_connection_mock):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        # create dummy transport, protocol
        fake_connection = asyncio.Future()

        self.mock_transport = MagicMock()
        self.mock_protocol = MagicMock()

        fake_connection.set_result((self.mock_transport, self.mock_protocol))
        create_connection_mock.return_value = fake_connection

        # instantiate client
        self.client = Irc2OscClient(
            9876, targets_file=os.path.join(TEST_DIR, 'test_target_file.json'), loop=self.loop
        )
        self.client.connect(
            'my.fake.irc.server',
            6667,
            'fake_irc_nick',
        )

    def tearDown(self):
        self.client.osc_transport.close()

        # Needs extra loop iteraction to actually close transport
        self.loop.run_until_complete(asyncio.sleep(0))
        self.loop.close()

    @patch('irc2osc.client.Irc2OscClient.osc_send')
    def test_command_with_no_value(self, mock_osc_send):
        """
        sending `parse_command` a command with an INCREMENT/DECRMENT
        value should set the new value and send the values to
        IRC and OSC
        """
        self.assertEqual(self.client.target_value('volume'), 0.5)

        self.client.parse_command('volume increment')

        self.assertEqual(self.client.target_value('volume'), 0.55)
        mock_osc_send.assert_called_with('/audio/volume', 0.55)

    @patch('irc2osc.client.Irc2OscClient.osc_send')
    def test_command_with_set_value(self, mock_osc_send):
        """
        sending `parse_command` a command with a SET value should set
        to the passed value, and send the values/message to IRC and OSC
        """
        self.assertEqual(self.client.target_value('volume'), 0.5)

        self.client.parse_command('volume set 0.73')

        self.assertEqual(self.client.target_value('volume'), 0.73)
        mock_osc_send.assert_called_with('/audio/volume', 0.73)

    @patch('irc2osc.client.Irc2OscClient.osc_send')
    def test_existing_target_but_fake_command_takes_no_action(self, mock_osc_send):
        """
        send `parse_command` a non-existing command but a valid target
        should silently register the InvalidAction and move on, not changing the target value
        or sending data to OSC or IRC
        """
        self.assertEqual(self.client.target_value('volume'), 0.5)

        with self.assertLogs() as cm:
            self.client.parse_command('volume foo')

            self.assertIn(
                'ERROR:irc2osc.client:"foo" is not a valid action for OSCTarget "volume"', cm.output
            )

        self.assertEqual(self.client.target_value('volume'), 0.5)
        mock_osc_send.assert_not_called()

    @patch('irc2osc.client.Irc2OscClient.osc_send')
    def test_non_existing_target_produces_no_response(self, mock_osc_send):
        """
        send `parse_command` a non-existing target should simply have no effect,
        neither calling/updating a target or sending data to OSC or IRC
        """
        self.assertIsNone(self.client.target_value('foo'))

        self.client.parse_command('foo bar')

        self.assertIsNone(self.client.target_value('foo'))
        mock_osc_send.assert_not_called()

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

    @patch('irc2osc.client.Irc2OscClient.osc_send')
    def test_osc_send_all(self, mock_osc_send):
        """
        `osc_send_all` should send the current or initial value for all
        extent targets
        """
        client = Irc2OscClient(
            9876, targets_file=os.path.join(TEST_DIR, 'test_target_file.json'), loop=self.loop
        )

        client.targets['brightness'] = MockTarget('/osc/brightness/', 1.0)
        client.targets['contrast'] = MockTarget('/osc/contrast/', 0.5, current=0.75)
        client.targets['hue'] = MockTarget('/osc/hue/', 0)

        client.osc_send_all()

        expected = [
            call('/osc/brightness/', 1.0),
            call('/osc/contrast/', 0.75),
            call('/osc/hue/', 0),
        ]

        mock_osc_send.assert_has_calls(expected, any_order=True)
