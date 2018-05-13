import asyncio
from unittest import TestCase, mock

from irc2osc.client import Irc2OscClient


class Irc2OscClientTests(TestCase):
    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        self.client = Irc2OscClient(9876, targets_file='tests/test_target_file.json', loop=self.loop)
        self.client.connect()
        self.client.load_targets()

    def tearDown(self):
        self.client.osc_transport.close()
        self.loop.run_until_complete(asyncio.sleep(0)) # Needs extra loop iteraction to actually close transport
        self.loop.close()

    @mock.patch('irc2osc.client.Irc2OscClient.osc_send')
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

    
    @mock.patch('irc2osc.client.Irc2OscClient.osc_send')
    def test_command_with_set_value(self, mock_osc_send):
        """
        sending `parse_command` a command with a SET value should set
        to the passed value, and send the values/message to IRC and OSC
        """
        self.assertEqual(self.client.target_value('volume'), 0.5)

        self.client.parse_command('volume set 0.73')
        
        self.assertEqual(self.client.target_value('volume'), 0.73)
        mock_osc_send.assert_called_with('/audio/volume', 0.73)

    @mock.patch('irc2osc.client.Irc2OscClient.osc_send')
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

    @mock.patch('irc2osc.client.Irc2OscClient.osc_send')
    def test_non_existing_target_produces_no_response(self, mock_osc_send):
        """
        send `parse_command` a non-existing target should simply have no effect,
        neither calling/updating a target or sending data to OSC or IRC
        """
        self.assertIsNone(self.client.target_value('foo'))

        self.client.parse_command('foo bar')

        self.assertIsNone(self.client.target_value('foo'))
        mock_osc_send.assert_not_called()
