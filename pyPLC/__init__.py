import logging

from pyUtils import Styles, debugLog

from .src.plcManager import *
from .src.plcMemoryAreas import (PLCDB, PLCInputs, PLCMarkers, PLCMemoryArea,
                                 PLCOutputs, PLCReadWrite, PLCVarDict)
from .src.plcVar import PLCMemoryOffset, PLCReadWrite, PLCVar
from .src.plcVarTypes import PLCVarType, PLCVarTypesFactory

logger: logging.Logger = logging.getLogger('snap7.client')
logger.disabled = True
logger: logging.Logger = logging.getLogger('snap7.common')
logger.disabled = True

debugLog(f'Package loaded: myPLC', Styles.GREEN)
