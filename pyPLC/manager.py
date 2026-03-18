import re
from collections.abc import Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import requests
from pydantic import BaseModel, Field, field_validator
from snap7 import Client
from typing_extensions import Self

from .file_readers import FileReader, yaml_reader
from .logs import Styles, pyplc_logger
from .memory_areas import PLCDB, PLCInputs, PLCMarks, PLCMemoryArea, PLCOutputs
from .structures import PLCComResult
from .vars import PLCVar


class PLCManager(BaseModel):
    name: str
    ip: str
    rack: int = Field(ge= 0)
    slot: int = Field(ge= 0)
    port: int = Field(ge= 0)
    inputs: Optional[PLCInputs] = None
    outputs: Optional[PLCOutputs] = None
    marks: Optional[PLCMarks] = None
    dbs: dict[int, PLCDB] = {}

    def __str__(self) -> str:
        return f'{self.__class__.__name__}({self.name})'

    @field_validator('ip')
    def validate_ip(self, value: str) -> str:
        try:
            ip_pattern = r'^(25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])(\.(25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])){3}$'
            if not re.match(ip_pattern, str(value)):
                raise ValueError
            return value
        except ValueError:
            msg: str = f'Invalid value for ip: {value}.'
            pyplc_logger.error(msg)
            raise ValueError(msg)

    @property
    def memory_areas(self) -> Sequence[PLCMemoryArea]:
        return tuple(
            x
            for x in (self.inputs, self.outputs, self.marks, *self.dbs.values())
            if x
        )

    @classmethod
    def from_file(
        cls,
        name: str,
        file_path: Path,
        reader: FileReader = yaml_reader
    ) -> Self:
        try:
            data: dict[str, Any] = reader(file_path)
        except (FileNotFoundError, ImportError, RuntimeError):
            raise
        for key, value in data.items():
            if key.upper() != 'PLC' or not isinstance(value, dict):
                continue
            for plc_name, plc_config in value.items():
                if plc_name != name or not isinstance(plc_config, dict):
                    continue
                return cls.from_dict(name= name, data= plc_config)
        msg: str = f'{file_path} doesn\'t have "plc.{name}" with a valid PLC config.'
        pyplc_logger.critical(msg)
        raise ValueError(msg)

    @classmethod
    def from_dict(cls, name: str, data: dict[str, Any]) -> Self:
        ip: Optional[str] = None
        rack: Optional[int] = None
        slot: Optional[int] = None
        port: Optional[int] = None
        inputs: Optional[PLCInputs] = None
        outputs: Optional[PLCOutputs] = None
        marks: Optional[PLCMarks] = None
        dbs: dict[int, PLCDB] = {}
        for key, value in data.items():
            match key.upper():
                case 'IP':
                    ip = value
                case 'RACK':
                    rack = value
                case 'SLOT':
                    slot = value
                case 'PORT':
                    port = value
                case 'INPUTS':
                    if not isinstance(value, dict):
                        raise ValueError
                    try:
                        inputs = PLCInputs.from_dict(data= value)
                    except ValueError:
                        msg: str = 'PLC.Inputs doesn\'t have a valid structure.'
                        pyplc_logger.error(msg)
                        pass
                case 'OUTPUTS':
                    if not isinstance(value, dict):
                        raise ValueError
                    try:
                        outputs = PLCOutputs.from_dict(data= value)
                    except ValueError:
                        msg: str = 'PLC.Outputs doesn\'t have a valid structure.'
                        pyplc_logger.error(msg)
                        pass
                case 'MARKS':
                    if not isinstance(value, dict):
                        raise ValueError
                    try:
                        marks = PLCMarks.from_dict(data= value)
                    except ValueError:
                        msg: str = 'PLC.Marks doesn\'t have a valid structure.'
                        pyplc_logger.error(msg)
                        pass
                case db_key if re.match('^DB[0-9]+$', db_key):
                    if not isinstance(value, dict):
                        raise ValueError
                    try:
                        new_db: PLCDB = PLCDB.from_dict(data= value)
                        dbs[new_db.number] = new_db
                    except ValueError:
                        msg: str = f'PLC.{key} doesn\'t have a valid structure.'
                        pyplc_logger.error(msg)
                        pass
        if None in (ip, rack, slot, port):
            msg: str = 'Data doesn\'t have a valid PLC config.'
            pyplc_logger.critical(msg)
            raise ValueError(msg)
        return cls(
            name= name,
            ip= ip,  # type: ignore
            rack= rack,  # type: ignore
            slot= slot,  # type: ignore
            port= port,  # type: ignore
            inputs= inputs,
            outputs= outputs,
            marks= marks,
            dbs= dbs
        )

    def connect(self) -> PLCComResult:
        self.client: Client = Client()
        try:
            self.client.connect(
                address= self.ip,
                rack= self.rack,
                slot= self.slot,
                tcp_port= self.port
            )
            pyplc_logger.debug(f'{self}: PLC connected.', Styles.SUCCEED)
            return PLCComResult.SUCCESS
        except RuntimeError:
            pyplc_logger.error(f'{self}: Connection failed.')
            return PLCComResult.NOT_CONNECTED

    def disconnect(self) -> PLCComResult:
        try:
            self.client.disconnect()
            pyplc_logger.debug(f'{self}: PLC disconnected.')
            return PLCComResult.SUCCESS
        except Exception as e:
            pyplc_logger.error(f'{self}: Disconnection failed. {e}.')
            return PLCComResult.UNESPECIFY_ERROR

    def is_connected(self) -> bool:
        try:
            return self.client.get_connected()
        except AttributeError:
            return False

    def read_data(self) -> None:
        self.read_inputs()
        self.read_outputs()
        self.read_markers()
        self.read_dbs()
        pyplc_logger.debug(f'{self}: Data readed.')

    def read_inputs(self) -> PLCComResult:
        if not self.is_connected():
            if not self.connect().is_error():
                return PLCComResult.NOT_CONNECTED
        if self.inputs is None:
            return PLCComResult.NO_ACTION
        result: PLCComResult = self.inputs.read_area(self.client)
        if result == PLCComResult.NOT_CONNECTED:
            self.disconnect()
        return result

    def read_outputs(self) -> PLCComResult:
        if not self.is_connected():
            if not self.connect().is_error():
                return PLCComResult.NOT_CONNECTED
        if self.outputs is None:
            return PLCComResult.NO_ACTION
        result: PLCComResult = self.outputs.read_area(self.client)
        if result == PLCComResult.NOT_CONNECTED:
            self.disconnect()
        return result

    def read_markers(self) -> PLCComResult:
        if not self.is_connected():
            if not self.connect().is_error():
                return PLCComResult.NOT_CONNECTED
        if self.marks is None:
            return PLCComResult.NO_ACTION
        result: PLCComResult = self.marks.read_area(self.client)
        if result == PLCComResult.NOT_CONNECTED:
            self.disconnect()
        return result

    def read_dbs(self, dbs: Optional[Sequence[int | PLCDB]] = None) -> PLCComResult:
        if not self.is_connected():
            if not self.connect().is_error():
                return PLCComResult.NOT_CONNECTED
        if dbs is None:
            dbs = tuple(self.dbs.keys())
        results: list[PLCComResult] = []
        results = [
            db.read_area(self.client)
            for db in self.dbs.values()
            if db in dbs
        ]
        if len(results) == 0:
            return PLCComResult.NO_ACTION
        if PLCComResult.NOT_CONNECTED in results:
            self.disconnect()
            return PLCComResult.NOT_CONNECTED
        return PLCComResult.SUCCESS

    def read_var(
        self,
        var: PLCVar | str,
        area: Optional[PLCMemoryArea] = None
    ) -> tuple[PLCComResult, Any]:
        if not self.is_connected():
            if not self.connect().is_error():
                return (PLCComResult.NOT_CONNECTED, None)
        for plc_area in self.memory_areas:
            if area is not None or plc_area != area:
                continue
            ret: PLCComResult
            value: Any
            ret, value = plc_area.read_var(var, self.client)
            if ret == PLCComResult.NOT_CONNECTED:
                self.disconnect()
                return (ret, None)
            if ret == PLCComResult.SUCCESS:
                return (ret, value)
        return (PLCComResult.INVALID_PARAMS, None)

    def get_var(
        self,
        var: PLCVar | str,
        area: Optional[PLCMemoryArea] = None
    ) -> Any:
        for plc_area in self.memory_areas:
            if area is None or plc_area == area:
                try:
                    return plc_area.get_var(var)
                except ValueError:
                    pass
        raise ValueError(f'{self}.{var} not found.')

    def write_inputs(self) -> PLCComResult:
        if not self.is_connected():
            if not self.connect().is_error():
                return PLCComResult.NOT_CONNECTED
        if self.inputs is None:
            return PLCComResult.NO_ACTION
        result: PLCComResult = self.inputs.write_area(self.client)
        if result == PLCComResult.NOT_CONNECTED:
            self.disconnect()
        return result

    def write_outputs(self) -> PLCComResult:
        if not self.is_connected():
            if not self.connect().is_error():
                return PLCComResult.NOT_CONNECTED
        if self.outputs is None:
            return PLCComResult.NO_ACTION
        result: PLCComResult = self.outputs.write_area(self.client)
        if result == PLCComResult.NOT_CONNECTED:
            self.disconnect()
        return result

    def write_marks(self) -> PLCComResult:
        if not self.is_connected():
            if not self.connect().is_error():
                return PLCComResult.NOT_CONNECTED
        if self.marks is None:
            return PLCComResult.NO_ACTION
        result: PLCComResult = self.marks.write_area(self.client)
        if result == PLCComResult.NOT_CONNECTED:
            self.disconnect()
        return result

    def write_db(self, dbs: Optional[Sequence[int | PLCDB]] = None) -> PLCComResult:
        if not self.is_connected():
            if not self.connect().is_error():
                return PLCComResult.NOT_CONNECTED
        if dbs is None:
            dbs = tuple(self.dbs.keys())
        results: list[PLCComResult] = []
        results = [
            db.write_area(self.client)
            for db in self.dbs.values()
            if db in dbs
        ]
        if len(results) == 0:
            return PLCComResult.NO_ACTION
        if PLCComResult.NOT_CONNECTED in results:
            self.disconnect()
            return PLCComResult.NOT_CONNECTED
        return PLCComResult.SUCCESS

    def write_var(
        self,
        var: PLCVar | str,
        value: Any,
        area: Optional[PLCMemoryArea] = None
    ) -> tuple[PLCComResult, Any]:
        if not self.is_connected():
            if not self.connect().is_error():
                return (PLCComResult.NOT_CONNECTED, None)
        for plc_area in self.memory_areas:
            if area is not None or plc_area != area:
                continue
            ret: PLCComResult
            ret, value = plc_area.write_var(
                var= var,
                value= value,
                client= self.client
            )
            if ret == PLCComResult.NOT_CONNECTED:
                self.disconnect()
                return (ret, None)
            if ret == PLCComResult.SUCCESS:
                return (ret, value)
        return (PLCComResult.INVALID_PARAMS, None)

    def set_var(
        self,
        var: PLCVar | str,
        value: Any,
        area: Optional[PLCMemoryArea] = None
    ) -> None:
        for plcArea in self.memory_areas:
            if area is None or plcArea == area:
                try:
                    plcArea.set_var(var, value)
                    return None
                except KeyError:
                    pass
        msg: str = f'{self}.{var} not found.'
        pyplc_logger.error(msg)
        raise KeyError(msg)

    def download_datalog(
        self,
        datalog_name: str,
        filePath: Path = Path.home() / 'Downloads'
    ) -> PLCComResult:
        try:
            response: requests.Response = requests.get(
                f'http://{self.ip}/DataLog.html?&FileName={datalog_name}.csv',
                verify= False
            )
            if response.content == '':
                raise ValueError
            date: str = str(datetime.now(timezone.utc).date()).replace('-','')
            with open(filePath / f'{date}-{datalog_name}.csv', 'wb') as file:
                file.write(response.content)
            pyplc_logger.debug(f'{self}: Readed DataLog({datalog_name}).')
            return PLCComResult.SUCCESS
        except requests.exceptions.ConnectionError:
            pyplc_logger.error(f'{self}: Can\'t download DataLog({datalog_name}).')
            return PLCComResult.NOT_CONNECTED
        except ValueError:
            msg: str = f'{self}:Empty response from PLC.'
            pyplc_logger.error(msg)
            return PLCComResult.UNESPECIFY_ERROR
