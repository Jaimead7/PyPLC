from collections.abc import Sequence
from enum import IntEnum, unique
from re import match
from typing import Any, Optional

from pydantic import (BaseModel, ConfigDict, ValidationInfo, field_serializer,
                      field_validator)
from pydantic_core import CoreSchema, core_schema
from typing_extensions import Self

from .logs import pyplc_logger
from .var_types import PLCVarType, PLCVarTypesReg


@unique
class PLCReadWrite(IntEnum):
    READ_WRITE = 0
    READ = 1

    @classmethod
    def validate(cls, value: str | int | Self) -> Self:
        if isinstance(value, cls):
            return value
        try:
            return cls(int(value))
        except (ValueError, TypeError):
            pass
        try:
            value_clear: str = str(value).strip().upper()
            return cls[value_clear]
        except Exception:
            pass
        return cls['READ']


class PLCMemoryOffset():
    def __init__(self, *args, **kwargs) -> None:
        self.bytes_offset: int
        self.bits_offset: int
        if len(args) == 1:
            if isinstance(args[0], str):
                self._init_from_str(args[0])
            elif isinstance(args[0], Sequence):
                self._init_from_seq(args[0])
            else:
                msg: str = f'{args} not valid for {self.__class__.__name__}.'
                pyplc_logger.critical(msg)
                raise ValueError(msg)
        elif len(args) >= 2:
            self._init_from_seq(args[:2])
        try:
            self._init_from_seq((
                kwargs['bytes_offset'],
                kwargs['bits_offset']
            ))
        except KeyError:
            pass

    def __str__(self) -> str:
        return f'({self.bytes_offset}.{self.bits_offset})'

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self.bytes_offset}.{self.bits_offset})'

    def __eq__(self, other: object) -> bool:
        if other is None:
            return False
        if not isinstance(other, PLCMemoryOffset):
            try:
                other = PLCMemoryOffset(other)
            except ValueError:
                return False
        conditions: tuple[bool, ...] = (
            self.bytes_offset == other.bytes_offset,
            self.bits_offset == other.bits_offset
        )
        return all(conditions)

    def __get_pydantic_core_schema__(self, *args, **kwargs) -> CoreSchema:
        return core_schema.no_info_plain_validator_function(
            self._validate,
            serialization= core_schema.plain_serializer_function_ser_schema(
                self._serialize,
                info_arg= False,
                return_schema= core_schema.dict_schema(
                    keys_schema= core_schema.str_schema(),
                    values_schema= core_schema.int_schema()
                )
            )
        )

    @classmethod
    def _validate(cls, value: Any) -> 'PLCMemoryOffset':
        if isinstance(value, PLCMemoryOffset):
            return value
        if isinstance(value, dict):
            return cls(**value)
        if isinstance(value, (list, tuple)) and len(value) == 2:
            return cls(bytes_offset= value[0], bits_offset= value[1])
        if isinstance(value, str):
            return cls(value)
        msg: str = f'Can\'t convert {value} to {cls.__name__}.'
        pyplc_logger.critical(msg)
        raise ValueError(msg)

    @classmethod
    def _serialize(cls, value: 'PLCMemoryOffset') -> dict[str, int]:
        return {
            'bytes_offset': value.bytes_offset,
            'bits_offset': value.bits_offset
        }

    def _init_from_str(self, value: str) -> None:
        pattern = r'^\d+\.[0-7]'
        try:
            if not match(pattern, value):
                raise ValueError
            byte_str: str
            bit_str: str
            byte_str, bit_str = value.split('.')
            self._init_from_seq((byte_str, bit_str))
        except ValueError:
            msg: str = f'"{value}" is not a valid {self.__class__.__name__} str.'
            pyplc_logger.critical(msg)
            raise ValueError(msg)

    def _init_from_seq(self, value: Sequence) -> None:
        try:
            byte_str: str
            bit_str: str
            byte_str, bit_str = value[:2]
            bytes_int: int = int(byte_str)
            bits_int: int = int(bit_str)
            if bytes_int < 0 or bits_int < 0 or bits_int > 7:
                raise ValueError
            self.bytes_offset = bytes_int
            self.bits_offset = bits_int
        except ValueError:
            msg: str = f'"{value}" is not a valid {self.__class__.__name__} Sequence.'
            pyplc_logger.critical(msg)
            raise ValueError(msg)


class PLCVar(BaseModel):
    name: str
    offset: PLCMemoryOffset
    var_type: type[PLCVarType]
    rw: PLCReadWrite = PLCReadWrite.READ
    value: Any = None

    model_config = ConfigDict(
        validate_assignment= True
    )

    def __str__(self) -> str:
        return f'{self.name}[{self.var_type.__name__}]'

    def __repr__(self) -> str:
        return f'{self.name}[type: {self.var_type.__name__}, offset: {self.offset}, rw: {self.rw}, value: {self.value}]'

    def __eq__(self, value: object) -> bool:
        if isinstance(value, self.__class__):
            conditions: tuple[bool, ...] = (
                self.name == value.name,
                self.offset == value.offset,
                self.var_type == value.var_type
            )
            return all(conditions)
        if isinstance(value, str):
            return self.name == value
        return super().__eq__(value)

    def __len__(self) -> int:  #INFO: if not defined pytest will fail if PLCVar is parametrize
        return self.var_type.BYTES * 8 + self.var_type.BITS

    @property
    def bytes_size(self) -> int:
        return self.var_type.BYTES if self.var_type.BYTES != 0 else 1

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        name: Optional[str] = None
        offset: Optional[PLCMemoryOffset] = None
        var_type: Optional[type[PLCVarType]] = None
        rw: Optional[PLCReadWrite] = None
        for key, value in data.items():
            match key.upper():
                case 'NAME':
                    name = str(value)
                case 'OFFSET':
                    offset = PLCMemoryOffset(value)
                case 'TYPE':
                    var_type = PLCVarTypesReg.get(value)
                case 'RW':
                    rw = PLCReadWrite.validate(value)
        if None in (name, offset, var_type, rw):
            msg: str = f'Data doesn\'t have a valid {cls.__name__}.'
            pyplc_logger.critical(msg)
            raise ValueError(msg)
        return cls(
            name= name,  # type: ignore
            offset= offset,  # type: ignore
            var_type= var_type,  # type: ignore
            rw= rw  # type: ignore
        )

    @field_serializer('var_type')
    def serialize_var_type(self, var_type: type[PLCVarType]) -> str:
        return var_type.__name__

    @field_validator('var_type', mode= 'before')
    def validate_var_type(cls, value: Any) -> type[PLCVarType]:
        try:
            if issubclass(value, PLCVarType):
                return value
        except TypeError:
            pass
        try:
            return PLCVarTypesReg.get(str(value))
        except ValueError:
            msg: str = f'Invalid type for {cls.__name__}.var_type: {value}'
            pyplc_logger.error(msg)
            raise ValueError(msg)

    @field_validator('value')
    def validate_value(cls, value: Any, info: ValidationInfo) -> Any:
        var_type: Optional[type[PLCVarType]] = info.data.get('var_type')
        offset: Optional[PLCMemoryOffset] = info.data.get('offset')
        if value is None or var_type is None or offset is None:
            return None
        try:
            return var_type.validate_value(
                value,
                offset.bits_offset
            )
        except ValueError:
            msg: str = f'Invalid value for {cls.__name__} of type "{var_type.NAME}": {value}.'
            pyplc_logger.error(msg)
            raise ValueError(msg)

    @field_validator('rw', mode= 'before')
    def validate_rw(cls, value: Any) -> PLCReadWrite:
        return PLCReadWrite.validate(value)

    def get_bytes_array(self, last_value: bytearray = bytearray()) -> bytearray:
        try:
            result: bytearray = self.var_type.get_bytes_array(
                value= self.value,
                last_value= last_value,
                pos= self.offset.bits_offset
            )
        except ValueError:
            raise
        return result

    def set_value_from_buffer(self, buffer: bytes) -> None:
        try:
            result: bytes = buffer[self.offset.bytes_offset : self.offset.bytes_offset + self.bytes_size]
        except IndexError:
            msg: str = f'Can\'t read {self} from "buffer". Out of range.'
            pyplc_logger.error(msg)
            raise ValueError(msg)
        self.value = result


class PLCVarDict(dict[str, PLCVar]):
    def __init__(self, *args, **kwargs) -> None:
        self.update(*args, **kwargs)

    def __getitem__(self, key) -> PLCVar:
        key_str: str = str(key)
        return super().__getitem__(key_str)

    def __setitem__(self, key, value) -> None:
        if not isinstance(value, PLCVar):
            msg: str = f'{self.__class__.__name__}: {value} is not type PLCVar.'
            pyplc_logger.critical(msg)
            raise ValueError(msg)
        key_str: str = str(key)
        return super().__setitem__(key_str, value)

    def __ior__(self, other: Any) -> Self:
        if not isinstance(other, (dict, PLCVarDict)):
            return NotImplemented
        self.update(other)
        return self

    def __or__(self, other: Any) -> Self:
        if not isinstance(other, (dict, PLCVarDict)):
            return NotImplemented
        new_dict: Self = self.__class__(self)
        new_dict.update(other)
        return new_dict

    def __str__(self) -> str:
        return str([str(value) for value in self.values()])

    def __repr__(self) -> str:
        return str(list(self.values()))

    def __get_pydantic_core_schema__(self, *args, **kwargs) -> CoreSchema:
        return core_schema.no_info_plain_validator_function(
            self._validate,
            serialization= core_schema.plain_serializer_function_ser_schema(
                self._serialize,
                info_arg= False,
                return_schema= core_schema.dict_schema(
                    keys_schema= core_schema.str_schema(),
                    values_schema= core_schema.int_schema()
                )
            )
        )

    @classmethod
    def _validate(cls, value: Any) -> 'PLCVarDict':
        if isinstance(value, PLCVarDict):
            return value
        msg: str = f'Can\'t convert {value} to {cls.__name__}.'
        pyplc_logger.critical(msg)
        raise ValueError(msg)

    @classmethod
    def _serialize(cls, value: 'PLCVarDict') -> dict[str, PLCVar]:
        return value

    def update(self, *args, **kwargs) -> None:
        if len(args) > 1:
            msg: str = f'Update expected at most 1 argument, got {len(args)}'
            pyplc_logger.error(msg)
            raise ValueError(msg)
        if args:
            other: Any = args[0]
            if isinstance(other, dict):
                for key, value in other.items():
                    key_str = str(key)
                    self[key_str] = value
            else:
                for key, value in other:
                    key_str = str(key)
                    self[key_str] = value
        for key, value in kwargs.items():
            key_str: str = str(key)
            self[key_str] = value

    def copy(self) -> Self:
        return self.__class__(self)
