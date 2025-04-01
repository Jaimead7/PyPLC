from datetime import date, time, timedelta
from struct import error as StructError
from struct import pack, unpack
from types import MappingProxyType
from typing import Any, ClassVar, Optional, Type

from pyUtils import NoInstantiable, ValidationClass


class PLCVarType():
    NAME: ClassVar[str] = ''
    BYTES: ClassVar[int] = 0
    BITS: ClassVar[int] = 0

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self.NAME}, {self.BYTES}, {self.BITS})'

    def __str__(self) -> str:
        return self.NAME

    @classmethod
    def validateValue(cls, value: Any, *args, **kwargs) -> Any:
        raise TypeError(f'{value} is not type {cls.NAME}')

    @classmethod
    def getBytearray(cls, newValue: Any, *args, **kwargs) -> bytes:
        raise TypeError(f'{newValue} is not type {cls.NAME}')


class PLCBoolType(PLCVarType, NoInstantiable):
    NAME: ClassVar[str] = 'Bool'
    BYTES: ClassVar[int] = 0
    BITS: ClassVar[int] = 1

    @classmethod
    def validateValue(cls, value: Any, pos: int = 0, *args, **kwargs) -> bool:
        try:
            if isinstance(value, bytearray):
                return int.from_bytes(value, 'big') & 2 ** pos != 0
            return ValidationClass.validateBool(value)
        except [TypeError, StructError]:
            super(cls, cls).validateValue(value)

    @classmethod
    def getBytearray(cls,
                     newValue: Any,
                     lastValue: bytearray = bytearray([0]),
                     pos: int = 0,
                     *args,
                     **kwargs) -> bytes:
        try:
            if ValidationClass.validateBool(newValue):
                mask = int(2 ** pos)
                return pack('>B', mask | int.from_bytes(lastValue, 'big'))
            else:
                mask = int(int(2 ** pos) ^ 255)
                return pack('>B', mask & int.from_bytes(lastValue, 'big'))
        except [TypeError, StructError]:
            super(cls, cls).getBytearray(newValue)


class PLCByteType(PLCVarType, NoInstantiable):
    NAME: ClassVar[str] = 'Byte'
    BYTES: ClassVar[int] = 1
    BITS: ClassVar[int] = 0

    @classmethod
    def validateValue(cls, value: Any, *args, **kwargs) -> Any:
        try:
            if isinstance(value, bytearray):
                return unpack('>b', value)[0]
            value = ValidationClass.validateInt(value)
            if value in range(-((2**(8*cls.BYTES))//2), (2**(8*cls.BYTES))//2):
                return value
        except [TypeError, StructError]:
            pass
        super(cls, cls).validateValue(value)

    @classmethod
    def getBytearray(cls, newValue: Any, *args, **kwargs) -> bytes:
        try:
            newValue = ValidationClass.validateInt(newValue)
            return pack('>b', newValue)
        except [TypeError, StructError]:
            super(cls, cls).getBytearray(newValue)


class PLCWordType(PLCVarType, NoInstantiable):
    NAME: ClassVar[str] = 'Word'
    BYTES: ClassVar[int] = 2
    BITS: ClassVar[int] = 0

    @classmethod
    def validateValue(cls, value: Any, *args, **kwargs) -> Any:
        try:
            if isinstance(value, bytearray):
                return unpack('>h', value)[0]
            value = ValidationClass.validateInt(value)
            if value in range(-((2**(8*cls.BYTES))//2), (2**(8*cls.BYTES))//2):
                return value
        except [TypeError, StructError]:
            pass
        super(cls, cls).validateValue(value)

    @classmethod
    def getBytearray(cls, newValue: Any, *args, **kwargs) -> bytes:
        try:
            newValue = ValidationClass.validateInt(newValue)
            return pack('>h', newValue)
        except [TypeError, StructError]:
            super(cls, cls).getBytearray(newValue)


class PLCDWordType(PLCVarType, NoInstantiable):
    NAME: ClassVar[str] = 'DWord'
    BYTES: ClassVar[int] = 4
    BITS: ClassVar[int] = 0

    @classmethod
    def validateValue(cls, value: Any, *args, **kwargs) -> Any:
        try:
            if isinstance(value, bytearray):
                return unpack('>l', value)[0]
            value = ValidationClass.validateInt(value)
            if value in range(-((2**(8*cls.BYTES))//2), (2**(8*cls.BYTES))//2):
                return value
        except [TypeError, StructError]:
            pass
        super(cls, cls).validateValue(value)

    @classmethod
    def getBytearray(cls, newValue: Any, *args, **kwargs) -> bytes:
        try:
            newValue = ValidationClass.validateInt(newValue)
            return pack('>l', newValue)
        except [TypeError, StructError]:
            super(cls, cls).validateValue(newValue)


class PLCIntType(PLCVarType, NoInstantiable):
    NAME: ClassVar[str] = 'Int'
    BYTES: ClassVar[int] = 2
    BITS: ClassVar[int] = 0

    @classmethod
    def validateValue(cls, value: Any, *args, **kwargs) -> Any:
        try:
            if isinstance(value, bytearray):
                return unpack('>h', value)[0]
            value = ValidationClass.validateInt(value)
            if value in range(-((2**(8*cls.BYTES))//2), (2**(8*cls.BYTES))//2):
                return value
        except [TypeError, StructError]:
            pass
        super(cls, cls).validateValue(value)

    @classmethod
    def getBytearray(cls, newValue: Any, *args, **kwargs) -> bytes:
        try:
            newValue = ValidationClass.validateInt(newValue)
            return pack('>h', newValue)
        except [TypeError, StructError]:
            super(cls, cls).validateValue(newValue)


class PLCUIntType(PLCVarType, NoInstantiable):
    NAME: ClassVar[str] = 'UInt'
    BYTES: ClassVar[int] = 2
    BITS: ClassVar[int] = 0

    @classmethod
    def validateValue(cls, value: Any, *args, **kwargs) -> Any:
        try:
            if isinstance(value, bytearray):
                return unpack('>H', value)[0]
            value = ValidationClass.validatePositiveInt(value)
            if value in range(0, (2**(8*cls.BYTES))):
                return value
        except [TypeError, StructError]:
            pass
        super(cls, cls).validateValue(value)

    @classmethod
    def getBytearray(cls, newValue: Any, *args, **kwargs) -> bytes:
        try:
            newValue = ValidationClass.validatePositiveInt(newValue)
            return pack('>H', newValue)
        except [TypeError, StructError]:
            super(cls, cls).validateValue(newValue)


class PLCSIntType(PLCVarType, NoInstantiable):
    NAME: ClassVar[str] = 'SInt'
    BYTES: ClassVar[int] = 1
    BITS: ClassVar[int] = 0

    @classmethod
    def validateValue(cls, value: Any, *args, **kwargs) -> Any:
        try:
            if isinstance(value, bytearray):
                return unpack('>b', value)[0]
            value = ValidationClass.validateInt(value)
            if value in range(-((2**(8*cls.BYTES))//2), (2**(8*cls.BYTES))//2):
                return value
        except [TypeError, StructError]:
            pass
        super(cls, cls).validateValue(value)

    @classmethod
    def getBytearray(cls, newValue: Any, *args, **kwargs) -> bytes:
        try:
            newValue = ValidationClass.validateInt(newValue)
            return pack('>b', newValue)
        except [TypeError, StructError]:
            super(cls, cls).validateValue(newValue)


class PLCUSIntType(PLCVarType, NoInstantiable):
    NAME: ClassVar[str] = 'USInt'
    BYTES: ClassVar[int] = 1
    BITS: ClassVar[int] = 0

    @classmethod
    def validateValue(cls, value: Any, *args, **kwargs) -> Any:
        try:
            if isinstance(value, bytearray):
                return unpack('>B', value)[0]
            value = ValidationClass.validatePositiveInt(value)
            if value in range(0, (2**(8*cls.BYTES))):
                return value
        except [TypeError, StructError]:
            pass
        super(cls, cls).validateValue(value)

    @classmethod
    def getBytearray(cls, newValue: Any, *args, **kwargs) -> bytes:
        try:
            newValue = ValidationClass.validatePositiveInt(newValue)
            return pack('>B', newValue)
        except [TypeError, StructError]:
            super(cls, cls).validateValue(newValue)


class PLCDIntType(PLCVarType, NoInstantiable):
    NAME: ClassVar[str] = 'DInt'
    BYTES: ClassVar[int] = 4
    BITS: ClassVar[int] = 0

    @classmethod
    def validateValue(cls, value: Any, *args, **kwargs) -> Any:
        try:
            if isinstance(value, bytearray):
                return unpack('>l', value)[0]
            value = ValidationClass.validateInt(value)
            if value in range(-((2**(8*cls.BYTES))//2), (2**(8*cls.BYTES))//2):
                return value
        except [TypeError, StructError]:
            pass
        super(cls, cls).validateValue(value)

    @classmethod
    def getBytearray(cls, newValue: Any, *args, **kwargs) -> bytes:
        try:
            newValue = ValidationClass.validateInt(newValue)
            return pack('>l', newValue)
        except [TypeError, StructError]:
            super(cls, cls).validateValue(newValue)


class PLCUDIntType(PLCVarType, NoInstantiable):
    NAME: ClassVar[str] = 'UDInt'
    BYTES: ClassVar[int] = 4
    BITS: ClassVar[int] = 0

    @classmethod
    def validateValue(cls, value: Any, *args, **kwargs) -> Any:
        try:
            if isinstance(value, bytearray):
                return unpack('>L', value)[0]
            value = ValidationClass.validatePositiveInt(value)
            if value in range(0, (2**(8*cls.BYTES))):
                return value
        except [TypeError, StructError]:
            pass
        super(cls, cls).validateValue(value)

    @classmethod
    def getBytearray(cls, newValue: Any, *args, **kwargs) -> bytes:
        try:
            newValue = ValidationClass.validatePositiveInt(newValue)
            return pack('>L', newValue)
        except [TypeError, StructError]:
            super(cls, cls).validateValue(newValue)


class PLCRealType(PLCVarType, NoInstantiable):
    NAME: ClassVar[str] = 'Real'
    BYTES: ClassVar[int] = 4
    BITS: ClassVar[int] = 0

    @classmethod
    def validateValue(cls, value: Any, *args, **kwargs) -> Any:
        try:
            if isinstance(value, bytearray):
                return unpack('>f', value)[0]
            return ValidationClass.validateFloat(value)
        except [TypeError, StructError]:
            pass
        super(cls, cls).validateValue(value)

    @classmethod
    def getBytearray(cls, newValue: Any, *args, **kwargs) -> bytes:
        try:
            newValue = ValidationClass.validateFloat(newValue)
            return pack('>f', newValue)
        except [TypeError, StructError]:
            super(cls, cls).validateValue(newValue)


class PLCLRealType(PLCVarType, NoInstantiable):
    NAME: ClassVar[str] = 'LReal'
    BYTES: ClassVar[int] = 8
    BITS: ClassVar[int] = 0

    @classmethod
    def validateValue(cls, value: Any, *args, **kwargs) -> Any:
        try:
            if isinstance(value, bytearray):
                return unpack('>d', value)[0]
            return ValidationClass.validateFloat(value)
        except [TypeError, StructError]:
            pass
        super(cls, cls).validateValue(value)

    @classmethod
    def getBytearray(cls, newValue: Any, *args, **kwargs) -> bytes:
        try:
            newValue = ValidationClass.validateFloat(newValue)
            return pack('>d', newValue)
        except [TypeError, StructError]:
            super(cls, cls).validateValue(newValue)


class PLCTimeType(PLCVarType, NoInstantiable):
    NAME: ClassVar[str] = 'Time'
    BYTES: ClassVar[int] = 4
    BITS: ClassVar[int] = 0

    @classmethod
    def validateValue(cls, value: Any, *args, **kwargs) -> Any:
        try:
            if isinstance(value, bytearray):
                return unpack('>l', value)[0]
            value = ValidationClass.validateInt(value)
            if value in range(-((2**(8*cls.BYTES))//2), (2**(8*cls.BYTES))//2):
                return time(second= value/1000)
        except [TypeError, StructError]:
            pass
        super(cls, cls).validateValue(value)

    @classmethod
    def getBytearray(cls, newValue: Any, *args, **kwargs) -> bytes:
        try:
            if isinstance(newValue, time):
                newValue = newValue.hour * 360000
                newValue += newValue.minute * 60000
                newValue += newValue.second * 1000
                newValue += newValue.microsecond / 1000
            newValue = ValidationClass.validateInt(newValue)
            return pack('>l', newValue)
        except [TypeError, StructError]:
            super(cls, cls).validateValue(newValue)


class PLCDateType(PLCVarType, NoInstantiable):
    NAME: ClassVar[str] = 'Date'
    BYTES: ClassVar[int] = 2
    BITS: ClassVar[int] = 0

    @classmethod
    def validateValue(cls, value: Any, *args, **kwargs) -> Any:
        try:
            if isinstance(value, bytearray):
                return unpack('>H', value)[0]
            value = ValidationClass.validatePositiveInt(value)
            if value in range(0, (2**(8*cls.BYTES))):
                return date(year= 1990, month= 1, day= 1) + timedelta(days= value)
        except [TypeError, StructError]:
            pass
        super(cls, cls).validateValue(value)

    @classmethod
    def getBytearray(cls, newValue: Any, *args, **kwargs) -> bytes:
        try:
            if isinstance(newValue, date):
                newValue = (newValue - date(year= 1990, month= 1, day= 1)).days
            newValue = ValidationClass.validatePositiveInt(newValue)
            return pack('>H', newValue)
        except [TypeError, StructError]:
            super(cls, cls).validateValue(newValue)


class PLCDTLType(PLCVarType, NoInstantiable):
    ... #TODO


class PLCCharType(PLCVarType, NoInstantiable):
    NAME: ClassVar[str] = 'Char'
    BYTES: ClassVar[int] = 1
    BITS: ClassVar[int] = 0

    @classmethod
    def validateValue(cls, value: Any, *args, **kwargs) -> Any:
        try:
            if isinstance(value, bytearray):
                return chr(unpack('>b', value)[0])
            if isinstance(value, str):
                return value[0]
            return chr(ValidationClass.validateInt(value))
        except [TypeError, StructError]:
            pass
        super(cls, cls).validateValue(value)

    @classmethod
    def getBytearray(cls, newValue: Any, *args, **kwargs) -> bytes:
        try:
            newValue = ValidationClass.validateInt(newValue)
            return pack('>b', newValue)
        except [TypeError, StructError]:
            super(cls, cls).validateValue(newValue)


class PLCStringType(PLCVarType, NoInstantiable):
    ... #TODO


class PLCVarTypesFactory(NoInstantiable):
    TYPES = MappingProxyType({
        PLCBoolType.NAME.upper(): PLCBoolType,
        PLCByteType.NAME.upper(): PLCByteType,
        PLCWordType.NAME.upper(): PLCWordType,
        PLCDWordType.NAME.upper(): PLCDWordType,
        PLCIntType.NAME.upper(): PLCIntType,
        PLCUIntType.NAME.upper(): PLCUIntType,
        PLCSIntType.NAME.upper(): PLCSIntType,
        PLCUSIntType.NAME.upper(): PLCUSIntType,
        PLCDIntType.NAME.upper(): PLCDIntType,
        PLCUDIntType.NAME.upper(): PLCUDIntType,
        PLCRealType.NAME.upper(): PLCRealType,
        PLCLRealType.NAME.upper(): PLCLRealType,
        PLCTimeType.NAME.upper(): PLCTimeType,
        PLCDateType.NAME.upper(): PLCDateType,
        PLCDTLType.NAME.upper(): PLCDTLType,
        PLCCharType.NAME.upper(): PLCCharType,
        PLCStringType.NAME.upper(): PLCStringType,
    })

    @classmethod
    def get(cls, name: str) -> Optional[Type[PLCVarType]]:
        try:
            return cls.TYPES[name.upper()]
        except KeyError:
            raise TypeError(f'"{name}" is not a PLCVarTypes')
