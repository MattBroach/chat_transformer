class BaseOutput:
    @classmethod
    def initialize(cls, *args, **kwargs):
        """
        Hook for performing specific output-specific tasks on initialization
        """
        return cls(*args, **kwargs)

    def connect(self, *args, **kwargs):
        """
        Hook to connect to a given output, if necessary.  Not all outputs
        require persistent connections
        """
        pass

    def send(self, data, **kwargs):
        """
        Send data to the given output.  Required for all possible outputs
        """
        raise NotImplemetedError
