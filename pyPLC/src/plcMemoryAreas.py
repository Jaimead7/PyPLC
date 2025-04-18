from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import KW_ONLY, InitVar, dataclass, field
from typing import TYPE_CHECKING, Any, Optional

from snap7.client import Client
from snap7.error import error_text

from pyUtils import (ConfigDict, NoInstantiable, ValidationClass, debugLog,
                     errorLog, warningLog)

if TYPE_CHECKING:
    from .plcManager import PLCManager

from .plcVar import PLCReadWrite, PLCVar, PLCVarDict

#TODO: manage Runtime exceptions in writeArea, writeVarToPLC
#TODO: manage exceptions when client is none

class PLCComunicationResult(NoInstantiable):
    SUCCESS = 0
    UNESPECIFY_ERROR = 100
    NOT_CONNECTED = 101
    INVALID_PARAMS = 102


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
        


@dataclass
class PLCMemoryArea(ValidationClass, ABC):
    variables: PLCVarDict = field(default_factory= PLCVarDict)
    size: int = 0
    _: KW_ONLY
    parent: Optional[PLCManager] = None
    fromDict: InitVar[Optional[dict]] = None

    def __post_init__(self, fromDict: Optional[dict]) -> None:
        if fromDict is not None:
            fromDict = ConfigDict(self.validateDict(fromDict))
            self.setVarsFromDict(fromDict)
        debugLog(f'{self._identifier}: Created')

    @property
    def _identifier(self) -> str:
        if self.parent is None:
            return f'{self.__class__.__name__}'
        return f'{self.__class__.__name__}({self.parent.name})'

    def validate_variables(self, value: Any) -> list[PLCVar]:
        try:
            return PLCVarDict(value)
        except TypeError:
            msg: str = f'Invalid type for {self._identifier}.variables: {value}'
            errorLog(msg)
            raise TypeError(msg)

    def validate_size(self, value: Any) -> int:
        try:
            return self.validatePositiveInt(value)
        except TypeError:
            msg: str = f'Invalid type for {self._identifier}.size: {value}'
            errorLog(msg)
            raise TypeError(msg)

    def validate_parent(self, value: Any) -> Optional[PLCManager]:
        from .plcManager import PLCManager
        if value is None:
            return None
        if isinstance(value, PLCManager):
            return value
        msg: str = f'Invalid type for {self._identifier}.parent: {value}'
        errorLog(msg)
        raise TypeError(msg)

    @abstractmethod
    def setVarsFromDict(self, fromDict: ConfigDict):
        ...

    @abstractmethod
    def readArea(self, client: Client= None) -> int:
        ...

    @abstractmethod
    def _readVar(self, var: PLCVar, client: Client= None) -> Optional[bytearray]:
        ...

    def getVar(self, var: PLCVar | str) -> Any:
        try:
            if isinstance(var, str):
                var = self.variables[var]
            valueToReturn: Any = self.variables[var.name].value
            debugLog(f'{self._identifier}: {valueToReturn} returned')
            return valueToReturn
        except KeyError:
            msg: str = f'{self._identifier}: {var} not found in variables'
            errorLog(msg)
            raise KeyError(msg)

    def readVarFromPLC(self, var: PLCVar | str, client: Client= None) -> Optional[Any]:
        if client is None:
            client = self.parent.client
        try:
            if isinstance(var, str):
                var = self.variables[var]
            self.variables[var.name].value = self._readVar(var, client)
            debugLog(f'{self._identifier}: "{self.variables[var.name]}" readed')
            return self.variables[var.name].value
        except KeyError:
            msg: str = f'{self._identifier}: "{var}" not found in variables'
            errorLog(msg)
            raise KeyError(msg)
        except RuntimeError as e:
            msg: str = f'{self._identifier}: Unable to read "{var}". {PLCClientErrors.getStr(e)}'
            errorLog(msg)
            raise RuntimeError(e)

    def writeArea(self, client: Client= None) -> None:
        if client is None:
            client = self.parent.client
        [self._writeVar(var, client) for var in self.variables]
        debugLog(f'{self._identifier}: Writed')

    @abstractmethod
    def _writeVar(self, var: PLCVar, client: Client= None) -> bool:
        ...

    def setVar(self, var: PLCVar | str, value: Any) -> None:
        try:
            if isinstance(var, str):
                var = self.variables[var]
            self.variables[var.name].value = value
            debugLog(f'{self._identifier}: {self.variables[var.name]} setted')
        except KeyError:
            msg: str = f'{self._identifier}: {var} not found in variables'
            errorLog(msg)
            raise KeyError(msg)

    def writeVarToPLC(self, var: PLCVar | str, value: Any, client: Client= None) -> None:
        if client is None:
            client = self.parent.client
        try:
            if isinstance(var, str):
                var = self.variables[var]
            self.variables[var.name].value = value
            if self._writeVar(self.variables[var.name], client):
                debugLog(f'{self._identifier}: {self.variables[var.name]} writed')
        except KeyError:
            msg: str = f'{self._identifier}: {var} not found in variables'
            errorLog(msg)
            raise KeyError(msg)

    def manageRuntimeError(self, error: Exception) -> int:
        if str(error) == str(PLCClientErrors.NOT_CONNECTED):
            errorLog(f'{self._identifier}: Unable to connect')
            return PLCComunicationResult.NOT_CONNECTED
        if str(error) == str(PLCClientErrors.INVALID_PARAMS):
            errorLog(f'{self._identifier}: Invalid parameters')
            return PLCComunicationResult.INVALID_PARAMS
        errorLog(f'{self._identifier}: Unable to read')
        return PLCComunicationResult.UNESPECIFY_ERROR


@dataclass
class PLCInputs(PLCMemoryArea):
    def setVarsFromDict(self, fromDict: dict) -> None:
        if not isinstance(fromDict, ConfigDict):
            fromDict = ConfigDict(self.validateDict(fromDict))
        try:
            for name, value in fromDict.items():
                if name.upper() == 'SIZE':
                    self.size = value
                if isinstance(value, dict):
                    self.variables[name] = PLCVar(name= name,
                                                  fromDict= value,
                                                  parent= self)
        except AttributeError:
            msg: str = f'{self._identifier}: "Inputs" not found'
            warningLog(msg)

    def readArea(self, client: Client= None) -> int:
        if client is None:
            client = self.parent.client
        try:
            buffer: bytearray = client.eb_read(0, self.size)
        except RuntimeError as e:
            return self.manageRuntimeError(e)
        [var.fromMemoryArea(buffer) for var in self.variables.values()]
        debugLog(f'{self._identifier}: Readed')
        return PLCComunicationResult.SUCCESS

    def _readVar(self, var: PLCVar, client: Client= None) -> Optional[bytearray]:
        if client is None:
            client = self.parent.client
        return client.eb_read(var.offset.bytesOffset, var.bytesSize)

    def _writeVar(self, var: PLCVar, client: Client= None) -> bool:
        if client is None:
            client = self.parent.client
        if var.rw in (PLCReadWrite.READWRITE):
            try:
                value: Optional[bytearray] = var.getBytearray()
            except TypeError as e:
                errorLog(f"{self._identifier}: Can't write {var}. {e}")
                return False
            if value is not None:
                client.eb_write(var.offset.bytesOffset, var.bytesSize, value)
                return True
        errorLog(f"{self._identifier}: Can't write {var}")


@dataclass
class PLCOutputs(PLCMemoryArea):
    def setVarsFromDict(self, fromDict: ConfigDict) -> None:
        if not isinstance(fromDict, ConfigDict):
            fromDict = ConfigDict(self.validateDict(fromDict))
        try:
            for name, value in fromDict.items():
                if name.upper() == 'SIZE':
                    self.size = value
                if isinstance(value, dict):
                    self.variables[name] = PLCVar(name= name,
                                                  fromDict= value,
                                                  parent= self)
        except AttributeError:
            msg: str = f'{self._identifier}: "Outputs" not found'
            warningLog(msg)

    def readArea(self, client: Client= None) -> int:
        if client is None:
            client = self.parent.client
        try:
            buffer: bytearray = client.ab_read(0, self.size)
        except RuntimeError as e:
            return self.manageRuntimeError(e)
        [var.fromMemoryArea(buffer) for var in self.variables.values()]
        debugLog(f'{self._identifier}: Readed')
        return PLCComunicationResult.SUCCESS

    def _readVar(self, var: PLCVar, client: Client= None) -> Optional[bytearray]:
        if client is None:
            client = self.parent.client
        return client.ab_read(var.offset.bytesOffset, var.bytesSize)

    def _writeVar(self, var: PLCVar, client: Client= None) -> None:
        if client is None:
            client = self.parent.client
        if var.rw in (PLCReadWrite.READWRITE):
            try:
                value: Optional[bytearray] = var.getBytearray()
            except TypeError as e:
                errorLog(f"{self._identifier}: Can't write {var}. {e}")
                return False
            if value is not None:
                client.ab_write(var.offset.bytesOffset, var.bytesSize, value)
                return True
        errorLog(f"{self._identifier}: Can't write {var}")


@dataclass
class PLCMarkers(PLCMemoryArea):
    def setVarsFromDict(self, fromDict: ConfigDict) -> None:
        if not isinstance(fromDict, ConfigDict):
            fromDict = ConfigDict(self.validateDict(fromDict))
        try:
            for name, value in fromDict.items():
                if name.upper() == 'SIZE':
                    self.size = value
                if isinstance(value, dict):
                    self.variables[name] = PLCVar(name= name,
                                                  fromDict= value,
                                                  parent= self)
        except AttributeError:
            msg: str = f'{self._identifier}: "Markers" not found in config file'
            warningLog(msg)

    def readArea(self, client: Client= None) -> int:
        if client is None:
            client = self.parent.client
        try:
            buffer: bytearray = client.mb_read(0, self.size)
        except RuntimeError as e:
            return self.manageRuntimeError(e)
        [var.fromMemoryArea(buffer) for var in self.variables.values()]
        debugLog(f'{self._identifier}: Readed')
        return PLCComunicationResult.SUCCESS

    def _readVar(self, var: PLCVar, client: Client= None) -> Optional[bytearray]:
        if client is None:
            client = self.parent.client
        return client.mb_read(var.offset.bytesOffset, var.bytesSize)

    def _writeVar(self, var: PLCVar, client: Client= None) -> None:
        if client is None:
            client = self.parent.client
        if var.rw in (PLCReadWrite.READWRITE):
            try:
                value: Optional[bytearray] = var.getBytearray()
            except TypeError as e:
                errorLog(f"{self._identifier}: Can't write {var}. {e}")
                return False
            if value is not None:
                client.mb_write(var.offset.bytesOffset, var.bytesSize, value)
                return True
        errorLog(f"{self._identifier}: Can't write {var}")


@dataclass
class PLCDB(PLCMemoryArea):
    number: int = 0

    @property
    def _identifier(self) -> str:
        if self.parent is None:
            return f'{self.__class__.__name__}'
        return f'{self.__class__.__name__}({self.parent.name}.DB{self.number})'

    def validate_number(self, value: Any) -> int:
        try:
            return self.validatePositiveInt(value)
        except TypeError:
            msg: str = f'Invalid type for {self._identifier}.number: {value}'
            errorLog(msg)
            raise TypeError(msg)

    def setVarsFromDict(self, fromDict: ConfigDict) -> None:
        if not isinstance(fromDict, ConfigDict):
            fromDict = ConfigDict(self.validateDict(fromDict))
        try:
            for name, value in fromDict.items():
                if name.upper() == 'SIZE':
                    self.size = value
                if name.upper() == 'NUMBER':
                    self.number = value
                if isinstance(value, dict):
                    self.variables[name] = PLCVar(name= name,
                                                  fromDict= value,
                                                  parent= self)
        except AttributeError:
            msg: str = f"{self._identifier}: DB's not found in config file"
            warningLog(msg)

    def readArea(self, client: Client= None) -> None:
        if client is None:
            client = self.parent.client
        try:
            buffer: bytearray = client.db_read(self.number, 0, self.size)
        except RuntimeError as e:
            return self.manageRuntimeError(e)
        [var.fromMemoryArea(buffer) for var in self.variables.values()]
        debugLog(f'{self._identifier}: Readed')
        return PLCComunicationResult.SUCCESS

    def _readVar(self, var: PLCVar, client: Client= None) -> Optional[bytearray]:
        if client is None:
            client = self.parent.client
        return client.db_read(self.number, var.offset.bytesOffset, var.bytesSize)

    def _writeVar(self, var: PLCVar, client: Client= None) -> None:
        if client is None:
            client = self.parent.client
        if var.rw in (PLCReadWrite.READWRITE):
            try:
                value: Optional[bytearray] = var.getBytearray()
            except TypeError as e:
                errorLog(f"{self._identifier}: Can't write {var}. {e}")
                return False
            if value is not None:
                client.db_write(self.number, var.offset.bytesOffset, value)
                return True
        errorLog(f"{self._identifier}: Can't write {var}")
