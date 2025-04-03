from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import KW_ONLY, InitVar, dataclass, field
from typing import TYPE_CHECKING, Any, Optional

from snap7.client import Client

from pyUtils import ConfigDict, ValidationClass, debugLog, errorLog, warningLog

if TYPE_CHECKING:
    from .plcManager import PLCManager

from .plcVar import PLCReadWrite, PLCVar


class PLCVarDict(dict):
    def __init__(self, *args, **kwargs) -> None:
        self.update(*args, **kwargs)

    def __setitem__(self, key, value) -> None:
        if not isinstance(value, PLCVar):
            raise TypeError(f'{self.__class__.__name__}: {value} is not type PLCVar')
        key: str = ValidationClass.validateStr(key)
        return super().__setitem__(key, value)

    def update(self, *args, **kwargs) -> None:
        for key, value in dict(*args, **kwargs).items():
            self[key] = value


@dataclass
class PLCMemoryArea(ValidationClass, ABC):
    variables: PLCVarDict = field(default_factory= PLCVarDict)
    size: int = 0
    parent: Optional[PLCManager] = None
    _: KW_ONLY
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

    @abstractmethod
    def setVarsFromDict(self, fromDict: ConfigDict):
        ...

    @abstractmethod
    def readArea(self, client: Client) -> None:
        ...

    @abstractmethod
    def _readVar(self, var: PLCVar, client: Client) -> Optional[bytearray]:
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

    def readVarFromPLC(self, var: PLCVar | str, client: Client) -> Optional[Any]:
        try:
            if isinstance(var, str):
                var = self.variables[var]
            self.variables[var.name].value = self._readVar(var, client)
            debugLog(f'{self._identifier}: {self.variables[var.name]} readed')
            return self.variables[var.name].value
        except KeyError:
            msg: str = f'{self._identifier}: {var} not found in variables'
            errorLog(msg)
            raise KeyError(msg)

    def writeArea(self, client: Client) -> None:
        [self._writeVar(var, client) for var in self.variables]
        debugLog(f'{self._identifier}: Writed')

    @abstractmethod
    def _writeVar(self, var: PLCVar, client: Client) -> bool:
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

    def writeVarToPLC(self, var: PLCVar | str, value: Any, client: Client) -> None:
        #TODO: manage exceptions
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
                    self.variables[name] = PLCVar(name= name, fromDict= value)
        except AttributeError:
            msg: str = f'{self._identifier}: "Inputs" not found'
            warningLog(msg)

    def readArea(self, client: Client) -> None:
        buffer: bytearray = client.eb_read(0, self.size)
        [var.fromMemoryArea(buffer) for var in self.variables]
        debugLog(f'{self._identifier}: Readed')

    def _readVar(self, var: PLCVar, client: Client) -> Optional[bytearray]:
        try:
            return client.eb_read(var.offset.bytesOffset, var.bytesSize)
        except RuntimeError:
            msg: str = f"{self._identifier}: Can't connect to PLC"
            errorLog(msg)
            raise RuntimeError(msg)

    def _writeVar(self, var: PLCVar, client: Client) -> bool:
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
                    self.variables[name] = PLCVar(name= name, fromDict= value)
        except AttributeError:
            msg: str = f'{self._identifier}: "Outputs" not found'
            warningLog(msg)

    def readArea(self, client: Client) -> None:
        buffer: bytearray = client.ab_read(0, self.size)
        [var.fromMemoryArea(buffer) for var in self.variables]
        debugLog(f'{self._identifier}: Readed')

    def _readVar(self, var: PLCVar, client: Client) -> Optional[bytearray]:
        try:
            return client.ab_read(var.offset.bytesOffset, var.bytesSize)
        except RuntimeError:
            msg: str = f"{self._identifier}: Can't connect to PLC"
            errorLog(msg)
            raise RuntimeError(msg)

    def _writeVar(self, var: PLCVar, client: Client) -> None:
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
                    self.variables[name] = PLCVar(name= name, fromDict= value)
        except AttributeError:
            msg: str = f'{self._identifier}: "Markers" not found in config file'
            warningLog(msg)

    def readArea(self, client: Client) -> None:
        buffer: bytearray = client.mb_read(0, self.size)
        [var.fromMemoryArea(buffer) for var in self.variables]
        debugLog(f'{self._identifier}: Readed')

    def _readVar(self, var: PLCVar, client: Client) -> Optional[bytearray]:
        try:
            return client.mb_read(var.offset.bytesOffset, var.bytesSize)
        except RuntimeError:
            msg: str = f"{self._identifier}: Can't connect to PLC"
            errorLog(msg)
            raise RuntimeError(msg)

    def _writeVar(self, var: PLCVar, client: Client) -> None:
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
        return f'{self.__class__.__name__}({self.parent.name}.{self.number})'

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
                    self.variables[name] = PLCVar(name= name, fromDict= value)
        except AttributeError:
            msg: str = f"{self._identifier}: DB's not found in config file"
            warningLog(msg)

    def readArea(self, client: Client) -> None:
        buffer: bytearray = client.db_get(self.number)
        [var.fromMemoryArea(buffer) for var in self.variables]
        debugLog(f'{self._identifier}: Readed')

    def _readVar(self, var: PLCVar, client: Client) -> Optional[bytearray]:
        try:
            return client.db_read(self.number, var.offset.bytesOffset, var.bytesSize)
        except RuntimeError:
            msg: str = f"{self._identifier}: Can't connect to PLC"
            errorLog(msg)
            raise RuntimeError(msg)

    def _writeVar(self, var: PLCVar, client: Client) -> None:
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
