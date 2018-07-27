from unittest import TestCase

from chat_transformer.responses import ActionResponse


class ActionResponseTests(TestCase):
    def test_str_representation(self):
        """
        String representation of an ActionResponse should be its `irc_message` value
        """
        response = ActionResponse(
            'This message goes to IRC',
            '/this/is/an/osc/address',
            0.5
        )
        self.assertEqual(str(response), 'This message goes to IRC')

    def test_has_output(self):
        """
        `has_output` should only return True if the ActionResponse object
        has both an `osc_value` and an `osc_address`
        """
        irc_message = 'This message goes to IRC'

        only_irc_response = ActionResponse(irc_message)
        self.assertFalse(only_irc_response.has_output)

        no_output_response = ActionResponse(irc_message, value=1.0)
        self.assertFalse(no_output_response.has_output)

        no_value_response = ActionResponse(
            irc_message,
            output_params={'osc': {'address': '/brightness/'}},
        )
        self.assertFalse(no_value_response.has_output)

        full_response = ActionResponse(
            'This message goes to IRC',
            0.5,
            {'osc': {'address': '/this/is/an/osc/address'}},
        )
        self.assertTrue(full_response.has_output)
