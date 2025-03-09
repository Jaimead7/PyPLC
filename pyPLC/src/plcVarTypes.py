from abc import ABC, abstractmethod
from struct import pack, unpack
from types import MappingProxyType
from typing import Any, ClassVar

from pyUtils import NoInstantiable, ValidationClass


class PLCVarType(ABC):
    NAME: ClassVar[str] = ''
    BYTES: ClassVar[int] = 0
    BITS: ClassVar[int] = 0

    @abstractmethod
    @classmethod
    def validateValue(cls, value: Any, *args, **kwargs) -> Any:
        raise TypeError(f'{value} is not type {cls.NAME}')

    @abstractmethod
    @classmethod
    def getByteArray(cls, newValue: Any, *args, **kwargs) -> bytes:
        ...


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
        finally:
            super.validateValue(value)

    @classmethod
    def getByteArray(cls,
                     newValue: Any,
                     lastValue: bytearray = bytearray([0]),
                     pos: int = 0,
                     *args,
                     **kwargs) -> bytes:
        if ValidationClass.validateBool(newValue):
            mask = int(2 ** pos)
            return pack('>B', mask | int.from_bytes(lastValue, 'big'))
        else:
            mask = int(int(2 ** pos) ^ 255)
            return pack('>B', mask & int.from_bytes(lastValue, 'big'))


class PLCWordType(PLCVarType, NoInstantiable):
    NAME: ClassVar[str] = 'Word'
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
        finally:
            super.validateValue(value)

    @classmethod
    def getByteArray(cls, newValue: Any, *args, **kwargs) -> bytes:
        newValue = ValidationClass.validatePositiveInt(newValue)
        return pack('>H', newValue)


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
        finally:
            super.validateValue(value)

    @classmethod
    def getByteArray(cls, newValue: Any, *args, **kwargs) -> bytes:
        newValue = ValidationClass.validateInt(newValue)
        return pack('>h', newValue)


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
        finally:
            super.validateValue(value)

    @classmethod
    def getByteArray(cls, newValue: Any, *args, **kwargs) -> bytes:
        newValue = ValidationClass.validatePositiveInt(newValue)
        return pack('>H', newValue)


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
        finally:
            super.validateValue(value)

    @classmethod
    def getByteArray(cls, newValue: Any, *args, **kwargs) -> bytes:
        newValue = ValidationClass.validateInt(newValue)
        return pack('>b', newValue)


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
        finally:
            super.validateValue(value)

    @classmethod
    def getByteArray(cls, newValue: Any, *args, **kwargs) -> bytes:
        newValue = ValidationClass.validatePositiveInt(newValue)
        return pack('>B', newValue)


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
        finally:
            super.validateValue(value)

    @classmethod
    def getByteArray(cls, newValue: Any, *args, **kwargs) -> bytes:
        newValue = ValidationClass.validateInt(newValue)
        return pack('>l', newValue)


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
        finally:
            super.validateValue(value)

    @classmethod
    def getByteArray(cls, newValue: Any, *args, **kwargs) -> bytes:
        newValue = ValidationClass.validatePositiveInt(newValue)
        return pack('>L', newValue)


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
        finally:
            super.validateValue(value)

    @classmethod
    def getByteArray(cls, newValue: Any, *args, **kwargs) -> bytes:
        newValue = ValidationClass.validateFloat(newValue)
        return pack('>f', newValue)


class PLCVarTypesFactory(NoInstantiable):
    TYPES = MappingProxyType({
        PLCBoolType.NAME.upper(): PLCBoolType,
        PLCWordType.NAME.upper(): PLCWordType,
        PLCIntType.NAME.upper(): PLCIntType,
        PLCUIntType.NAME.upper(): PLCUIntType,
        PLCSIntType.NAME.upper(): PLCSIntType,
        PLCUSIntType.NAME.upper(): PLCUSIntType,
        PLCDIntType.NAME.upper(): PLCDIntType,
        PLCUDIntType.NAME.upper(): PLCUDIntType,
        PLCRealType.NAME.upper(): PLCRealType,
    })
