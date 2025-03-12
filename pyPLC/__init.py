from pyUtils import Styles, debugLog

from .src.plcManager import *
from .src.plcMemoryAreas import (PLCDB, PLCInputs, PLCMarkers, PLCMemoryArea,
                                 PLCOutputs, PLCReadWrite, PLCVarDict)
from .src.plcVar import PLCMemoryOffset, PLCReadWrite, PLCVar
from .src.plcVarTypes import PLCVarType, PLCVarTypesFactory

debugLog(f'Package loaded: myPLC', Styles.GREEN)
