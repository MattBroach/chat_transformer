class ActionResponse:
    """
    Contains data necessary to both set the appropriate OSC value (if required),
    and send the current status of the variable in question to IRC.
    """
    def __init__(self, irc_message, osc_value=None, osc_address=None):
        self.irc_message = irc_message
        self.osc_value = osc_value
        self.osc_address = osc_address

    @property
    def has_osc_update(self):
        return self.osc_value is not None and self.osc_address is not None

    def __str__(self):
        return self.irc_message
