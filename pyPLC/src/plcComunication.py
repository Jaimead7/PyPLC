from snap7.error import error_text

from pyUtils import NoInstantiable


class PLCComunicationResult(NoInstantiable):
    SUCCESS = 0
    UNESPECIFY_ERROR = 100
    NOT_CONNECTED = 101
    INVALID_PARAMS = 102
    READ_ONLY_VALUE = 103


class PLCClientErrors(NoInstantiable):
    NOT_CONNECTED = RuntimeError(error_text(0x92746))
    INVALID_PARAMS = RuntimeError(error_text(0x200000))
    
    @staticmethod
    def getStr(error: RuntimeError) -> str:
        if str(error) == str(PLCClientErrors.NOT_CONNECTED):
            return 'PLC not connected'
        if str(error) == str(PLCClientErrors.INVALID_PARAMS):
            return 'Invalid parameters'
        return 'Unknown error'