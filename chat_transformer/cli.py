import os
import sys
import argparse
import logging
import asyncio
import json

from .client import TransformerClient

logger = logging.getLogger(__name__)


def get_required_key(key, config):
    """
    Standardizes error checking for loading a key from config
    """
    try:
        return config[key]
    except KeyError:
        raise ValueError(
            '"{}" is a required key in your config file.'.format(key)
        )


class CLI:
    """
    Command-line interface for running the IRC chat-to-command transformer
    """
    description = (
        'IRC Chat Transformer: A Client to connect to IRC and transfrom chat messages to other data '
        'formats including UDP, OSC, HTTP.'
    )

    def __init__(self):
        self.parser = argparse.ArgumentParser(
            description=self.description,
        )
        self.parser.add_argument(
            '-c',
            '--config',
            dest='config_file',
            help=(
                'Filename/Filepath of the JSON config file. '
                'See website for config file options: '
                'https://github.com/MattBroach/ChatTransformer'
            ),
            default=os.environ.get('CHAT_TRANSFORMER_CONFIG', 'config.json'),
        )
        self.parser.add_argument(
            '-v',
            '--verbosity',
            type=int,
            help='How verbose to make the output. Default is 1 (INFO)',
            default=1,
        )

    @classmethod
    def entrypoint(cls):
        """
        Main entrypoint for running as CLI
        """
        cls().run(sys.argv[1:])

    def run(self, args):
        """
        Mounts the client, connects to IRC and OSC targets, and enters the main processing loop
        """
        args = self.parser.parse_args(args)

        # Set up logging
        logging.basicConfig(
            level={
                0: logging.WARN,
                1: logging.INFO,
                2: logging.DEBUG,
            }[args.verbosity],
            format="%(asctime)-15s %(levelname)-8s %(message)s",
        )

        with open(args.config_file) as config_file:
            config = json.loads(config_file.read())

        # Parse IRC values
        irc = get_required_key('irc', config)

        irc_server = irc.get('server', None)
        irc_port = irc.get('port', 6667)
        irc_nickname = irc.get('nickname', None)
        irc_channel = irc.get('channel', irc_nickname)
        irc_password = irc.get('password', None)
        irc_realname = irc.get('realname', None)
        irc_username = irc.get('username', None)

        # Check that required IRC arguments are received
        if not all([irc_server, irc_nickname]):
            raise ValueError(
                '"server" and "nickname" are required arguments in your "irc" config.'
            )

        # Parse COMMAND values
        commands = config.get('commands', {})
        commands_file = commands.get('filename', 'commands.json')
        watch_commands_file = commands.get('watch', False)
        watch_interval = commands.get('watch_interval', 60)

        # Load OUTPUT Values
        outputs = get_required_key('outputs', config)

        client = TransformerClient(
            irc_channel=irc_channel if irc_channel is not None else irc_nickname,
            commands_file=commands_file,
            watch_commands_file=watch_commands_file,
            watch_file_interval=watch_interval,
            output_data=outputs,
        )

        loop = client.reactor.loop

        loop.run_until_complete(client.connect(
            irc_server,
            irc_port,
            irc_nickname,
            password=irc_password,
            username=irc_username,
            ircname=irc_realname,
        ))

        try:
            client.start()
        except KeyboardInterrupt:
            logger.info("Disconnecting from {}:{}...".format(
                client.connection.server, client.connection.port
            ))
            client.disconnect()
            client.cleanup()

            tasks = asyncio.gather(
                *asyncio.Task.all_tasks(loop=loop),
                loop=loop,
                return_exceptions=True
            )
            tasks.add_done_callback(lambda t: loop.stop())
            tasks.cancel()

            while not tasks.done() and not loop.is_closed():
                loop.run_forever()
        finally:
            loop.close()
            sys.exit(0)
