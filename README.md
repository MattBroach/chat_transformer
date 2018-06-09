[![Build Status](https://travis-ci.org/MattBroach/irc2osc.svg?branch=master)](https://travis-ci.org/MattBroach/irc2osc)
[![PyPI version](https://badge.fury.io/py/irc2osc.svg)](https://badge.fury.io/py/irc2osc)

# IRC2OSC

Translates incoming IRC messages to OSC messages.

## Installation

`irc2osc` can be installed using `pip`:

```python
pip install irc2osc
```

## Set up

You must create a `json` file that specifies that mapping of IRC messages to OSC commands. The file must contain a JSON object, where each KEY is an IRC command/message, and the VALUE is a JSON object with the parameters for converting the IRC message to OSC commands.  For example:

```json
{
    "brightness": {
        "address": "/osc/brightness/",
        "min": 0.0,
        "max": 2.0,
        "delta": 0.1,
        "initial": 1.0,
    },
    ....
}
```

With the above targets data, the following IRC message:

```
brightness set 0.75
```

would translate to the following OSC Message:

```
/osc/brightness 0.75
```


## Usage

`irc2osc` can be run as a CLI command. At minimum, the port of the OSC reciever, the address of the IRC Server must be specified, and the IRC nickname must be specified. For example, to listen to freenode servers and pass messages to a program listening on port `6789` you'd run:

```bash
irc2osc --osc-ip 6789 --irc-server chat.freenode.net --irc-nickname my_freenode_nick
```

Or with the shorthand commands:

```bash
irc2osc -p 6789 -s chat.freenode.net -n my_freenode_nick
```

Rather than specifying options as command-line arguments, options can instead be set as environment variables:

```bash
export IRC2OSC_OSC_IP=6789
export IRC2OSC_IRC_SERVER=chat.freenode.net
export IRC2OSC_IRC_NICKNAME=my_freenode_nic
irc2osc
```

## Command Line Options

| Argument | Env variable name | Description | Default |
| -------- | ----------------- | ----------- | ------- |
| -i, --osc-ip | IRC2OSC_OSC_IP | IP Address of the OSC target | 127.0.0.1 |
| -p, --osc-port | IRC2OSC_OSC_PORT | Port of the OSC target | |
| -s, --irc-server | IRC2OSC_IRC_SERVER | Server address of the IRC Server | |
| -o, --irc-port | IRC2OSC_IRC_PORT | Port number of the IRC Server | 6667 |
| -n, --irc-nickname | IRC2OSC_IRC_NICKNAME |  address of the IRC Server | |
| -c, --irc-channel | IRC2OSC_IRC_CHANNEL | IRC channel to join and listen for incoming commands. | `IRC_NICKNAME` (above) |
| --irc-password | IRC2OSC_IRC_PASSWORD | Password for authentication on the IRC server | |
| --irc-username | IRC2OSC_IRC_USERNAME | Username for authentication on the IRC server | `IRC_NICKNAME` |
| --irc-realname | IRC2OSC_IRC_REALNAME | Real name on on the IRC server | |
| -t, --targets-file | IRC2OSC_TARGETS_FILE | Path of the file that holds the IRC -> OSC commands mapping | targets.json |
| -w, --watch-targets-file | IRC2OSC_WATCH_TARGETS_FILE | Reload the Targets file when it has changed on disk | False |
| --watch-file-interval | IRC2OSC_WATCH_FILE_INTERVAL | Time (in seconds) between checking for file changes | 60 |
| -v, --verbosity | | How verbose to make the output | 1 (Info) |

## Target File Options

| Key | Description | Default |
| --- | ----------- | ------- |
| address | OSC Address to which the message should be send | |
| min | Mininum possible value for this OSC address | 0.0 |
| max | Maximum possible value for this OSC address | 1.0 |
| delta | Amount to change whenever an INCREMENT or DECREMENT value is received | 0.05 |
| initial | Initial value for this OSC address | 0.5 |
| allowed_actions | Which IRC messages this OSC address will respond to.  Must be an array containing any permutation of INCREMENT, DECREMENT, and SET | [INCREMENT, DECREMENT, SET] |

