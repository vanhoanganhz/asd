# Decompiled with PyLingual (https://pylingual.io)
# Internal filename: core\exceptions\base.py
# Bytecode version: 3.11a7e (3495)
# Source timestamp: 1970-01-01 00:00:00 UTC (0)

class APIError(Exception):
    BASE_MESSAGES = ['refresh your captcha!!', 'Incorrect answer. Try again!']
    pass

    def __init__(self, error: str, response_data: dict=None):
        self.error = error
        self.response_data = response_data

    @property
    def error_message(self) -> str:
        if self.response_data:
            try:
                return self.response_data['msg']
            except KeyError:
                return str(self.error)
        return None

    def __str__(self):
        return self.error

class NodeDisconnected(Exception):
    """Raised when the node is disconnected"""