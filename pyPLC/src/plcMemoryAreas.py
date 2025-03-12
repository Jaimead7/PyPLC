import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional

from pyUtils import ConfigFileManager, ValidationClass, errorLog, warningLog
from snap7.client import Client

from .plcVar import PLCReadWrite, PLCVar


class PLCVarDict(dict):
    def __init__(self, *args, **kwargs) -> None:
        self.update(*args, **kwargs)

    def __setitem__(self, key, value) -> None:
        if not isinstance(value, PLCVar):
            raise TypeError(f'{value} is not type PLCVar')
        key: str = ValidationClass.validateStr(key)
        return super().__setitem__(key, value)

    def update(self, *args, **kwargs) -> None:
        for key, value in dict(*args, **kwargs).items():
            self[key] = value


@dataclass
class PLCMemoryArea(ValidationClass, ABC):
    variables: PLCVarDict = field(default_factory= PLCVarDict)
    size: int = 0

    def validate_variables(self, value: Any) -> list[PLCVar]:
        try:
            return PLCVarDict(value)
        except TypeError:
            msg: str = f'Invalid type for {self.__class__.__name__}.variables: {value}'
            errorLog(msg)
            raise TypeError(msg)

    def validate_size(self, value: Any) -> int:
        try:
            return self.validatePositiveInt(value)
        except TypeError:
            msg: str = f'Invalid type for {self.__class__.__name__}.size: {value}'
            errorLog(msg)
            raise TypeError(msg)

    @abstractmethod
    def setVarsFromConfigFile(self, cfg: ConfigFileManager, plcName= 'mainPLC'):
        ...

    @abstractmethod
    def readArea(self, client: Client) -> None:
        ...

    @abstractmethod
    def _readValue(self, var: PLCVar | str, client: Client) -> Optional[bytearray]:
        ...

    def getVar(self, var: PLCVar | str) -> Any:
        try:
            return self.variables[var].value
        except KeyError:
            msg: str = f'{var} not found in {self} variables'
            errorLog(msg)
            raise KeyError(msg)

    def readVarFromPLC(self, var: PLCVar | str, client: Client) -> Optional[Any]:
        try:
            self.variables[var].value = self._readValue(var, client)
            return self.variables[var].value
        except KeyError:
            msg: str = f'{var} not found in {self} variables'
            errorLog(msg)
            raise KeyError(msg)

    def writeArea(self, client: Client):
        [self._writeVar(var, client) for var in self.variables]

    @abstractmethod
    def _writeVar(self, var: PLCVar | str, client: Client) -> None:
        ...

    def setVar(self, var: PLCVar | str, value: Any) -> None:
        try:
            self.variables[var].value = value
        except KeyError:
            msg: str = f'{var} not found in {self} variables'
            errorLog(msg)
            raise KeyError(msg)

    def writeVarToPLC(self, var: PLCVar | str, value: Any, client: Client):
        #TODO: manage exceptions
        try:
            self.variables[var].value = value
            self._writeVar(self.variables[var], client)
        except KeyError:
            msg: str = f'{var} not found in {self} variables'
            errorLog(msg)
            raise KeyError(msg)


@dataclass
class PLCInputs(PLCMemoryArea):
    def setVarsFromConfigFile(self, cfg: ConfigFileManager, plcName= 'mainPLC') -> None:
        try:
            for name, attr in cfg.plc.__getattr__(plcName).Inputs.items():
                if name.upper() == 'SIZE':
                    self.size = attr
                if isinstance(attr, dict):
                    self.variables[attr[name]] = PLCVar(name= name, fromDict= attr)
        except AttributeError:
            msg: str = f'plc.{plcName}.Inputs not found in config file'
            warningLog(msg)

    def readArea(self, client: Client) -> None:
        buffer: bytearray = client.eb_read(0, self.size)
        [var.fromMemoryArea(buffer) for var in self.variables]

    def _readValue(self, var: PLCVar | str, client: Client) -> Optional[bytearray]:
        try:
            return client.eb_read(var.offset.bytesOffset, var.bytesSize)
        except RuntimeError:
            msg: str = f"Can't connect to PLC"
            errorLog(msg)
            raise RuntimeError(msg)

    def _writeVar(self, var: PLCVar | str, client: Client) -> None:
        if var.rw in (PLCReadWrite.READWRITE):
            value: Optional[bytearray] = var.getBytearray()
            if value is not None:
                client.eb_write(var.offset.bytesOffset, var.bytesSize, value)
                return
        warningLog(f"Can't write {PLCVar} to PLC inputs")


@dataclass
class PLCOutputs(PLCMemoryArea):
    def setVarsFromConfigFile(self, cfg: ConfigFileManager, plcName= 'mainPLC') -> None:
        try:
            for name, attr in cfg.plc.__getattr__(plcName).Outputs.items():
                if name.upper() == 'SIZE':
                    self.size = attr
                if isinstance(attr, dict):
                    self.variables[attr[name]] = PLCVar(name= name, fromDict= attr)
        except AttributeError:
            msg: str = f'plc.{plcName}.Outputs not found in config file'
            warningLog(msg)

    def readArea(self, client: Client) -> None:
        buffer: bytearray = client.ab_read(0, self.size)
        [var.fromMemoryArea(buffer) for var in self.variables]

    def _readValue(self, var: PLCVar | str, client: Client) -> Optional[bytearray]:
        try:
            return client.ab_read(var.offset.bytesOffset, var.bytesSize)
        except RuntimeError:
            msg: str = f"Can't connect to PLC"
            errorLog(msg)
            raise RuntimeError(msg)

    def _writeVar(self, var: PLCVar | str, client: Client) -> None:
        if var.rw in (PLCReadWrite.READWRITE):
            value: Optional[bytearray] = var.getBytearray()
            if value is not None:
                client.ab_write(var.offset.bytesOffset, value)
                return
        warningLog(f"Can't write {PLCVar} to PLC outputs")


@dataclass
class PLCMarkers(PLCMemoryArea):
    def setVarsFromConfigFile(self, cfg: ConfigFileManager, plcName= 'mainPLC') -> None:
        try:
            for name, attr in cfg.plc.__getattr__(plcName).Markers.items():
                if name.upper() == 'SIZE':
                    self.size = attr
                if isinstance(attr, dict):
                    self.variables[attr[name]] = PLCVar(name= name, fromDict= attr)
        except AttributeError:
            msg: str = f'plc.{plcName}.Markers not found in config file'
            warningLog(msg)

    def readArea(self, client: Client) -> None:
        buffer: bytearray = client.mb_read(0, self.size)
        [var.fromMemoryArea(buffer) for var in self.variables]

    def _readValue(self, var: PLCVar | str, client: Client) -> Optional[bytearray]:
        try:
            return client.mb_read(var.offset.bytesOffset, var.bytesSize)
        except RuntimeError:
            msg: str = f"Can't connect to PLC"
            errorLog(msg)
            raise RuntimeError(msg)

    def _writeVar(self, var: PLCVar | str, client: Client) -> None:
        if var.rw in (PLCReadWrite.READWRITE):
            value: Optional[bytearray] = var.getBytearray()
            if value is not None:
                client.mb_write(var.offset.bytesOffset, var.bytesSize, value)
                return
        warningLog(f"Can't write {PLCVar} to PLC markers")


@dataclass
class PLCDB(PLCMemoryArea):
    number: int

    def setVarsFromConfigFile(self, cfg: ConfigFileManager, plcName= 'mainPLC') -> None:
        try:
            for key, value in cfg.plc.__getattr__(plcName).items():
                if not re.compile('DB[0-9]+$').match(key):
                    raise AttributeError
                if self.number != int(key[2:]):
                    raise AttributeError
                for name, attr in value.items():
                    if name.upper() == 'SIZE':
                        self.size = attr
                    if isinstance(attr, dict):
                        self.variables[attr[name]] = PLCVar(name= name, fromDict= attr)
        except AttributeError:
            msg: str = f'plc.{plcName}.DB not found in config file'
            warningLog(msg)

    def readArea(self, client: Client) -> None:
        buffer: bytearray = client.db_get(self.number)
        [var.fromMemoryArea(buffer) for var in self.variables]

    def _readValue(self, var: PLCVar | str, client: Client) -> Optional[bytearray]:
        try:
            return client.db_read(self.number, var.offset.bytesOffset, var.bytesSize)
        except RuntimeError:
            msg: str = f"Can't connect to PLC"
            errorLog(msg)
            raise RuntimeError(msg)

    def _writeVar(self, var: PLCVar | str, client: Client) -> None:
        if var.rw in (PLCReadWrite.READWRITE):
            value: Optional[bytearray] = var.getBytearray()
            if value is not None:
                client.db_write(self.number, var.offset.bytesOffset, value)
                return
        warningLog(f"Can't write {PLCVar} to PLC DB{self.number}")
