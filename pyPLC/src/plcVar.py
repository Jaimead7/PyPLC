from dataclasses import KW_ONLY, InitVar, dataclass
from typing import Any, ClassVar, Optional, Type

from pyUtils import NoInstantiable, ValidationClass, warningLog

from .plcVarTypes import PLCVarType, PLCVarTypesFactory


class PLCReadWrite(NoInstantiable):
    READWRITE: ClassVar[int] = 0
    READ: ClassVar[int] = 1
    WRITE: ClassVar[int] = 2
    _DICT: ClassVar[dict] = {'READ': READ,
                             'WRITE': WRITE,
                             'READWRITE': READWRITE}

    @classmethod
    def get(cls, value: str) -> int:
        try:
            return cls._DICT[ValidationClass.validateStr(value).upper()]
        except KeyError:
            raise KeyError(f'{value} not found in {cls.__name__}')

    @classmethod
    def check(cls, value: int) -> bool:
        return value in cls._DICT.values()


class PLCMemoryOffset():
    def __init__(self, *args, **kwargs) -> None:
        try:
            if len(args) == 1:
                if isinstance(args[0], str):
                    args[0] = args[0].split('.')
                if isinstance(args[0], (tuple, list)):
                    input: tuple = tuple(ValidationClass.validatePositiveInt(args[0][0]),
                                         ValidationClass.validatePositiveInt(args[0][1]))
                else:
                    raise TypeError
            if len(args) == 2:
                input: tuple = (ValidationClass.validatePositiveInt(args[0]),
                                ValidationClass.validatePositiveInt(args[1]))
            try:
                input: tuple = (ValidationClass.validatePositiveInt(kwargs['bytesOffset']),
                                ValidationClass.validatePositiveInt(kwargs['bitsOffset']))
            except KeyError:
                pass
        except TypeError:
            raise TypeError(f'{args} not valid as {self.__class__.__name__}')
        self.bytesOffset: int = input[0]
        self.bitsOffset: int = input[1]


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
        if fromDict:
            try:
                self.name = fromDict['Name']
            except KeyError:
                pass
            try:
                self.offset = fromDict['Offset']
            except KeyError:
                pass
            try:
                self.varType = fromDict['Type']
            except KeyError:
                pass
            try:
                self.rw = PLCReadWrite.get(fromDict['R/W'])
            except KeyError:
                pass
        super().__post_init__()

    def __eq__(self, value: object) -> bool:
        if isinstance(value, self.__class__):
            return self.name == value.name and self.varType == value.varType
        if isinstance(value, str):
            return self.name == value
        return super().__eq__(value)

    def validate_name(self, value: Any) -> str:
        try:
            return self.validateStr(value)
        except TypeError:
            raise TypeError(f'Invalid type {self.__class__.__name__}.name')

    def validate_offset(self, value: Any) -> PLCMemoryOffset:
        if isinstance(value, PLCMemoryOffset):
            return value
        return PLCMemoryOffset(value)

    def validate_varType(self, value: Any) -> Type[PLCVarType]:
        if issubclass(value, PLCVarType):
            return value
        return PLCVarTypesFactory.get(self.validateStr(value))

    def validate_rw(self, value: Any) -> int:
        value = self.validatePositiveInt(value)
        if PLCReadWrite.check(value):
            return value
        raise TypeError(f'Invalid type {self.__class__.__name__}.rw')

    def validate_value(self, value: Any) -> Optional[Any]:
        if value is None: return value
        try:
            return self.varType.validateValue(value, self.offset.bitsOffset)
        except TypeError:
            raise TypeError(f'Invalid type {self.__class__.__name__}.value of type "{self.varType.NAME}"')

    def bytearray(self, lastValue: bytearray = bytearray()) -> bytearray:
        return self.varType.getBytearray(self.value, lastValue, self.offset.bitsOffset)

    def fromMemoryArea(self, buffer: bytearray) -> None:
        auxBytes: int = self.varType.BYTES if self.varType.BYTES != 0 else 1
        self.value = buffer[self.offset.bytesOffset: self.offset.bytesOffset + auxBytes]
