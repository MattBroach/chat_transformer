import json
import logging
import asyncio

from irc.client_aio import AioSimpleIRCClient

from .utils import class_from_string
from .commands import InvalidActionError, Command
from .watchers import FileWatcher

logger = logging.getLogger(__name__)


DEFAULT_OUTPUT_CLASSES = {
    'osc': 'chat_transformer.outputs.osc.OSCOutput',
    'http': 'chat_transformer.outputs.http.HTTPOutput',
}


class TransformerClient(AioSimpleIRCClient):
    """
    Takes data from an IRC server, parses it, and passes the appropriate data
    the appropriate output(s), e.g. OSC, http, and/or back out to IRC
    """
    reconnect_delay = 60

    def __init__(
        self,
        irc_channel=None,
        commands_file="targets.json",
        watch_commands_file=False,
        watch_file_interval=60,
        loop=None,
        output_data={},
    ):
        self.irc_channel = self.format_irc_channel(irc_channel) if irc_channel is not None else None

        self.commands = {}
        self.commands_file = commands_file
        self.load_commands()

        self.loop = loop if loop is not None else asyncio.get_event_loop()

        # Initialize outputs
        self.outputs = {}
        for key, value in output_data.items():
            output_cls_str = value.pop('class', DEFAULT_OUTPUT_CLASSES[key])
            output_cls = class_from_string(output_cls_str)
            self.outputs[key] = output_cls(**value)

        # Init from AioSimpleIRRCClient, but passing the event loop
        self.reactor = self.reactor_class(loop=self.loop)
        self.connection = self.reactor.server()
        self.reactor.add_global_handler("all_events", self._dispatcher, -10)

        if watch_commands_file:
            watcher = FileWatcher(
                self.commands_file, self.on_reload, loop=self.loop, check_interval=watch_file_interval
            )
            watcher.start()

    def on_reload(self):
        """
        Fires when the commands file is reloaded, if `watch_commands_file` is True
        """
        self.load_commands()
        self.send_all()

    def format_irc_channel(self, irc_channel):
        """
        ensures the irc_channel starts with '#'
        """
        return irc_channel if irc_channel[0] == '#' else '#{}'.format(irc_channel)

    async def connect(self, irc_server, irc_port, irc_nickname, is_reconnect=False, *args, **kwargs):
        """
        Creates both IRC and OSC connections
        """
        self.irc_server = irc_server
        self.irc_port = irc_port
        self.irc_nickname = irc_nickname

        if self.irc_channel is None:
            self.irc_channel = self.format_irc_channel(self.irc_nickname)

        for output in self.outputs.values():
            await output.connect()

        self.send_all()

        await self.connection.connect(irc_server, irc_port, irc_nickname, *args, **kwargs)

        if not is_reconnect:
            self.loop.call_later(self.reconnect_delay, self.reconnect_checker)

    def on_welcome(self, connection, event):
        """
        When connection is established, join the target IRC channel
        to begin receiving messages
        """
        self.connection.join(self.irc_channel)

    def irc_send(self, message):
        """
        Sends message to the joined IRC channel
        """
        self.connection.privmsg(self.irc_channel, message)

    def load_commands(self):
        """
        load commands from file.  IRC commands should come in the form of:

            COMMAND ACTION <VALUE>

        JSON values should be of the form:

            {
                "COMMAND": {
                    "min": MIN_VALUE,
                    "max": MAX_VALUE,
                    "delta": INCREMENT/DECREMENT_VALUE,
                    "initial": INITIAL_VALUE,
                    "type": "NUMBER" (or "BOOLEAN", "MESSAGE"),
                    "outputs": {
                        "osc": { "address": "/OSC/ADDRESS" },
                        "http": { "endpoint": "/HTTP/ENDPOINT" },
                        ...
                    }
                },
                ...
            }
        """
        with open(self.commands_file) as commands_file:
            commands = json.loads(commands_file.read())

        # Load "initial" value into "current" value
        self.commands = {
            key.lower(): Command(
                name=key.lower(),
                current=self.command_value(key.lower()),
                **value
            )
            for key, value in commands.items()
        }

    def send_all(self):
        """
        Initializes the OSC command with all current/initial values
        """
        for command in self.commands.values():
            value = command.current if command.current is not None else command.initial

            for output_name, output in self.outputs.items():
                output.send_full(
                    value,
                    min=command.min,
                    max=command.max,
                    **command.outputs[output_name],
                )

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
        send it to the appropriate Command for handling
        """
        tokens = irc_command.split(' ')
        if len(tokens) == 2:
            command_name, action = tokens
            value = None
        elif len(tokens) == 3:
            command_name, action, value = tokens
        else:
            return

        command = self.commands.get(command_name.lower(), None)

        if command is not None:
            try:
                response = command.run_action(action, value)
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

        if response.has_output:
            for output_name, output_params in response.output_params.items():
                self.outputs[output_name].send(response.value, **output_params)

    def command_value(self, command):
        """
        Returns the current value of a given Command.  Currently, mostly
        a convenience function for testing and debugging
        """
        command_data = self.commands.get(command, None)
        return command_data.current if command_data is not None else None

    def cleanup(self):
        for output in self.outputs.values():
            output.cleanup()

    def reconnect_checker(self):
        """
        Checks at a regular interval as to whether the connection to IRC has been
        disconnected, and re-starts the connection if it has
        """
        if not self.connected and self.autoreconnect:
            logger.info('Attempting to reconnect to {}:{}'.format(
                self.connection.server, self.connection.port
            ))
            asyncio.ensure_future(
                self.connect(
                    self.connection.server,
                    self.connection.port,
                    self.connection.nickname,
                    password=self.connection.password,
                    username=self.connection.username,
                    ircname=self.connection.ircname,
                    is_reconnect=True,
                ),
                loop=self.loop
            )

        self.loop.call_later(self.reconnect_delay, self.reconnect_checker)
