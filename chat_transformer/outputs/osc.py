from collections import Iterable

from pythonosc.osc_message_builder import OscMessageBuilder

from .udp import UDPOutput


class OSCOutput(UDPOutput):
    def send(self, value, address='', **kwargs):
        """
        send structures OSC message via UDP
        """
        msg = self.build_osc_message(address, value)
        self.transport.sendto(msg)

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
