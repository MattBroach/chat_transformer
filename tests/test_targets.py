from unittest import TestCase

from irc2osc.targets import OSCTarget, InvalidActionError


class OSCTargetTests(TestCase):
    def test_str_representation(self):
        """
        String representation of an OSCTarget should be its `name`
        """
        target = OSCTarget(name='My Target', address='/osc/address')
        self.assertEqual(str(target), 'My Target')

    def test_invalid_actions_raises_invalid_action_error(self):
        """
        Passing an action not in `allowed_actions` to `run_action` should raise
        an `InvalidActionError`
        """
        target = OSCTarget(
            name='My Target',
            address='/osc/address',
            allowed_actions=['increment', 'decrement', 'set'],
        )

        with self.assertRaises(InvalidActionError) as error:
            target.run_action('set_to_zero')

        self.assertEqual(
            str(error.exception),
            '"set_to_zero" is not a valid action for OSCTarget "My Target"',
        )

    def test_increment_inside_range(self):
        """
        Running the "increment" action should add the target's `delta` to
        the current value.  Repeated runs should continue to increase the value
        """
        target = OSCTarget(
            name='My Target',
            address='/osc/address',
            initial=0.5,
            delta=0.07,
            max=1.0,
        )

        response = target.run_action('increment')
        self.assertAlmostEqual(response.osc_value, 0.57)
        self.assertAlmostEqual(target.current, 0.57)
        self.assertEqual(response.osc_address, '/osc/address')
        self.assertEqual(
            response.irc_message,
            'MY TARGET is at 0.57 (Max 1.0)'
        )

        response = target.run_action('increment')
        self.assertAlmostEqual(response.osc_value, 0.64)
        self.assertAlmostEqual(target.current, 0.64)

        response = target.run_action('increment')
        self.assertAlmostEqual(response.osc_value, 0.71)
        self.assertAlmostEqual(target.current, 0.71)

    def test_increment_overlapping_range(self):
        """
        if the delta + current is greater than the max, the `increment` value should
        be clamped down to max, but an osc_value should still be sent
        """
        target = OSCTarget(
            name='My Target',
            address='/osc/address',
            initial=0.97,
            delta=0.07,
            max=1.0,
        )

        response = target.run_action('increment')
        self.assertAlmostEqual(response.osc_value, 1.0)
        self.assertAlmostEqual(target.current, 1.0)
        self.assertEqual(response.osc_address, '/osc/address')
        self.assertEqual(
            response.irc_message,
            'MY TARGET is at 1.0 (Max 1.0)'
        )

    def test_increment_already_max(self):
        """
        If the `current` is already at `max`, no OSC values should be sent from "increment",
        but the IRC message should still be created
        """
        target = OSCTarget(
            name='My Target',
            address='/osc/address',
            initial=1.0,
            delta=0.07,
            max=1.0,
        )
        response = target.run_action('increment')
        self.assertAlmostEqual(target.current, 1.0)
        self.assertIsNone(response.osc_value)
        self.assertIsNone(response.osc_address)
        self.assertEqual(
            response.irc_message,
            'MY TARGET is at 1.0 (Max 1.0)'
        )

    def test_decrement_inside_range(self):
        """
        Running the "decrement" action should subtract the target's `delta` to
        the current value.  Repeated runs should continue to decrease the value
        """
        target = OSCTarget(
            name='My Target',
            address='/osc/address',
            initial=0.5,
            delta=0.07,
            min=0.0,
        )

        response = target.run_action('decrement')
        self.assertAlmostEqual(response.osc_value, 0.43)
        self.assertAlmostEqual(target.current, 0.43)
        self.assertEqual(response.osc_address, '/osc/address')
        self.assertEqual(
            response.irc_message,
            'MY TARGET is at 0.43 (Min 0.0)'
        )

        response = target.run_action('decrement')
        self.assertAlmostEqual(response.osc_value, 0.36)
        self.assertAlmostEqual(target.current, 0.36)

        response = target.run_action('decrement')
        self.assertAlmostEqual(response.osc_value, 0.29)
        self.assertAlmostEqual(target.current, 0.29)

    def test_decrement_overlapping_range(self):
        """
        if the delta + current is less than the min, the `decrement` value should
        be clamped up to min, but an osc_value should still be sent
        """
        target = OSCTarget(
            name='My Target',
            address='/osc/address',
            initial=0.03,
            delta=0.07,
            min=0.0,
        )

        response = target.run_action('decrement')
        self.assertAlmostEqual(response.osc_value, 0.0)
        self.assertAlmostEqual(target.current, 0.0)
        self.assertEqual(response.osc_address, '/osc/address')
        self.assertEqual(
            response.irc_message,
            'MY TARGET is at 0.0 (Min 0.0)'
        )

    def test_decrement_already_min(self):
        """
        If the `current` is already at `min`, no OSC values should be sent from "decrement",
        but the IRC message should still be created
        """
        target = OSCTarget(
            name='My Target',
            address='/osc/address',
            initial=0.0,
            delta=0.07,
            min=0.0,
        )
        response = target.run_action('decrement')
        self.assertAlmostEqual(target.current, 0.0)
        self.assertIsNone(response.osc_value)
        self.assertIsNone(response.osc_address)
        self.assertEqual(
            response.irc_message,
            'MY TARGET is at 0.0 (Min 0.0)'
        )

    def test_set_in_range(self):
        """
        If the passed value is within the range, the `current` value should be updated
        and the message should be generated based on the direction that the value moved
        """
        target = OSCTarget(
            name='My Target',
            address='/osc/address',
            initial=0.5,
            min=0.0,
            max=1.0,
            delta=0.07,
        )

        response = target.run_action('set', 0.65)
        self.assertAlmostEqual(response.osc_value, 0.65)
        self.assertAlmostEqual(target.current, 0.65)
        self.assertEqual(response.osc_address, '/osc/address')
        self.assertEqual(
            response.irc_message,
            'MY TARGET is at 0.65 (Max 1.0)'
        )

        response = target.run_action('set', 0.43)
        self.assertAlmostEqual(response.osc_value, 0.43)
        self.assertAlmostEqual(target.current, 0.43)
        self.assertEqual(response.osc_address, '/osc/address')
        self.assertEqual(
            response.irc_message,
            'MY TARGET is at 0.43 (Min 0.0)'
        )

    def test_set_outside_range(self):
        """
        If the set value is outside the min or max, the out_of_bounds message should
        be sent to IRC, and no osc_value should be sent
        """
        target = OSCTarget(
            name='My Target',
            address='/osc/address',
            initial=0.5,
            min=0.1,
            max=1.0,
            delta=0.07,
        )

        response = target.run_action('set', 1.1)
        self.assertAlmostEqual(target.current, 0.5)
        self.assertIsNone(response.osc_value)
        self.assertIsNone(response.osc_address)
        self.assertEqual(
            response.irc_message,
            '1.1 is out of bounds for MY TARGET (Min 0.1, Max 1.0)'
        )

        response = target.run_action('set', 0.05)
        self.assertAlmostEqual(target.current, 0.5)
        self.assertIsNone(response.osc_value)
        self.assertIsNone(response.osc_address)
        self.assertEqual(
            response.irc_message,
            '0.05 is out of bounds for MY TARGET (Min 0.1, Max 1.0)'
        )

    def test_invalid_value(self):
        """
        If a non-floatable is passed to a `run_action`, it should send a `not valid value` error
        """
        target = OSCTarget(
            name='My Target',
            address='/osc/address',
            initial=0.5,
            min=0.1,
            max=1.0,
            delta=0.07,
        )

        response = target.run_action('set', 'bar')
        self.assertEqual(response.irc_message, 'bar is not a valid value for MY TARGET')
        self.assertIsNone(response.osc_value)
        self.assertIsNone(response.osc_address)

    def test_increment_extra_value(self):
        """
        Passing an extra value with increment into `run_action` should have no effect
        """
        target = OSCTarget(
            name='My Target',
            address='/osc/address',
            initial=0.5,
            min=0.1,
            max=1.0,
            delta=0.07,
        )

        response = target.run_action('increment', '.75')
        self.assertAlmostEqual(response.osc_value, 0.57)
        self.assertAlmostEqual(target.current, 0.57)
