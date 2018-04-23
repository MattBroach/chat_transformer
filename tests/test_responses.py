from unittest import TestCase

from irc2osc.targets import ActionResponse


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

    def test_has_osc_update(self):
        """
        `has_osc_update` should only return True if the ActionResponse object
        has both an `osc_value` and an `osc_address`
        """
        irc_message = 'This message goes to IRC'

        only_irc_response = ActionResponse(irc_message)
        self.assertFalse(only_irc_response.has_osc_update)

        no_address_response = ActionResponse(irc_message, osc_value=1.0)
        self.assertFalse(no_address_response.has_osc_update)

        no_value_response = ActionResponse(irc_message, osc_address='/some/address')
        self.assertFalse(no_value_response.has_osc_update)

        full_response = ActionResponse(
            'This message goes to IRC',
            '/this/is/an/osc/address',
            0.5
        )
        self.assertTrue(full_response.has_osc_update)
