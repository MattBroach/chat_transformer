from unittest import TestCase

from chat_transformer.commands import Command, InvalidActionError


class CommandTests(TestCase):
    def test_str_representation(self):
        """
        String representation of an OSCCommand should be its `name`
        """
        command = Command(
            name='My Command',
        )
        self.assertEqual(str(command), 'My Command')

    def test_invalid_actions_raises_invalid_action_error(self):
        """
        Passing an action not in `allowed_actions` to `run_action` should raise
        an `InvalidActionError`
        """
        command = Command(
            name='My Command',
            allowed_actions=['set', 'get'],
        )

        with self.assertRaises(InvalidActionError) as error:
            command.run_action('increment')

        self.assertEqual(
            str(error.exception),
            '"increment" is not a valid action for command "MY COMMAND"',
        )

    def test_increment_inside_range(self):
        """
        Running the "increment" action should add the command's `delta` to
        the current value.  Repeated runs should continue to increase the value
        """
        command = Command(
            name='My Command',
            initial=0.5,
            delta=0.07,
            max=1.0,
            allowed_actions=['get', 'set', 'increment', 'decrement'],
        )

        response = command.run_action('increment')
        self.assertAlmostEqual(response.value, 0.57)
        self.assertAlmostEqual(command.current, 0.57)
        self.assertEqual(
            response.irc_message,
            'MY COMMAND is at 0.57 (Max 1.0)'
        )

        response = command.run_action('increment')
        self.assertAlmostEqual(response.value, 0.64)
        self.assertAlmostEqual(command.current, 0.64)

        response = command.run_action('increment')
        self.assertAlmostEqual(response.value, 0.71)
        self.assertAlmostEqual(command.current, 0.71)

    def test_increment_overlapping_range(self):
        """
        if the delta + current is greater than the max, the `increment` value should
        be clamped down to max, but an osc_value should still be sent
        """
        command = Command(
            name='My Command',
            initial=0.97,
            delta=0.07,
            max=1.0,
            allowed_actions=['get', 'set', 'increment', 'decrement'],
        )

        response = command.run_action('increment')
        self.assertAlmostEqual(response.value, 1.0)
        self.assertAlmostEqual(command.current, 1.0)
        self.assertEqual(
            response.irc_message,
            'MY COMMAND is at 1.0 (Max 1.0)'
        )

    def test_increment_already_max(self):
        """
        If the `current` is already at `max`, no OSC values should be sent from "increment",
        but the IRC message should still be created
        """
        command = Command(
            name='My Command',
            initial=1.0,
            delta=0.07,
            max=1.0,
            allowed_actions=['get', 'set', 'increment', 'decrement'],
        )
        response = command.run_action('increment')
        self.assertAlmostEqual(command.current, 1.0)
        self.assertIsNone(response.value)
        self.assertEqual(
            response.irc_message,
            'MY COMMAND is at 1.0 (Max 1.0)'
        )

    def test_decrement_inside_range(self):
        """
        Running the "decrement" action should subtract the command's `delta` to
        the current value.  Repeated runs should continue to decrease the value
        """
        command = Command(
            name='My Command',
            initial=0.5,
            delta=0.07,
            min=0.0,
            allowed_actions=['get', 'set', 'increment', 'decrement'],
        )

        response = command.run_action('decrement')
        self.assertAlmostEqual(response.value, 0.43)
        self.assertAlmostEqual(command.current, 0.43)
        self.assertEqual(
            response.irc_message,
            'MY COMMAND is at 0.43 (Min 0.0)'
        )

        response = command.run_action('decrement')
        self.assertAlmostEqual(response.value, 0.36)
        self.assertAlmostEqual(command.current, 0.36)

        response = command.run_action('decrement')
        self.assertAlmostEqual(response.value, 0.29)
        self.assertAlmostEqual(command.current, 0.29)

    def test_decrement_overlapping_range(self):
        """
        if the delta + current is less than the min, the `decrement` value should
        be clamped up to min, but an osc_value should still be sent
        """
        command = Command(
            name='My Command',
            initial=0.03,
            delta=0.07,
            min=0.0,
            allowed_actions=['get', 'set', 'increment', 'decrement'],
        )

        response = command.run_action('decrement')
        self.assertAlmostEqual(response.value, 0.0)
        self.assertAlmostEqual(command.current, 0.0)
        self.assertEqual(
            response.irc_message,
            'MY COMMAND is at 0.0 (Min 0.0)'
        )

    def test_decrement_already_min(self):
        """
        If the `current` is already at `min`, no OSC values should be sent from "decrement",
        but the IRC message should still be created
        """
        command = Command(
            name='My Command',
            initial=0.0,
            delta=0.07,
            min=0.0,
            allowed_actions=['get', 'set', 'increment', 'decrement'],
        )
        response = command.run_action('decrement')
        self.assertAlmostEqual(command.current, 0.0)
        self.assertIsNone(response.value)
        self.assertEqual(
            response.irc_message,
            'MY COMMAND is at 0.0 (Min 0.0)'
        )

    def test_set_in_range(self):
        """
        If the passed value is within the range, the `current` value should be updated
        and the message should be generated based on the direction that the value moved
        """
        command = Command(
            name='My Command',
            initial=0.5,
            min=0.0,
            max=1.0,
            delta=0.07,
            allowed_actions=['get', 'set', 'increment', 'decrement'],
        )

        response = command.run_action('set', 0.65)
        self.assertAlmostEqual(response.value, 0.65)
        self.assertAlmostEqual(command.current, 0.65)
        self.assertEqual(
            response.irc_message,
            'MY COMMAND is at 0.65 (Max 1.0)'
        )

        response = command.run_action('set', 0.43)
        self.assertAlmostEqual(response.value, 0.43)
        self.assertAlmostEqual(command.current, 0.43)
        self.assertEqual(
            response.irc_message,
            'MY COMMAND is at 0.43 (Min 0.0)'
        )

    def test_set_outside_range(self):
        """
        If the set value is outside the min or max, the out_of_bounds message should
        be sent to IRC, and no osc_value should be sent
        """
        command = Command(
            name='My Command',
            initial=0.5,
            min=0.1,
            max=1.0,
            delta=0.07,
            allowed_actions=['get', 'set', 'increment', 'decrement'],
        )

        response = command.run_action('set', 1.1)
        self.assertAlmostEqual(command.current, 0.5)
        self.assertIsNone(response.value)
        self.assertEqual(
            response.irc_message,
            '1.1 is out of bounds for MY COMMAND (Min 0.1, Max 1.0)'
        )

        response = command.run_action('set', 0.05)
        self.assertAlmostEqual(command.current, 0.5)
        self.assertIsNone(response.value)
        self.assertEqual(
            response.irc_message,
            '0.05 is out of bounds for MY COMMAND (Min 0.1, Max 1.0)'
        )

    def test_invalid_value(self):
        """
        If a non-floatable is passed to a `run_action`, it should send a `not valid value` error
        """
        command = Command(
            name='My Command',
            initial=0.5,
            min=0.1,
            max=1.0,
            delta=0.07,
            allowed_actions=['get', 'set', 'increment', 'decrement'],
        )

        response = command.run_action('set', 'bar')
        self.assertEqual(
            response.irc_message,
            '"MY COMMAND set" requires a number value between 0.1 and 1.0',
        )
        self.assertIsNone(response.value)

    def test_increment_extra_value(self):
        """
        Passing an extra value with increment into `run_action` should have no effect
        """
        command = Command(
            name='My Command',
            initial=0.5,
            min=0.1,
            max=1.0,
            delta=0.07,
            allowed_actions=['get', 'set', 'increment', 'decrement'],
        )

        response = command.run_action('increment', '.75')
        self.assertAlmostEqual(response.value, 0.57)
        self.assertAlmostEqual(command.current, 0.57)

    def test_echo(self):
        """
        Calling `run_action` with no action should call the associated
        "echo" value
        """
        command = Command(
            name='My Command',
            echo="This is a description of my command"
        )

        response = command.run_action()
        self.assertEqual(
            response.irc_message,
            "This is a description of my command",
        )
        self.assertIsNone(response.value)
