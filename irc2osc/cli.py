import os
import sys
import argparse
import logging
import asyncio

from .client import Irc2OscClient

logger = logging.getLogger(__name__)


class CLI:
    """
    Command-line interface for running the IRC -> OSC bridge
    """
    description = (
        'IRC -> OSC Bridge: A Client to connect to IRC and transfrom messages to OSC data'
    )

    def __init__(self):
        self.parser = argparse.ArgumentParser(
            description=self.description,
        )
        self.parser.add_argument(
            '-i',
            '--osc-ip',
            dest='osc_ip',
            help='IP Address of the OSC target. Default is 127.0.0.1.',
            default=os.environ.get('IRC2OSC_OSC_IP', '127.0.0.1'),
        )
        self.parser.add_argument(
            '-p',
            '--osc-port',
            dest='osc_port',
            help='Port of the OSC target. No default value.',
            default=os.environ.get('IRC2OSC_OSC_PORT', None),
        )
        self.parser.add_argument(
            '-c',
            '--irc-channel',
            dest='irc_channel',
            help=(
                'IRC channel to join and listen for incoming commands. '
                'If no value is supplied, the irc user nickname used to connect to '
                'the server will be used.'
            ),
            default=os.environ.get('IRC2OSC_IRC_CHANNEL', None),
        )
        self.parser.add_argument(
            '-s',
            '--irc-server',
            dest='irc_server',
            help='Server address of the IRC Server. No default value.',
            default=os.environ.get('IRC2OSC_IRC_SERVER', None),
        )
        self.parser.add_argument(
            '-o',
            '--irc-port',
            dest='irc_port',
            help='Port number of the IRC Server to connect to. Default value is 6667.',
            default=os.environ.get('IRC2OSC_IRC_PORT', 6667),
        )
        self.parser.add_argument(
            '-n'
            '--irc-nickname',
            dest='irc_nickname',
            help='Nickname for authentication on the IRC server. No default value.',
            default=os.environ.get('IRC2OSC_IRC_NICKNAME', None),
        )
        self.parser.add_argument(
            '--irc-password',
            dest='irc_password',
            help='Password for authentication on the IRC server. No default value.',
            default=os.environ.get('IRC2OSC_IRC_PASSWORD', None),
        )
        self.parser.add_argument(
            '--irc-username',
            dest='irc_username',
            help=(
                'Username for authentication on the IRC server. '
                'If no value is provided, the value for `irc_nickname` will be used.'
            ),
            default=os.environ.get('IRC2OSC_IRC_USERNAME', None),
        )
        self.parser.add_argument(
            '--irc-realname',
            dest='irc_realname',
            help=(
                'Real name on the IRC server. No default value.'
            ),
            default=os.environ.get('IRC2OSC_IRC_REALNAME', None),
        )
        self.parser.add_argument(
            '-t',
            '--targets-file',
            dest='targets_file',
            help=(
                'Path of the file that holds the IRC -> OSC commands mapping. '
                'Default is `targets.json`.'
            ),
            default=os.environ.get('IRC2OSC_TARGETS_FILE', 'targets.json')
        )
        self.parser.add_argument(
            '-v',
            '--verbosity',
            type=int,
            help='How verbose to make the output. Default is 1 (INFO)',
            default=1,
        )
        self.parser.add_argument(
            '-w',
            '--watch-targets-file',
            dest='watch_targets_file',
            help=(
                'Reload the Targets file when it has changed on disk. set to True to initiate '
                'autoreload.  All other values (or no value) will be interpreted as False.'
            ),
            default=os.environ.get('IRC2OSC_WATCH_TARGETS_FILE', False)
        )
        self.parser.add_argument(
            '--watch-file-interval',
            dest='watch_file_interval',
            help=(
                'Time (in seconds) between checking for file changes.  Default is 60'
            ),
            default=os.environ.get('IRC2OSC_WATCH_FILE_INTERVAL', 60)
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

        # Check that requires arguments received a value either from CLI args or env vars
        if not all([args.osc_port, args.irc_server, args.irc_nickname]):
            raise ValueError(
                "--osc-port, --irc_server, and --irc_nickname are required arguments. "
                "Please add them via the command line or their respective env variables."
            )

        watch_targets_file = args.watch_targets_file in ['true', 'True']

        client = Irc2OscClient(
            args.osc_port,
            irc_channel=args.irc_channel if args.irc_channel is not None else args.irc_nickname,
            osc_ip=args.osc_ip,
            targets_file=args.targets_file,
            watch_targets_file=watch_targets_file,
            watch_file_interval=float(args.watch_file_interval)
        )

        client.connect(
            args.irc_server,
            args.irc_port,
            args.irc_nickname,
            password=args.irc_password,
            username=args.irc_username,
            ircname=args.irc_realname,
        )

        loop = client.reactor.loop

        try:
            client.start()
        except KeyboardInterrupt:
            logger.info("Disconnecting from {}:{}...".format(
                client.connection.server, client.connection.port
            ))
            client.disconnect()

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
