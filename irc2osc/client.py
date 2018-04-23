import json
import logging

from pythonosc.udp_client import SimpleUDPClient

from .targets import InvalidActionError, OSCTarget

logger = logging.getLogger(__name__)


class IRC_2_OSC_Client:
    """
    Takes data from an IRC server, parses it, and passes the appropriate data
    to OSC
    """
    def __init__(
        self,
        osc_port,
        osc_ip='127.0.0.1',
        commands_file="commands.json"
        irc_channel=""
    ):
        self.port = port
        self.ip = ip

        self.osc_client = SimpleUDPClient(
            self.ip, self.port
        )

        self.targets_file = commands_file

        self.irc_client = None

    def osc_send(self, address, value):
        """
        Sends message to set value via IRC
        """
        self.osc_client.send_message(address, value)

    def irc_send(self, message):
        """
        Sends message to the joined IRC channel
        """
        pass

    def save_targets(self):
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
        targets_file = open(self.targets_file).read()
        targets = json.loads(targets_file)

        # Load "initial" value into "current" value
        self.targets = {
            key: OSCTarget(
                name=key,
                irc_client=self.irc_client,
                osc_client=self.osc_client,
                **value
            )
            for key, value in commands
        }

    def save_targets(self):
        """
        Write current commands (with current values) to file
        """
        with open(self.commands_file, 'w') as outfile:
            json.dump(self.commands, outfile, indent=4)

    def parse_command(self, irc_command):
        """
        break irc_command into its parts and, if it's a valid command, 
        send it to the appropriate OSCTarget for handling
        """
        tokens = irc_command.split(' ')
        if tokens.length == 2:
            target, action = tokens
            value = None
        elif tokens.length == 3:
            target, action, value = tokens
        else:
            return

        osc_target = self.targets.get(target, None)

        if osc_target is not None:
            try:
                response = osc_target.run_action(action, value)
            except InvalidActionError as error:
                logger.error(str(error.exception))

            self.handle_action_response(response)

    def handle_action_response(self, response):
        """
        Sends appropriate response message to IRC.
        If an OSC update is needed, also sends the appropriate OSC msg
        """
        self.irc_send(response.irc_message)

        if response.has_osc_update:
            self.osc_send(response.osc_address, response.osc_value)
