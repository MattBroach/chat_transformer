class ActionResponse:
    """
    Contains data necessary to both set the output values,
    and send the current status of the variable in question to IRC.
    """
    def __init__(self, irc_message, value=None, output_params=None):
        self.irc_message = irc_message
        self.value = value
        self.output_params = output_params

    @property
    def has_output(self):
        return self.value is not None and self.output_params is not None

    def __str__(self):
        return self.irc_message
