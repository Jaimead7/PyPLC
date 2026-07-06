import re
from collections.abc import Iterable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import httpx
from pydantic import BaseModel, Field, field_validator
from snap7 import Client
from typing_extensions import Self

from .file_readers import FileReader, FileReaderReg
from .logs import Styles, pyplc_logger
from .memory_areas import PLCDB, PLCInputs, PLCMarks, PLCMemoryArea, PLCOutputs
from .structures import PLCComResult, PLCConnType
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
    @classmethod
    def validate_ip(cls, value: str) -> str:
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
    def memory_areas(self) -> Iterable[PLCMemoryArea]:
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
        reader: Optional[FileReader] = None
    ) -> Self:
        if reader is None:
            reader = FileReaderReg.from_file(file_path)
        data: dict[str, Any] = reader(file_path)
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

    def connect(self, conn_type: PLCConnType = PLCConnType.OP) -> PLCComResult:
        self._client: Client = Client()
        self._client.set_connection_type(conn_type)
        try:
            self._client.connect(
                address= self.ip,
                rack= self.rack,
                slot= self.slot,
                tcp_port= self.port
            )
            pyplc_logger.debug(f'{self}: PLC connected.', Styles.SUCCEED)
            return PLCComResult.SUCCESS
        except Exception as e:
            pyplc_logger.error(f'{self}: Connection failed. {e}')
            return PLCComResult.NOT_CONNECTED

    def disconnect(self) -> PLCComResult:
        try:
            self._client.disconnect()
            pyplc_logger.debug(f'{self}: PLC disconnected.')
            return PLCComResult.SUCCESS
        except Exception as e:
            pyplc_logger.error(f'{self}: Disconnection failed. {e}.')
            return PLCComResult.UNESPECIFY_ERROR

    def is_connected(self) -> bool:
        try:
            return self._client.get_connected()
        except Exception:
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
        result: PLCComResult = self.inputs.read_area(self._client)
        if result == PLCComResult.NOT_CONNECTED:
            self.disconnect()
        return result

    def read_outputs(self) -> PLCComResult:
        if not self.is_connected():
            if not self.connect().is_error():
                return PLCComResult.NOT_CONNECTED
        if self.outputs is None:
            return PLCComResult.NO_ACTION
        result: PLCComResult = self.outputs.read_area(self._client)
        if result == PLCComResult.NOT_CONNECTED:
            self.disconnect()
        return result

    def read_markers(self) -> PLCComResult:
        if not self.is_connected():
            if not self.connect().is_error():
                return PLCComResult.NOT_CONNECTED
        if self.marks is None:
            return PLCComResult.NO_ACTION
        result: PLCComResult = self.marks.read_area(self._client)
        if result == PLCComResult.NOT_CONNECTED:
            self.disconnect()
        return result

    def read_dbs(self, dbs: Optional[Iterable[int | PLCDB]] = None) -> PLCComResult:
        if not self.is_connected():
            if not self.connect().is_error():
                return PLCComResult.NOT_CONNECTED
        if dbs is None:
            dbs = tuple(self.dbs.keys())
        results: list[PLCComResult] = []
        results = [
            db.read_area(self._client)
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
        area: Any = None
    ) -> tuple[PLCComResult, Any]:
        if not self.is_connected():
            if not self.connect().is_error():
                return (PLCComResult.NOT_CONNECTED, None)
        for plc_area in self.memory_areas:
            if area is not None and plc_area != area:
                continue
            ret: PLCComResult
            value: Any
            ret, value = plc_area.read_var(var, self._client)
            if ret == PLCComResult.NOT_CONNECTED:
                self.disconnect()
                return (ret, None)
            if ret == PLCComResult.SUCCESS:
                return (ret, value)
        return (PLCComResult.INVALID_PARAMS, None)

    def get_var(
        self,
        var: PLCVar | str,
        area: Any = None
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
        result: PLCComResult = self.inputs.write_area(self._client)
        if result == PLCComResult.NOT_CONNECTED:
            self.disconnect()
        return result

    def write_outputs(self) -> PLCComResult:
        if not self.is_connected():
            if not self.connect().is_error():
                return PLCComResult.NOT_CONNECTED
        if self.outputs is None:
            return PLCComResult.NO_ACTION
        result: PLCComResult = self.outputs.write_area(self._client)
        if result == PLCComResult.NOT_CONNECTED:
            self.disconnect()
        return result

    def write_marks(self) -> PLCComResult:
        if not self.is_connected():
            if not self.connect().is_error():
                return PLCComResult.NOT_CONNECTED
        if self.marks is None:
            return PLCComResult.NO_ACTION
        result: PLCComResult = self.marks.write_area(self._client)
        if result == PLCComResult.NOT_CONNECTED:
            self.disconnect()
        return result

    def write_db(self, dbs: Optional[Iterable[int | PLCDB]] = None) -> PLCComResult:
        if not self.is_connected():
            if not self.connect().is_error():
                return PLCComResult.NOT_CONNECTED
        if dbs is None:
            dbs = tuple(self.dbs.keys())
        results: list[PLCComResult] = []
        results = [
            db.write_area(self._client)
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
        area: Any = None
    ) -> tuple[PLCComResult, Any]:
        if not self.is_connected():
            if not self.connect().is_error():
                return (PLCComResult.NOT_CONNECTED, None)
        for plc_area in self.memory_areas:
            if area is not None and plc_area != area:
                continue
            ret: PLCComResult
            ret, res_value = plc_area.write_var(
                var= var,
                value= value,
                client= self._client
            )
            if ret == PLCComResult.NOT_CONNECTED:
                self.disconnect()
                return (ret, None)
            if ret == PLCComResult.SUCCESS:
                return (ret, res_value)
        return (PLCComResult.INVALID_PARAMS, None)

    def set_var(
        self,
        var: PLCVar | str,
        value: Any,
        area: Any = None
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
        timeout: httpx.Timeout = httpx.Timeout(10., connect= 5.)
        with httpx.Client(timeout= timeout) as client:
            try:
                response: httpx.Response = client.get(
                    f'http://{self.ip}/DataLog.html?&FileName={datalog_name}.csv'
                )
                response.raise_for_status()
                if response.content == '':
                    raise ValueError
                date: str = str(datetime.now(timezone.utc).date()).replace('-','')
                with open(filePath / f'{date}-{datalog_name}.csv', 'wb') as file:
                    file.write(response.content)
                pyplc_logger.debug(f'{self}: Readed DataLog({datalog_name}).')
                return PLCComResult.SUCCESS
            except httpx.HTTPStatusError as e:
                pyplc_logger.error(f'{self}: Can\'t download DataLog({datalog_name}). [{e.response.status_code}] {e.response.text}')
                return PLCComResult.NOT_CONNECTED
            except httpx.TimeoutException:
                pyplc_logger.error(f'{self}: Can\'t download DataLog({datalog_name}). Timeout error.')
                return PLCComResult.NOT_CONNECTED
            except httpx.RequestError:
                pyplc_logger.error(f'{self}: Can\'t download DataLog({datalog_name}). Connexion error.')
                return PLCComResult.NOT_CONNECTED
            except ValueError:
                msg: str = f'{self}: Empty response from PLC.'
                pyplc_logger.error(msg)
                return PLCComResult.UNESPECIFY_ERROR
