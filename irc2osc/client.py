import json
import logging
import asyncio
from collections import Iterable
from irc.client_aio import AioSimpleIRCClient

from pythonosc.osc_message_builder import OscMessageBuilder

from .targets import InvalidActionError, OSCTarget
from .protocol import OSCProtocol
from .watchers import FileWatcher

logger = logging.getLogger(__name__)


class Irc2OscClient(AioSimpleIRCClient):
    """
    Takes data from an IRC server, parses it, and passes the appropriate data
    to OSC
    """
    def __init__(
        self,
        osc_port,
        irc_channel=None,
        osc_ip='127.0.0.1',
        targets_file="targets.json",
        watch_targets_file=False,
        watch_file_interval=60,
        loop=None,
    ):
        self.osc_port = osc_port
        self.osc_ip = osc_ip

        self.irc_channel = self.format_irc_channel(irc_channel) if irc_channel is not None else None

        self.targets = {}
        self.targets_file = targets_file
        self.load_targets()

        self.loop = loop if loop is not None else asyncio.get_event_loop()

        # Init from AioSimpleIRRCClient, but passing the event loop
        self.reactor = self.reactor_class(loop=self.loop)
        self.connection = self.reactor.server()
        self.reactor.add_global_handler("all_events", self._dispatcher, -10)

        if watch_targets_file:
            watcher = FileWatcher(
                self.targets_file, self.load_targets, loop=self.loop, check_interval=watch_file_interval
            )
            watcher.start()

    def format_irc_channel(self, irc_channel):
        """
        ensures the irc_channel starts with '#'
        """
        return irc_channel if irc_channel[0] == '#' else '#{}'.format(irc_channel)

    def connect(self, irc_server, irc_port, irc_nickname, *args, **kwargs):
        """
        Creates both IRC and OSC connections
        """
        self.irc_server = irc_server
        self.irc_port = irc_port
        self.irc_nickname = irc_nickname

        if self.irc_channel is None:
            self.irc_channel = self.format_irc_channel(self.irc_nickname)

        osc_connect = self.loop.create_datagram_endpoint(
            lambda: OSCProtocol(), remote_addr=(self.osc_ip, self.osc_port)
        )
        self.osc_transport, _ = self.loop.run_until_complete(osc_connect)

        self.osc_send_all()

        super().connect(irc_server, irc_port, irc_nickname, *args, **kwargs)

    def on_welcome(self, connection, event):
        """
        When connection is established, join the target IRC channel
        to begin receiving messages
        """
        self.connection.join(self.irc_channel)

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
        self.connection.privmsg(self.irc_channel, message)

    def load_targets(self):
        """
        load commands from file.  IRC commands should come in the form of:

            TARGET ACTION <VALUE>

        JSON values should be of the form:

            {
                "TARGET": {
                    "address": "/OSC/ADDRESS",
                    "min": MIN_VALUE,
                    "max": MAX_VALUE,
                    "delta": INCREMENT/DECREMENT_VALUE,
                    "initial": INITIAL_VALUE,
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
                current=self.target_value(key.lower()),
                **value
            )
            for key, value in targets.items()
        }


    def osc_send_all(self):
        """
        Initializes the OSC target with all current/initial values
        """
        for target in self.targets.values():
            self.osc_send(
                target.address, target.current if target.current is not None else target.initial
            )

    def save_targets(self):
        """
        Write current commands (with current values) to file
        """
        with open(self.commands_file, 'w') as outfile:
            json.dump(self.commands, outfile, indent=2)

    def on_privmsg(self, connection, event):
        """
        Pass to incoming PRIVMSG to command parser
        """
        self._handle_on_message(connection, event)

    def on_pubmsg(self, connection, event):
        """
        Pass to incoming PUBMSG to command parser
        """
        self._handle_on_message(connection, event)

    def _handle_on_message(self, connection, event):
        """
        Redirects all incoming IRC messages to a single parser
        """
        self.parse_command(event.arguments[0])

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
