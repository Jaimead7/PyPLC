from abc import ABC, abstractmethod
from typing import Any, Optional

from pydantic import BaseModel, Field
from snap7.client import Client
from typing_extensions import Self

from .logs import Styles, pyplc_logger
from .structures import PLCClientErrors, PLCComResult
from .vars import PLCReadWrite, PLCVar, PLCVarDict

#TODO: manage exceptions when parent.client is none

class PLCMemoryArea(BaseModel, ABC):
    vars: PLCVarDict = Field(default_factory= PLCVarDict)
    size: int = Field(ge= 0, default= 0)

    def __str__(self) -> str:
        return f'{self.name}'

    def __eq__(self, value: Any) -> bool:
        return isinstance(value, self.__class__)

    @property
    def name(self) -> str:
        return f'{self.__class__.__name__}'

    @classmethod
    @abstractmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        ...

    @abstractmethod
    def read_area(self, client: Client) -> PLCComResult:
        ...

    @abstractmethod
    def _read_var(self, var: PLCVar, client: Client) -> bytearray:
        ...

    def get_var(self, var: PLCVar | str) -> Any:
        try:
            if isinstance(var, str):
                var = self.vars[var]
            return self.vars[var.name].value
        except ValueError:
            msg: str = f'{self}: {var} not found in variables.'
            pyplc_logger.error(msg)
            raise ValueError(msg)

    def read_var(
        self,
        var: PLCVar | str,
        client: Client
    ) -> tuple[PLCComResult, Any]:
        try:
            if isinstance(var, str):
                var = self.vars[var]
            self.vars[var.name].value = self._read_var(var, client)
            pyplc_logger.debug(f'{self}: "{self.vars[var.name]}" readed.')
            return (PLCComResult.SUCCESS, self.vars[var.name].value)
        except KeyError:
            msg: str = f'{self}.{var} not found in variables.'
            pyplc_logger.error(msg)
            return (PLCComResult.INVALID_PARAMS, None)
        except RuntimeError as e:
            result: PLCComResult = self.manage_runtime_error(e)
            msg: str = f'{self}.{var} read error {result}. {PLCClientErrors.get_str(e)}.'
            pyplc_logger.error(msg)
            return (result, None)

    def write_area(self, client: Client) -> PLCComResult:
        results: list[int] = [self._write_var(var, client) for var in self.vars.values()]
        if PLCComResult.NOT_CONNECTED in results:
            return PLCComResult.NOT_CONNECTED
        pyplc_logger.debug(f'{self} writed.', Styles.SUCCEED)
        return PLCComResult.SUCCESS

    @abstractmethod
    def _write_var(self, var: PLCVar, client: Client) -> PLCComResult:
        ...

    def set_var(self, var: PLCVar | str, value: Any) -> None:
        try:
            if isinstance(var, str):
                var = self.vars[var]
            self.vars[var.name].value = value
            pyplc_logger.debug(f'{self}: {self.vars[var.name]} setted.', Styles.SUCCEED)
        except KeyError:
            msg: str = f'{self}.{var} not found in variables.'
            pyplc_logger.error(msg)
            raise KeyError(msg)

    def write_var(
        self,
        var: PLCVar | str,
        value: Any,
        client: Client
    ) -> tuple[PLCComResult, Any]:
        try:
            if isinstance(var, str):
                var = self.vars[var]
            self.vars[var.name].value = value
            result: PLCComResult = self._write_var(self.vars[var.name], client)
            if not result.is_error():
                pyplc_logger.debug(f'{self}.{self.vars[var.name]} writed.')
            return (result, value)
        except KeyError:
            msg: str = f'{self}.{var} not found in variables.'
            pyplc_logger.error(msg)
            return (PLCComResult.INVALID_PARAMS, None)

    def manage_runtime_error(self, error: Exception) -> PLCComResult:
        if str(error) == str(PLCClientErrors.NOT_CONNECTED):
            return PLCComResult.NOT_CONNECTED
        if str(error) == str(PLCClientErrors.INVALID_PARAMS):
            return PLCComResult.INVALID_PARAMS
        return PLCComResult.UNESPECIFY_ERROR


class PLCInputs(PLCMemoryArea):
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        size: int = 0
        vars: PLCVarDict = PLCVarDict()
        for name, value in data.items():
            if name.upper() == 'SIZE':
                size = value
            if isinstance(value, dict):
                vars[name] = PLCVar.from_dict(value)
        if size == 0:
            msg: str = f'"SIZE" not found in data to build {cls.__name__}.'
            pyplc_logger.error(msg)
            raise ValueError(msg)
        return cls(vars= vars, size= size)

    def read_area(self, client: Client) -> PLCComResult:
        try:
            buffer: bytearray = client.eb_read(0, self.size)
        except RuntimeError as e:
            return self.manage_runtime_error(e)
        error_vars: list[PLCVar] = []
        for var in self.vars.values():
            try:
                var.set_value_from_buffer(buffer)
            except ValueError:
                error_vars.append(var)
        if len(error_vars) > 0:
            pyplc_logger.warning(f'Unable to read {error_vars}.')
            return PLCComResult.UNCOMPLETED
        pyplc_logger.debug(f'{self} readed.', Styles.SUCCEED)
        return PLCComResult.SUCCESS

    def _read_var(self, var: PLCVar, client: Client) -> bytearray:
        try:
            return client.eb_read(var.offset.bytes_offset, var.bytes_size)
        except RuntimeError:
            raise

    def _write_var(self, var: PLCVar, client: Client) -> PLCComResult:
        if var.rw not in (PLCReadWrite.READ_WRITE,):
            pyplc_logger.warning(f'{self}.{var} is a read only var.')
            return PLCComResult.READ_ONLY
        try:
            value: bytearray = var.get_bytes_array()
        except ValueError as e:
            pyplc_logger.error(f'Can\'t write {self}.{var}. {e}.')
            return PLCComResult.INVALID_PARAMS
        try:
            client.eb_write(var.offset.bytes_offset, var.bytes_size, value)
            pyplc_logger.debug(f'{self}.{var} writed.', Styles.SUCCEED)
            return PLCComResult.SUCCESS
        except RuntimeError as e:
            pyplc_logger.error(f'Can\'t write {self}.{var}. {e}.')
            return self.manage_runtime_error(e)


class PLCOutputs(PLCMemoryArea):
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        size: int = 0
        vars: PLCVarDict = PLCVarDict()
        for name, value in data.items():
            if name.upper() == 'SIZE':
                size = value
            if isinstance(value, dict):
                vars[name] = PLCVar.from_dict(value)
        if size == 0:
            msg: str = f'"SIZE" not found in data to build {cls.__name__}.'
            pyplc_logger.error(msg)
            raise ValueError(msg)
        return cls(vars= vars, size= size)

    def read_area(self, client: Client) -> PLCComResult:
        try:
            buffer: bytearray = client.ab_read(0, self.size)
        except RuntimeError as e:
            return self.manage_runtime_error(e)
        error_vars: list[PLCVar] = []
        for var in self.vars.values():
            try:
                var.set_value_from_buffer(buffer)
            except ValueError:
                error_vars.append(var)
        if len(error_vars) > 0:
            pyplc_logger.warning(f'Unable to read {error_vars}.')
            return PLCComResult.UNCOMPLETED
        pyplc_logger.debug(f'{self} readed.', Styles.SUCCEED)
        return PLCComResult.SUCCESS

    def _read_var(self, var: PLCVar, client: Client) -> bytearray:
        try:
            return client.ab_read(var.offset.bytes_offset, var.bytes_size)
        except RuntimeError:
            raise

    def _write_var(self, var: PLCVar, client: Client) -> PLCComResult:
        if var.rw not in (PLCReadWrite.READ_WRITE,):
            pyplc_logger.warning(f'{self}.{var} is a read only var')
            return PLCComResult.READ_ONLY
        try:
            value: Optional[bytearray] = var.get_bytes_array()
        except ValueError as e:
            pyplc_logger.error(f'Can\'t write {self}.{var}. {e}.')
            return PLCComResult.INVALID_PARAMS
        try:
            client.ab_write(var.offset.bytes_offset, value)
            pyplc_logger.debug(f'{self}.{var} writed.', Styles.SUCCEED)
            return PLCComResult.SUCCESS
        except RuntimeError as e:
            pyplc_logger.error(f'Can\'t write {self}.{var}. {e}.')
            return self.manage_runtime_error(e)


class PLCMarks(PLCMemoryArea):
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        size: int = 0
        vars: PLCVarDict = PLCVarDict()
        for name, value in data.items():
            if name.upper() == 'SIZE':
                size = value
            if isinstance(value, dict):
                vars[name] = PLCVar.from_dict(value)
        if size == 0:
            msg: str = f'"SIZE" not found in data to build {cls.__name__}.'
            pyplc_logger.error(msg)
            raise ValueError(msg)
        return cls(vars= vars, size= size)

    def read_area(self, client: Client) -> PLCComResult:
        try:
            buffer: bytearray = client.mb_read(0, self.size)
        except RuntimeError as e:
            return self.manage_runtime_error(e)
        error_vars: list[PLCVar] = []
        for var in self.vars.values():
            try:
                var.set_value_from_buffer(buffer)
            except ValueError:
                error_vars.append(var)
        if len(error_vars) > 0:
            pyplc_logger.warning(f'Unable to read {error_vars}.')
            return PLCComResult.UNCOMPLETED
        pyplc_logger.debug(f'{self} readed.', Styles.SUCCEED)
        return PLCComResult.SUCCESS

    def _read_var(self, var: PLCVar, client: Client) -> bytearray:
        try:
            return client.mb_read(var.offset.bytes_offset, var.bytes_size)
        except RuntimeError:
            raise

    def _write_var(self, var: PLCVar, client: Client) -> PLCComResult:
        if var.rw not in (PLCReadWrite.READ_WRITE,):
            pyplc_logger.warning(f'{self}.{var} is a read only var.')
            return PLCComResult.READ_ONLY
        try:
            value: Optional[bytearray] = var.get_bytes_array()
        except TypeError as e:
            pyplc_logger.error(f'Can\'t write {self}.{var}. {e}.')
            return PLCComResult.INVALID_PARAMS
        try:
            client.mb_write(var.offset.bytes_offset, var.bytes_size, value)
            pyplc_logger.debug(f'{self}.{var} writed.', Styles.SUCCEED)
            return PLCComResult.SUCCESS
        except RuntimeError as e:
            pyplc_logger.error(f'Can\'t write {self}.{var}. {e}.')
            return self.manage_runtime_error(e)


class PLCDB(PLCMemoryArea):
    number: int = Field(ge= 0)

    def __eq__(self, value: Any) -> bool:
        try:
            return self.number == int(value)
        except (ValueError, TypeError):
            return False

    def __int__(self) -> int:
        return self.number

    @property
    def name(self) -> str:
        return f'{self.__class__.__name__}{self.number}'

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        size: int = 0
        number: Optional[int] = None
        vars: PLCVarDict = PLCVarDict()
        for name, value in data.items():
            if name.upper() == 'SIZE':
                size = value
            if name.upper() == 'NUMBER':
                number = value
            if isinstance(value, dict):
                vars[name] = PLCVar.from_dict(value)
        if size == 0:
            msg: str = f'"SIZE" not found in data to build {cls.__name__}.'
            pyplc_logger.error(msg)
            raise ValueError(msg)
        if number is None:
            msg: str = f'"NUMBER" not found in data to build {cls.__name__}.'
            pyplc_logger.error(msg)
            raise ValueError(msg)
        return cls(vars= vars, size= size, number= number)

    def read_area(self, client: Client) -> PLCComResult:
        try:
            buffer: bytearray = client.db_read(self.number, 0, self.size)
        except RuntimeError as e:
            return self.manage_runtime_error(e)
        error_vars: list[PLCVar] = []
        for var in self.vars.values():
            try:
                var.set_value_from_buffer(buffer)
            except ValueError:
                error_vars.append(var)
        if len(error_vars) > 0:
            pyplc_logger.warning(f'Unable to read {error_vars}.')
            return PLCComResult.UNCOMPLETED
        pyplc_logger.debug(f'{self} readed.', Styles.SUCCEED)
        return PLCComResult.SUCCESS

    def _read_var(self, var: PLCVar, client: Client) -> bytearray:
        try:
            return client.db_read(self.number, var.offset.bytes_offset, var.bytes_size)
        except RuntimeError:
            raise

    def _write_var(self, var: PLCVar, client: Client) -> PLCComResult:
        if var.rw not in (PLCReadWrite.READ_WRITE,):
            pyplc_logger.warning(f'{self}.{var} is a read only var')
            return PLCComResult.READ_ONLY
        try:
            value: Optional[bytearray] = var.get_bytes_array()
        except TypeError as e:
            pyplc_logger.error(f'Can\'t write {self}.{var}. {e}.')
            return PLCComResult.INVALID_PARAMS
        try:
            client.db_write(self.number, var.offset.bytes_offset, value)
            pyplc_logger.debug(f'{self}.{var} writed.', Styles.SUCCEED)
            return PLCComResult.SUCCESS
        except RuntimeError as e:
            pyplc_logger.error(f'Can\'t write {self}.{var}. {e}.')
            return self.manage_runtime_error(e)
