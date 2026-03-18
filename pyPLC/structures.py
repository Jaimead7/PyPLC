from enum import IntEnum, unique

from snap7.error import error_text
from typing_extensions import Self

from .logging import pyplc_logger


@unique
class PLCComResult(IntEnum):
    NO_ACTION = 100
    SUCCESS = 200
    UNESPECIFY_ERROR = 400
    NOT_CONNECTED = 401
    INVALID_PARAMS = 402
    READ_ONLY = 403
    UNCOMPLETED = 404

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
