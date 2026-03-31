import logging

from .file_readers import FileReader, FileReaderReg
from .logs import Styles, pyplc_logger
from .manager import PLCManager
from .memory_areas import (PLCDB, PLCInputs, PLCMarks, PLCMemoryArea,
                           PLCOutputs, PLCReadWrite, PLCVarDict)
from .structures import PLCClientErrors, PLCComResult
from .var_types import PLCVarType, PLCVarTypesReg
from .vars import PLCMemoryOffset, PLCReadWrite, PLCVar

logger: logging.Logger = logging.getLogger('snap7.client')
logger.disabled = True
logger: logging.Logger = logging.getLogger('snap7.common')
logger.disabled = True

pyplc_logger.debug(f'Package loaded.', Styles.SUCCEED)
