import re
import socket
from dataclasses import KW_ONLY, InitVar, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import requests
from snap7 import Client

from pyUtils import ConfigDict, ValidationClass, errorLog, warningLog

from .plcMemoryAreas import PLCDB, PLCInputs, PLCMarkers, PLCOutputs


@dataclass
class PLCManager(ValidationClass):
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
                self.ip = fromDict.IP
            except KeyError:
                warningLog(f'{self.__class__.__name__}: "IP" not found in dict')
            try:
                self.rack = fromDict.Rack
            except KeyError:
                warningLog(f'{self.__class__.__name__}: "Rack" not found in dict')
            try:
                self.slot = fromDict.Slot
            except KeyError:
                warningLog(f'{self.__class__.__name__}: "Slot" not found in dict')
            try:
                self.port = fromDict.Port
            except KeyError:
                warningLog(f'{self.__class__.__name__}: "Port" not found in dict')
            try:
                inputs: ConfigDict = fromDict.Inputs
            except AttributeError:
                warningLog(f'{self.__class__.__name__}: "Inputs" not found in dict')
                inputs = None
            self.inputs = PLCInputs(fromDict= inputs)
            try:
                outputs: ConfigDict = fromDict.Outputs
            except AttributeError:
                warningLog(f'{self.__class__.__name__}: "Outputs" not found in dict')
                outputs = None
            self.outputs = PLCOutputs(fromDict= outputs)
            try:
                markers: ConfigDict = fromDict.Markers
            except AttributeError:
                warningLog(f'{self.__class__.__name__}: "Markers" not found in dict')
                markers = None
            self.markers = PLCMarkers(fromDict= markers)
            self.dbs: list[PLCDB] = []
            for key, value in fromDict.items():
                if re.compile('^DB[0-9]+$').match(key):
                    self.dbs.append(PLCDB(number= key[2:], fromDict= value))
            self.client: Client = Client()
            self.connect()

    def validate_ip(self, value: Any) -> Optional[str]:
        try:
            value = ValidationClass.validateOptStr(value)
            if value is not None:
                socket.inet_aton(value)
        except [socket.error, TypeError]:
            msg: str = f'Invalid type {self.__class__.__name__}.ip: {value}'
            errorLog(msg)
            raise TypeError(msg)
        return value

    def validate_rack(self, value: Any) -> Optional[int]:
        try:
            return ValidationClass.validateOptPositiveInt(value)
        except TypeError:
            msg: str = f'Invalid type {self.__class__.__name__}.rack: {value}'
            errorLog(msg)
            raise TypeError(msg)

    def validate_slot(self, value: Any) -> Optional[int]:
        try:
            return ValidationClass.validateOptPositiveInt(value)
        except TypeError:
            msg: str = f'Invalid type {self.__class__.__name__}.slot: {value}'
            errorLog(msg)
            raise TypeError(msg)

    def validate_port(self, value: Any) -> Optional[int]:
        try:
            return ValidationClass.validateOptPositiveInt(value)
        except TypeError:
            msg: str = f'Invalid type {self.__class__.__name__}.port: {value}'
            errorLog(msg)
            raise TypeError(msg)

    def validate_inputs(self, value: Any) -> PLCInputs:
        if not isinstance(value, PLCInputs):
            msg: str = f'Invalid type {self.__class__.__name__}.inputs: {value}'
            errorLog(msg)
            raise TypeError(msg)
        return value

    def validate_outputs(self, value: Any) -> PLCOutputs:
        if not isinstance(value, PLCOutputs):
            msg: str = f'Invalid type {self.__class__.__name__}.outputs: {value}'
            errorLog(msg)
            raise TypeError(msg)
        return value

    def validate_markers(self, value: Any) -> PLCMarkers:
        if not isinstance(value, PLCMarkers):
            msg: str = f'Invalid type {self.__class__.__name__}.markers: {value}'
            errorLog(msg)
            raise TypeError(msg)
        return value

    def validate_dbs(self, value: Any) -> list[PLCDB]:
        try:
            value = ValidationClass.validateList(value, [PLCDB])
        except TypeError:
            msg: str = f'Invalid type {self.__class__.__name__}.dbs: {value}'
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
        except RuntimeError:
            warningLog(f'{self.__class__.__name__}: Connection failed')

    def disconnect(self) -> None:
        return self.client.disconnect()

    def isConnected(self) -> bool:
        return self.client.get_connected()

    def readData(self) -> None:
        self.inputs.readArea(self.client)
        self.outputs.readArea(self.client)
        self.markers.readArea(self.client)
        [db.readArea(self.client) for db in self.dbs]

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
        except requests.exceptions.ConnectionError:
            errorLog(f"Can't download DataLog from {self.ip}")
