[![Build Status](https://travis-ci.org/MattBroach/chat_transformer.svg?branch=master)](https://travis-ci.org/MattBroach/chat_transformer)
[![PyPI version](https://badge.fury.io/py/chat_transformer.svg)](https://badge.fury.io/py/chat_transformer)

# chat_transformer

Translates incoming IRC messages to OSC, HTTP, or any other output format you need.

## Installation

`chat_transformer` can be installed using `pip`:

```python
pip install chat_transformer
```

## Set up

You must create a `json` file that specifies that mapping of IRC messages to output data. The file must contain a JSON object, where each KEY is an IRC command/message, and the VALUE is a JSON object with the parameters for converting the IRC message to OSC commands.  For example:

```json
{
    "brightness": {
        "address": "/osc/brightness/",
        "min": 0.0,
        "max": 2.0,
        "delta": 0.1,
        "initial": 1.0,
        "outputs": {
            "osc": {"address": "/video/brightness"},
            "http": {"command_name": "brightness"}
        }
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

and the following POST message to the main HTTP target:

```
{brightness: {"value": 0.75, "min": 0.0, "max": 2.0}}
```

## Usage

`chat_transformer` can be run as a CLI command. At minimum, you must specify the location of a config file that will hold the various settings necessary for running `chat_transformer`: 

```bash
chat_transformer --config /path/to/my/config.json
```

Or with the shorthand commands:

```bash
chat_transformer -c /path/to/my/config.json
```

Rather than specifying options as command-line arguments, options can instead be set as environment variables:

```bash
export CHAT_TRANSFORMER_CONFIG=/path/to/my/config.json
chat_transformer
```

## Command Line Options

| Argument | Env variable name | Description | Default |
| -------- | ----------------- | ----------- | ------- |
| -c, --config | CHAT_TRANSFORMER_CONFIG | filepath of the config JSON file | config.json
| -v, --verbosity | | How verbose to make the output | 1 (Info) |

## Configuration File

The configuration JSON file holds all the necessary settings for running your instance of `chat_transformer`. At bear minimum it must include an `irc` key with the server and login information, a `commands` key with information about the the commands JSON file (which contains the list of active commands to listen for and respond to), and at least one output (`osc` and `http` are supported out of the box).  Here's an example of a minimal configuration file that's listening to freenode:

```json
{
    "irc": {
        "server": "chat.freenode.net"
    },
    "commands": {
        "filename": "/path/to/my/commands.json"
    },
    "outputs": {
        "osc": {
            "port": 9876
        }
    }
}
```

## Configuration File Ooptions

| Key   | Description | Default |
| ----- | ----------- | ------- |
| `irc.server` | Server address of the IRC Server | None (**Required**) |
| `irc.port` | Port number of the IRC Server | 6667 |
| `irc.nickname` | Nickname for authnenticating on IRC | None (**Required**) |
| `irc.password` | Password for authentication on the IRC server | |
| `irc.username` | Username for authentication on the IRC server | `irc.nickname` (above) |
| `irc.realname` | Real name on on the IRC server | |
| `irc.channel` | IRC channel to join and listen for incoming commands. | `irc.nickname` (above) |
| `commands.filename` |  Path of the file that holds the IRC commands to listen | commands.json |
| `commands.watch` | Reload the commands file when it has changed on disk | False |
| `commands.watch_interval` | Time (in seconds) between checking for file changes | 60 |
| `output.osc.ip` | IP Address of the OSC target | 127.0.0.1 |
| `output.osc.post` | Port of the OSC target | None (**Required** if `OSC` is used) |
| `output.http.base_url` | URL target to post to | None (**Required** if `HTTP` is used) |
| `output.http.jwt_secret` | JWT secret for using JWT encoding | |

## Commands File Options

| Key | Description | Default |
| --- | ----------- | ------- |
| `min` | Mininum possible value for this command | 0.0 |
| `max` | Maximum possible value for this command | 1.0 |
| `delta` | Amount to change whenever an INCREMENT or DECREMENT command is received | 0.05 |
| `initial` | Initial value for this command | 0.5 |
| `outputs.osc.address` | OSC Address to which the message should be send | |
| `outputs.http.command_new` | Key to used for the POSTed HTTP data | |
| `outputs.http.endpoint` | Endpoint to POST to for this command | |
