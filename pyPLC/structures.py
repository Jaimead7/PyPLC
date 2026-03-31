from enum import IntEnum, unique

from snap7.error import error_text
from typing_extensions import Self

from .logs import pyplc_logger


@unique
class PLCComResult(IntEnum):
    NO_ACTION = 100
    SUCCESS = 200
    UNESPECIFY_ERROR = 400
    NOT_CONNECTED = 401
    INVALID_PARAMS = 402
    READ_ONLY = 403
    UNCOMPLETED = 404
    CONNECTION_REFUSED = 405 #TODO:
    # snap7.error.S7ProtocolError: S7 protocol error (class=0x81, code=0x04): This service is not implemented on the module or a frame error was reported
    # snap7.error.S7ProtocolError: Read operation failed: Invalid address (0x05)

    def is_error(self) -> bool:
        return 400 <= self.value < 500


class PLCClientErrors:
    NOT_CONNECTED = RuntimeError(error_text(0x92746))
    INVALID_PARAMS = RuntimeError(error_text(0x200000))

    def __new__(cls) -> Self:
        msg: str = f'"{cls.__name__}" is not instantiable.'
        pyplc_logger.critical(msg)
        raise RuntimeError(msg)

    @staticmethod
    def get_str(error: RuntimeError) -> str:
        if str(error) == str(PLCClientErrors.NOT_CONNECTED):
            return 'PLC not connected.'
        if str(error) == str(PLCClientErrors.INVALID_PARAMS):
            return 'Invalid parameters.'
        return 'Unknown error.'
