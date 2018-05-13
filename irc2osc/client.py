import json
import logging
import asyncio
from collections import Iterable

from pythonosc.osc_message_builder import OscMessageBuilder

from .targets import InvalidActionError, OSCTarget
from .protocol import OSCProtocol

logger = logging.getLogger(__name__)


class Irc2OscClient:
    """
    Takes data from an IRC server, parses it, and passes the appropriate data
    to OSC
    """
    def __init__(
        self,
        osc_port,
        osc_ip='127.0.0.1',
        targets_file="targets.json",
        irc_channel="",
        loop=None
    ):
        self.osc_port = osc_port
        self.osc_ip = osc_ip

        self.targets_file = targets_file

        self.irc_client = None

        self.loop = loop if loop is not None else asyncio.get_event_loop()

    def connect(self):
        """
        Creates both IRC and OSC connections
        """
        osc_connect = self.loop.create_datagram_endpoint(
            lambda: OSCProtocol(), remote_addr=(self.osc_ip, self.osc_port)
        )
        self.osc_transport, _ = self.loop.run_until_complete(osc_connect)

    def build_osc_message(self, address, value):
        """
        composes OSC message in proper format for sending
        """
        builder = OscMessageBuilder(address=address)
        if not isinstance(value, Iterable) or isinstance(value, (str, bytes)):
            values = [value]
        else:
            values = value
        for val in values:
            builder.add_arg(val)
        msg = builder.build()

        return msg.dgram

    def osc_send(self, address, value):
        """
        Sends message to set value via IRC
        """
        msg = self.build_osc_message(address, value)
        self.osc_transport.sendto(msg)

    def irc_send(self, message):
        """
        Sends message to the joined IRC channel
        """
        pass

    def load_targets(self):
        """
        load commands from file.  IRC commands should come in the form of:

            !TARGET ACTION <VALUE>

        JSON values should be of the form:

            {
                "TARGET": {
                    "address": "/OSC/ADDRESS",
                    "min": MIN_VALUE,
                    "max": MAX_VALUE,
                    "delta": INCREMENT/DECREMENT_VALUE,
                    "initial": INITIAL_VALUE,
                    "current": LAST_OBSERVED_VALUE,
                    "allowed_actions": [
                        "INCREMENT",
                        "DECREMENT",
                        "SET",
                    ],
                },
                ...
            }
        """
        with open(self.targets_file) as targets_file:
            targets = json.loads(targets_file.read())

        # Load "initial" value into "current" value
        self.targets = {
            key.lower(): OSCTarget(
                name=key.lower(),
                **value
            )
            for key, value in targets.items()
        }

    def save_targets(self):
        """
        Write current commands (with current values) to file
        """
        with open(self.commands_file, 'w') as outfile:
            json.dump(self.commands, outfile, indent=2)

    def parse_command(self, irc_command):
        """
        break irc_command into its parts and, if it's a valid command, 
        send it to the appropriate OSCTarget for handling
        """
        tokens = irc_command.split(' ')
        if len(tokens) == 2:
            target, action = tokens
            value = None
        elif len(tokens) == 3:
            target, action, value = tokens
        else:
            return

        osc_target = self.targets.get(target.lower(), None)

        if osc_target is not None:
            try:
                response = osc_target.run_action(action, value)
            except InvalidActionError as error:
                logger.error(str(error))
            else:
                self.handle_action_response(response)

    def handle_action_response(self, response):
        """
        Sends appropriate response message to IRC.
        If an OSC update is needed, also sends the appropriate OSC msg
        """
        self.irc_send(response.irc_message)

        if response.has_osc_update:
            self.osc_send(response.osc_address, response.osc_value)

    def target_value(self, target):
        """
        Returns the current value of a given target.  Currently, mostly a convenience 
        function for testing and debugging
        """
        target_data = self.targets.get(target, None)
        return target_data.current if target_data is not None else None
