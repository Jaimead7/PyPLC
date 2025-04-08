from __future__ import annotations

from dataclasses import KW_ONLY, InitVar, dataclass
from typing import Any, ClassVar, Optional, Type

from pyUtils import NoInstantiable, ValidationClass, debugLog, errorLog

from .plcVarTypes import PLCVarType, PLCVarTypesFactory


class PLCReadWrite(NoInstantiable):
    READWRITE: ClassVar[int] = 0
    READ: ClassVar[int] = 1
    _DICT: ClassVar[dict] = {'READ': READ,
                             'READWRITE': READWRITE}

    @classmethod
    def validate(cls, value: Any) -> int:
        if isinstance(value, str):
            try:
                return cls._DICT[ValidationClass.validateStr(value).upper()]
            except KeyError:
                ...
        try:
            value = ValidationClass.validatePositiveInt(value)
            if value in cls._DICT.values():
                return value
        except TypeError:
            ...
        raise TypeError(f'{value} is not a valid {cls.__name__}')


class PLCMemoryOffset():
    def __init__(self, *args, **kwargs) -> None:
        try:
            if len(args) == 1:
                if isinstance(args[0], str):
                    input: tuple = tuple((ValidationClass.validatePositiveInt(args[0].split('.')[0]),
                                          ValidationClass.validatePositiveInt(args[0].split('.')[1]))) 
                elif isinstance(args[0], (tuple, list)):
                    input: tuple = tuple((ValidationClass.validatePositiveInt(args[0][0]),
                                          ValidationClass.validatePositiveInt(args[0][1])))
                else:
                    raise TypeError
            if len(args) == 2:
                input: tuple = ((ValidationClass.validatePositiveInt(args[0]),
                                 ValidationClass.validatePositiveInt(args[1])))
            try:
                input: tuple = ((ValidationClass.validatePositiveInt(kwargs['bytesOffset']),
                                 ValidationClass.validatePositiveInt(kwargs['bitsOffset'])))
            except KeyError:
                pass
            if input[1] > 7: raise TypeError
        except TypeError:
            raise TypeError(f'{args} not valid as {self.__class__.__name__}')
        self.bytesOffset: int = input[0]
        self.bitsOffset: int = input[1]

    def __str__(self) -> str:
        return f'({self.bytesOffset}.{self.bitsOffset})'

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self.bytesOffset}.{self.bitsOffset})'

    def __eq__(self, other: PLCMemoryOffset) -> bool:
        if not isinstance(other, PLCMemoryOffset):
            try:
                other = PLCMemoryOffset(other)
            except TypeError:
                return False
        conditions: tuple[bool] = (self.bytesOffset == other.bytesOffset,
                                   self.bitsOffset == other.bitsOffset)
        return all(conditions)


@dataclass
class PLCVar(ValidationClass):
    name: str = ''
    offset: PLCMemoryOffset = PLCMemoryOffset('0.0')
    varType: Type[PLCVarType] = PLCVarTypesFactory.get('bool')
    rw: int = PLCReadWrite.READ
    value: Optional[Any] = None
    _: KW_ONLY
    fromDict: InitVar[Optional[dict]] = None

    def __post_init__(self, fromDict: Optional[dict]) -> None:
        if fromDict is not None:
            try:
                self.name = fromDict['Name']
                debugLog(f'{self._identifier}: name overwritten from dict')
            except KeyError:
                pass
            try:
                self.offset = fromDict['Offset']
                debugLog(f'{self._identifier}: offset overwritten from dict')
            except KeyError:
                pass
            try:
                self.varType = fromDict['Type']
                debugLog(f'{self._identifier}: varType overwritten from dict')
            except KeyError:
                pass
            try:
                self.rw = fromDict['R/W']
                debugLog(f'{self._identifier}: rw overwritten from dict')
            except KeyError:
                pass
        super().__post_init__()

    def __str__(self) -> str:
        return self.name

    def __eq__(self, value: object) -> bool:
        if isinstance(value, self.__class__):
            conditions: tuple[bool] = (self.name == value.name,
                                       self.offset == value.offset,
                                       self.varType == value.varType)
            return all(conditions)
        if isinstance(value, str):
            return self.name == value
        return super().__eq__(value)

    def __len__(self) -> int:  #INFO: if not defined pytest will fail if PLCVar is parametrize
        return self.varType.BYTES + self.varType.BITS * 8

    @property
    def _identifier(self) -> str:
        return f'{self.__class__.__name__}({self.name})'

    @property
    def bytesSize(self) -> int:
        return self.varType.BYTES if self.varType.BYTES != 0 else 1

    def validate_name(self, value: Any) -> str:
        try:
            return self.validateStr(value)
        except TypeError:
            msg: str = f'Invalid type for {self._identifier}.name: {value}'
            errorLog(msg)
            raise TypeError(msg)

    def validate_offset(self, value: Any) -> PLCMemoryOffset:
        if isinstance(value, PLCMemoryOffset):
            return value
        try:
            return PLCMemoryOffset(value)
        except TypeError:
            msg: str = f'Invalid type for {self._identifier}.offset: {value}'
            errorLog(msg)
            raise TypeError(msg)

    def validate_varType(self, value: Any) -> Type[PLCVarType]:
        try:
            if issubclass(value, PLCVarType):
                return value
        except TypeError:
            pass
        try:
            return PLCVarTypesFactory.get(self.validateStr(value))
        except TypeError:
            msg: str = f'Invalid type for {self._identifier}.varType: {value}'
            errorLog(msg)
            raise TypeError(msg)

    def validate_rw(self, value: Any) -> int:
        try:
            value = PLCReadWrite.validate(value)
            return value
        except TypeError:
            msg: str = f'Invalid type for {self._identifier}.rw: {value}'
            errorLog(msg)
            raise TypeError(msg)

    def validate_value(self, value: Any) -> Optional[Any]:
        if value is None: return value
        try:
            return self.varType.validateValue(value, self.offset.bitsOffset)
        except TypeError:
            msg: str = f'Invalid type for {self._identifier}.value of type "{self.varType.NAME}": {value}'
            errorLog(msg)
            raise TypeError(msg)

    def getBytearray(self, lastValue: bytearray = bytearray()) -> bytearray:
        return self.varType.getBytearray(self.value, lastValue, self.offset.bitsOffset)

    def fromMemoryArea(self, buffer: bytearray) -> None:
        result: bytearray = buffer[self.offset.bytesOffset : self.offset.bytesOffset + self.bytesSize]
        if len(result) != self.bytesSize:
            msg: str = f'{self._identifier}.fromMemoryArea(): buffer out of bounds. len(buffer) == {len(buffer)}; size == {self.bytesSize}'
            errorLog(msg)
            raise TypeError(msg)
        self.value = result
