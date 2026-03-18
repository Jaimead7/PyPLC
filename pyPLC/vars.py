from collections.abc import Sequence
from enum import IntEnum, unique
from re import match
from typing import Any, Type

from pydantic import BaseModel, field_validator, model_validator
from typing_extensions import Self

from .logging import pyplc_logger
from .var_types import PLCVarType, PLCVarTypesReg


@unique
class PLCReadWrite(IntEnum):
    READWRITE = 0
    READ = 1


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
                raise ValueError(f'{args} not valid for {self.__class__.__name__}.')
        elif len(args) == 2:
            self._init_from_seq(args[0][:2])
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
            raise ValueError(f'"{value}" is not a valid {self.__class__.__name__} str.')

    def _init_from_seq(self, value: Sequence) -> None:
        try:
            byte_str: str
            bit_str: str
            byte_str, bit_str = value[:2]
            bytes_int: int = int(byte_str)
            bits_int: int = int(bit_str)
            if bytes_int < 0 or bits_int < 0:
                raise ValueError
            self.bytes_offset = bytes_int
            self.bits_offset = bits_int
        except ValueError:
            raise ValueError(f'"{value}" is not a valid {self.__class__.__name__} Sequence.')


class PLCVar(BaseModel):
    name: str
    offset: PLCMemoryOffset
    var_type: Type[PLCVarType]
    rw: PLCReadWrite = PLCReadWrite.READ
    value: Any = None

    def __str__(self) -> str:
        return f'{self.name}({self.var_type.__name__})'

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
        return self.var_type.BYTES + self.var_type.BITS * 8

    @property
    def bytes_size(self) -> int:
        return self.var_type.BYTES if self.var_type.BYTES != 0 else 1

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        ...

    @field_validator('var_type', mode= 'before')
    def validate_var_type(cls, value: Any) -> Type[PLCVarType]:
        if issubclass(value, PLCVarType):
            return value
        try:
            return PLCVarTypesReg.get(str(value))
        except ValueError:
            msg: str = f'Invalid type for {cls.__name__}.var_type: {value}'
            pyplc_logger.error(msg)
            raise ValueError(msg)

    @model_validator(mode= 'after')
    def validate_value(self) -> Any:
        if self.value is None:
            return
        try:
            self.value = self.var_type.validate_value(self.value, self.offset.bits_offset)
        except ValueError:
            msg: str = f'Invalid value for {self.__class__.__name__} of type "{self.var_type.NAME}": {self.value}'
            self.value = None
            pyplc_logger.error(msg)
            raise ValueError(msg)

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
            raise TypeError(f'{self.__class__.__name__}: {value} is not type PLCVar.')
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

    def update(self, *args, **kwargs) -> None:
        if len(args) > 1:
            raise TypeError(f'Update expected at most 1 argument, got {len(args)}')
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
