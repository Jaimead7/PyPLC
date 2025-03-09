from pyUtils import Styles, debugLog

from .src.plcManager import *
from .src.plcMemotyAreas import *
from .src.plcVar import *
from .src.plcVarTypes import PLCVarType, PLCVarTypesFactory

debugLog(f'Package loaded: myPLC', Styles.GREEN)
