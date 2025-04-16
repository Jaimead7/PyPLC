import re
import socket
from dataclasses import KW_ONLY, InitVar, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Optional

import requests
from snap7 import Client

from pyUtils import ConfigDict, ValidationClass, debugLog, errorLog, warningLog

from .plcMemoryAreas import (PLCDB, PLCComunicationResult, PLCInputs,
                             PLCMarkers, PLCOutputs)


@dataclass
class PLCManager(ValidationClass):
    name: Optional[str] = None
    ip: Optional[str] = None
    rack: Optional[int] = None
    slot: Optional[int] = None
    port: Optional[int] = None
    _: KW_ONLY
    fromDict: InitVar[Optional[dict]] = None

    def __post_init__(self, fromDict: Optional[dict]) -> None:
        if fromDict is not None:
            fromDict = ConfigDict(self.validateDict(fromDict))
            try:
                self.name = fromDict.Name
            except KeyError:
                warningLog(f'{self._identifier}: "Name" not found in dict')
            try:
                self.ip = fromDict.IP
            except KeyError:
                warningLog(f'{self._identifier}: "IP" not found in dict')
            try:
                self.rack = fromDict.Rack
            except KeyError:
                warningLog(f'{self._identifier}: "Rack" not found in dict')
            try:
                self.slot = fromDict.Slot
            except KeyError:
                warningLog(f'{self._identifier}: "Slot" not found in dict')
            try:
                self.port = fromDict.Port
            except KeyError:
                warningLog(f'{self._identifier}: "Port" not found in dict')
            try:
                inputs: ConfigDict = fromDict.Inputs
            except AttributeError:
                warningLog(f'{self._identifier}: "Inputs" not found in dict')
                inputs = None
            self.inputs = PLCInputs(fromDict= inputs, parent= self)
            try:
                outputs: ConfigDict = fromDict.Outputs
            except AttributeError:
                warningLog(f'{self._identifier}: "Outputs" not found in dict')
                outputs = None
            self.outputs = PLCOutputs(fromDict= outputs, parent= self)
            try:
                markers: ConfigDict = fromDict.Markers
            except AttributeError:
                warningLog(f'{self._identifier}: "Markers" not found in dict')
                markers = None
            self.markers = PLCMarkers(fromDict= markers, parent= self)
            self.dbs: dict[int, PLCDB] = {}
            for key, value in fromDict.items():
                if re.compile('^DB[0-9]+$').match(key):
                    self.dbs[int(key[2:])] = PLCDB(number= key[2:],
                                                   fromDict= value,
                                                   parent= self)
            self.connect()
        debugLog(f'{self._identifier}: Created')

    @property
    def _identifier(self) -> str:
        return f'{self.__class__.__name__}({self.name})'

    def validate_name(self, value: Any) -> Optional[str]:
        try:
            value = ValidationClass.validateOptStr(value)
        except TypeError:
            msg: str = f'Invalid type {self._identifier}.name: {value}'
            errorLog(msg)
            raise TypeError(msg)
        return value

    def validate_ip(self, value: Any) -> Optional[str]:
        try:
            value = ValidationClass.validateOptStr(value)
            if value is not None:
                socket.inet_aton(value)
        except [socket.error, TypeError]:
            msg: str = f'Invalid type {self._identifier}.ip: {value}'
            errorLog(msg)
            raise TypeError(msg)
        return value

    def validate_rack(self, value: Any) -> Optional[int]:
        try:
            return ValidationClass.validateOptPositiveInt(value)
        except TypeError:
            msg: str = f'Invalid type {self._identifier}.rack: {value}'
            errorLog(msg)
            raise TypeError(msg)

    def validate_slot(self, value: Any) -> Optional[int]:
        try:
            return ValidationClass.validateOptPositiveInt(value)
        except TypeError:
            msg: str = f'Invalid type {self._identifier}.slot: {value}'
            errorLog(msg)
            raise TypeError(msg)

    def validate_port(self, value: Any) -> Optional[int]:
        try:
            return ValidationClass.validateOptPositiveInt(value)
        except TypeError:
            msg: str = f'Invalid type {self._identifier}.port: {value}'
            errorLog(msg)
            raise TypeError(msg)

    def validate_inputs(self, value: Any) -> PLCInputs:
        if not isinstance(value, PLCInputs):
            msg: str = f'Invalid type {self._identifier}.inputs: {value}'
            errorLog(msg)
            raise TypeError(msg)
        return value

    def validate_outputs(self, value: Any) -> PLCOutputs:
        if not isinstance(value, PLCOutputs):
            msg: str = f'Invalid type {self._identifier}.outputs: {value}'
            errorLog(msg)
            raise TypeError(msg)
        return value

    def validate_markers(self, value: Any) -> PLCMarkers:
        if not isinstance(value, PLCMarkers):
            msg: str = f'Invalid type {self._identifier}.markers: {value}'
            errorLog(msg)
            raise TypeError(msg)
        return value

    def validate_dbs(self, value: Any) -> dict[int, PLCDB]:
        try:
            value = ValidationClass.validateDict(value, ((int), (PLCDB)))
        except TypeError:
            msg: str = f'Invalid type {self._identifier}.dbs: {value}'
            errorLog(msg)
            raise TypeError(msg)
        return value

    def connect(self) -> None:
        self.client: Client = Client()
        try:
            self.client.connect(self.ip,
                                self.rack,
                                self.slot,
                                self.port)
            debugLog(f'{self._identifier}: PLC connected')
        except RuntimeError:
            errorLog(f'{self._identifier}: Connection failed')

    def disconnect(self) -> None:
        self.client.disconnect()
        debugLog(f'{self._identifier}: PLC disconnected')

    def isConnected(self) -> bool:
        return self.client.get_connected()

    def readData(self) -> None:
        self.readInputs()
        self.readOutputs()
        self.readMarkers()
        self.readDB()
        debugLog(f'{self._identifier}: Data readed')

    def readInputs(self) -> None:
        if not self.isConnected():
            return
        result: int = self.inputs.readArea(self.client)
        if result == PLCComunicationResult.NOT_CONNECTED:
            self.disconnect()

    def readOutputs(self) -> None:
        if not self.isConnected():
            return
        result: int = self.outputs.readArea(self.client)
        if result == PLCComunicationResult.NOT_CONNECTED:
            self.disconnect()

    def readMarkers(self) -> None:
        if not self.isConnected():
            return
        result: int = self.markers.readArea(self.client)
        if result == PLCComunicationResult.NOT_CONNECTED:
            self.disconnect()

    def readDB(self, dbs: Optional[Iterable | PLCDB] = None) -> None:
        if not self.isConnected():
            return
        if dbs is None:
            dbs = self.dbs
        if isinstance(dbs, PLCDB):
            dbs = {dbs.number: dbs}
        results: list = [db.readArea(self.client) for db in dbs.values()]
        if PLCComunicationResult.NOT_CONNECTED in results:
            self.disconnect()

    def downloadDatalog(self,
                        datalogName: str,
                        filePath: Path= Path.home() / 'Downloads') -> None:
        try:
            response: requests.Response = requests.get(f'http://{self.ip}/DataLog.html?&FileName={datalogName}.csv',
                                                       verify= False)
            if not response.content == '':
                date: str = str(datetime.now(timezone.utc).date()).replace('-','')
                with open(filePath / f'{date}-{datalogName}.csv', 'wb') as file:
                    file.write(response.content)
                    debugLog(f'{self._identifier}: Readed DataLog "{datalogName}"')
        except requests.exceptions.ConnectionError:
            errorLog(f"{self._identifier}: Can't download DataLog")
