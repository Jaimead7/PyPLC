from collections.abc import Callable
from datetime import date, time, timedelta
from struct import error as StructError
from struct import pack, unpack
from typing import Any, ClassVar, NoReturn

from typing_extensions import Self

from .logging import pyplc_logger


class PLCVarType():
    NAME: ClassVar[str] = ''
    BYTES: ClassVar[int] = 0
    BITS: ClassVar[int] = 0

    def __new__(cls) -> Self:
        msg: str = f'"{cls.__name__}" is not instantiable.'
        pyplc_logger.critical(msg)
        raise RuntimeError(msg)

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self.NAME}, {self.BYTES}, {self.BITS})'

    def __str__(self) -> str:
        return self.NAME

    @classmethod
    def _raise_value_error(cls, value: Any) -> NoReturn:
        msg: str = f'{value} is not type {cls.NAME}.'
        pyplc_logger.error(msg)
        raise ValueError(msg)

    @classmethod
    def validate_value(cls, value: Any, *args, **kwargs) -> Any:
        msg: str = f'{cls.__name__} has no validate_value method.'
        pyplc_logger.critical(msg)
        raise NotImplementedError(msg)

    @classmethod
    def get_bytes_array(cls, value: Any, *args, **kwargs) -> bytearray:
        msg: str = f'{cls.__name__} has no get_bytes_array method.'
        pyplc_logger.critical(msg)
        raise NotImplementedError(msg)


class PLCVarTypesReg():
    _plc_var_types: ClassVar[dict[str, type[PLCVarType]]] = {}

    def __new__(cls) -> Self:
        msg: str = f'"{cls.__name__}" is not instantiable.'
        pyplc_logger.critical(msg)
        raise RuntimeError(msg)

    @staticmethod
    def _parse_name(name: str) -> str:
        return name.upper()

    @classmethod
    def register(cls, name: str) -> Callable[[type[PLCVarType]], type[PLCVarType]]:
        name = cls._parse_name(name)
        def decorator(func: type[PLCVarType]) -> type[PLCVarType]:
            if name in cls._plc_var_types:
                pyplc_logger.warning(f'PLCVarType "{name}" is already registered. It will be overwritten.')
            cls._plc_var_types[name] = func
            return func
        return decorator

    @classmethod
    def unregister(cls, name: str) -> None:
        name = cls._parse_name(name)
        cls._plc_var_types.pop(name, None)

    @classmethod
    def get(cls, name: str) -> type[PLCVarType]:
        name = cls._parse_name(name)
        var_type: type[PLCVarType] | None = cls._plc_var_types.get(name, None)
        if var_type is None:
            msg: str = f'"{name}" is not a valid PLCVarType.'
            pyplc_logger.error(msg)
            raise ValueError(msg)
        return var_type

    @classmethod
    def list(cls) -> list[str]:
        return sorted(cls._plc_var_types.keys())

    @classmethod
    def clear(cls) -> None:
        cls._plc_var_types.clear()


@PLCVarTypesReg.register(name= 'BOOL')
class PLCBoolType(PLCVarType):
    NAME: ClassVar[str] = 'Bool'
    BYTES: ClassVar[int] = 0
    BITS: ClassVar[int] = 1

    @classmethod
    def validate_value(cls, value: Any, pos: int = 0, *args, **kwargs) -> bool:
        try:
            if isinstance(value, bytearray):
                return int.from_bytes(value, 'big') & 2 ** pos != 0
            return bool(value)
        except (ValueError, TypeError, StructError):
            pass
        cls._raise_value_error(value)

    @classmethod
    def get_bytes_array(
        cls,
        value: Any,
        last_value: bytearray = bytearray([0]),
        pos: int = 0,
        *args,
        **kwargs
    ) -> bytearray:
        try:
            if bool(value):
                mask = int(2 ** pos)
                return bytearray(pack('>B', mask | int.from_bytes(last_value, 'big')))
            else:
                mask = int(int(2 ** pos) ^ 255)
                return bytearray(pack('>B', mask & int.from_bytes(last_value, 'big')))
        except (ValueError, TypeError, StructError):
            pass
        cls._raise_value_error(value)


@PLCVarTypesReg.register(name= 'BYTE')
class PLCByteType(PLCVarType):
    NAME: ClassVar[str] = 'Byte'
    BYTES: ClassVar[int] = 1
    BITS: ClassVar[int] = 0

    @classmethod
    def validate_value(cls, value: Any, *args, **kwargs) -> Any:
        try:
            if isinstance(value, bytearray):
                return unpack('>b', value)[0]
            value = int(value)
            if value not in range(-((2**(8*cls.BYTES))//2), (2**(8*cls.BYTES))//2):
                raise ValueError
            return value
        except (ValueError, TypeError, StructError):
            pass
        cls._raise_value_error(value)

    @classmethod
    def get_bytes_array(cls, value: Any, *args, **kwargs) -> bytearray:
        try:
            value = int(value)
            return bytearray(pack('>b', value))
        except (ValueError, TypeError, StructError):
            pass
        cls._raise_value_error(value)


@PLCVarTypesReg.register(name= 'WORD')
class PLCWordType(PLCVarType):
    NAME: ClassVar[str] = 'Word'
    BYTES: ClassVar[int] = 2
    BITS: ClassVar[int] = 0

    @classmethod
    def validate_value(cls, value: Any, *args, **kwargs) -> Any:
        try:
            if isinstance(value, bytearray):
                return unpack('>h', value)[0]
            value = int(value)
            if value not in range(-((2**(8*cls.BYTES))//2), (2**(8*cls.BYTES))//2):
                raise ValueError
            return value
        except (ValueError, TypeError, StructError):
            pass
        cls._raise_value_error(value)

    @classmethod
    def get_bytes_array(cls, value: Any, *args, **kwargs) -> bytearray:
        try:
            value = int(value)
            return bytearray(pack('>h', value))
        except (ValueError, TypeError, StructError):
            pass
        cls._raise_value_error(value)


@PLCVarTypesReg.register(name= 'DWORD')
class PLCDWordType(PLCVarType):
    NAME: ClassVar[str] = 'DWord'
    BYTES: ClassVar[int] = 4
    BITS: ClassVar[int] = 0

    @classmethod
    def validate_value(cls, value: Any, *args, **kwargs) -> Any:
        try:
            if isinstance(value, bytearray):
                return unpack('>l', value)[0]
            value = int(value)
            if value not in range(-((2**(8*cls.BYTES))//2), (2**(8*cls.BYTES))//2):
                raise ValueError
            return value
        except (ValueError, TypeError, StructError):
            pass
        cls._raise_value_error(value)

    @classmethod
    def get_bytes_array(cls, value: Any, *args, **kwargs) -> bytearray:
        try:
            value = int(value)
            return bytearray(pack('>l', value))
        except (ValueError, TypeError, StructError):
            pass
        cls._raise_value_error(value)


@PLCVarTypesReg.register(name= 'INT')
class PLCIntType(PLCVarType):
    NAME: ClassVar[str] = 'Int'
    BYTES: ClassVar[int] = 2
    BITS: ClassVar[int] = 0

    @classmethod
    def validate_value(cls, value: Any, *args, **kwargs) -> Any:
        try:
            if isinstance(value, bytearray):
                return unpack('>h', value)[0]
            value = int(value)
            if value not in range(-((2**(8*cls.BYTES))//2), (2**(8*cls.BYTES))//2):
                raise ValueError
            return value
        except (ValueError, TypeError, StructError):
            pass
        cls._raise_value_error(value)

    @classmethod
    def get_bytes_array(cls, value: Any, *args, **kwargs) -> bytearray:
        try:
            value = int(value)
            return bytearray(pack('>h', value))
        except (ValueError, TypeError, StructError):
            pass
        cls._raise_value_error(value)


@PLCVarTypesReg.register(name= 'UINT')
class PLCUIntType(PLCVarType):
    NAME: ClassVar[str] = 'UInt'
    BYTES: ClassVar[int] = 2
    BITS: ClassVar[int] = 0

    @classmethod
    def validate_value(cls, value: Any, *args, **kwargs) -> Any:
        try:
            if isinstance(value, bytearray):
                return unpack('>H', value)[0]
            value = int(value)
            if value < 0:
                raise ValueError
            if value not in range(0, (2**(8*cls.BYTES))):
                raise ValueError
            return value
        except (ValueError, TypeError, StructError):
            pass
        cls._raise_value_error(value)

    @classmethod
    def get_bytes_array(cls, value: Any, *args, **kwargs) -> bytearray:
        try:
            value = int(value)
            if value < 0:
                raise ValueError
            return bytearray(pack('>H', value))
        except (ValueError, TypeError, StructError):
            pass
        cls._raise_value_error(value)


@PLCVarTypesReg.register(name= 'SINT')
class PLCSIntType(PLCVarType):
    NAME: ClassVar[str] = 'SInt'
    BYTES: ClassVar[int] = 1
    BITS: ClassVar[int] = 0

    @classmethod
    def validate_value(cls, value: Any, *args, **kwargs) -> Any:
        try:
            if isinstance(value, bytearray):
                return unpack('>b', value)[0]
            value = int(value)
            if value not in range(-((2**(8*cls.BYTES))//2), (2**(8*cls.BYTES))//2):
                raise ValueError
            return value
        except (ValueError, TypeError, StructError):
            pass
        cls._raise_value_error(value)

    @classmethod
    def get_bytes_array(cls, value: Any, *args, **kwargs) -> bytearray:
        try:
            value = int(value)
            return bytearray(pack('>b', value))
        except (ValueError, TypeError, StructError):
            pass
        cls._raise_value_error(value)


@PLCVarTypesReg.register(name= 'USINT')
class PLCUSIntType(PLCVarType):
    NAME: ClassVar[str] = 'USInt'
    BYTES: ClassVar[int] = 1
    BITS: ClassVar[int] = 0

    @classmethod
    def validate_value(cls, value: Any, *args, **kwargs) -> Any:
        try:
            if isinstance(value, bytearray):
                return unpack('>B', value)[0]
            value = int(value)
            if value < 0:
                raise ValueError
            if value not in range(0, (2**(8*cls.BYTES))):
                raise ValueError
            return value
        except (ValueError, TypeError, StructError):
            pass
        cls._raise_value_error(value)

    @classmethod
    def get_bytes_array(cls, value: Any, *args, **kwargs) -> bytearray:
        try:
            value = int(value)
            if value < 0:
                raise ValueError
            return bytearray(pack('>B', value))
        except (ValueError, TypeError, StructError):
            pass
        cls._raise_value_error(value)


@PLCVarTypesReg.register(name= 'DINT')
class PLCDIntType(PLCVarType):
    NAME: ClassVar[str] = 'DInt'
    BYTES: ClassVar[int] = 4
    BITS: ClassVar[int] = 0

    @classmethod
    def validate_value(cls, value: Any, *args, **kwargs) -> Any:
        try:
            if isinstance(value, bytearray):
                return unpack('>l', value)[0]
            value = int(value)
            if value not in range(-((2**(8*cls.BYTES))//2), (2**(8*cls.BYTES))//2):
                raise ValueError
            return value
        except (ValueError, TypeError, StructError):
            pass
        cls._raise_value_error(value)

    @classmethod
    def get_bytes_array(cls, value: Any, *args, **kwargs) -> bytearray:
        try:
            value = int(value)
            return bytearray(pack('>l', value))
        except (ValueError, TypeError, StructError):
            pass
        cls._raise_value_error(value)


@PLCVarTypesReg.register(name= 'UDINT')
class PLCUDIntType(PLCVarType):
    NAME: ClassVar[str] = 'UDInt'
    BYTES: ClassVar[int] = 4
    BITS: ClassVar[int] = 0

    @classmethod
    def validate_value(cls, value: Any, *args, **kwargs) -> Any:
        try:
            if isinstance(value, bytearray):
                return unpack('>L', value)[0]
            value = int(value)
            if value < 0:
                raise ValueError
            if value not in range(0, (2**(8*cls.BYTES))):
                raise ValueError
            return value
        except (ValueError, TypeError, StructError):
            pass
        cls._raise_value_error(value)

    @classmethod
    def get_bytes_array(cls, value: Any, *args, **kwargs) -> bytearray:
        try:
            value = int(value)
            if value < 0:
                raise ValueError
            return bytearray(pack('>L', value))
        except (ValueError, TypeError, StructError):
            pass
        cls._raise_value_error(value)


@PLCVarTypesReg.register(name= 'REAL')
class PLCRealType(PLCVarType):
    NAME: ClassVar[str] = 'Real'
    BYTES: ClassVar[int] = 4
    BITS: ClassVar[int] = 0

    @classmethod
    def validate_value(cls, value: Any, *args, **kwargs) -> Any:
        try:
            if isinstance(value, bytearray):
                return unpack('>f', value)[0]
            return float(value)
        except (ValueError, TypeError, StructError):
            pass
        cls._raise_value_error(value)

    @classmethod
    def get_bytes_array(cls, value: Any, *args, **kwargs) -> bytearray:
        try:
            value = float(value)
            return bytearray(pack('>f', value))
        except (ValueError, TypeError, StructError):
            pass
        cls._raise_value_error(value)


@PLCVarTypesReg.register(name= 'LREAL')
class PLCLRealType(PLCVarType):
    NAME: ClassVar[str] = 'LReal'
    BYTES: ClassVar[int] = 8
    BITS: ClassVar[int] = 0

    @classmethod
    def validate_value(cls, value: Any, *args, **kwargs) -> Any:
        try:
            if isinstance(value, bytearray):
                return unpack('>d', value)[0]
            return float(value)
        except (ValueError, TypeError, StructError):
            pass
        cls._raise_value_error(value)

    @classmethod
    def get_bytes_array(cls, value: Any, *args, **kwargs) -> bytearray:
        try:
            value = float(value)
            return bytearray(pack('>d', value))
        except (ValueError, TypeError, StructError):
            pass
        cls._raise_value_error(value)


@PLCVarTypesReg.register(name= 'TIME')
class PLCTimeType(PLCVarType):
    NAME: ClassVar[str] = 'Time'
    BYTES: ClassVar[int] = 4
    BITS: ClassVar[int] = 0

    @classmethod
    def validate_value(cls, value: Any, *args, **kwargs) -> Any:
        try:
            if isinstance(value, bytearray):
                return unpack('>l', value)[0]
            value = int(value)
            if value not in range(-((2**(8*cls.BYTES))//2), (2**(8*cls.BYTES))//2):
                raise ValueError
            return time(second= value/1000)
        except (ValueError, TypeError, StructError):
            pass
        cls._raise_value_error(value)

    @classmethod
    def get_bytes_array(cls, value: Any, *args, **kwargs) -> bytearray:
        try:
            if isinstance(value, time):
                value = value.hour * 360000
                value += value.minute * 60000
                value += value.second * 1000
                value += value.microsecond / 1000
            value = int(value)
            return bytearray(pack('>l', value))
        except (ValueError, TypeError, StructError):
            pass
        cls._raise_value_error(value)


@PLCVarTypesReg.register(name= 'DATE')
class PLCDateType(PLCVarType):
    NAME: ClassVar[str] = 'Date'
    BYTES: ClassVar[int] = 2
    BITS: ClassVar[int] = 0

    @classmethod
    def validate_value(cls, value: Any, *args, **kwargs) -> Any:
        try:
            if isinstance(value, bytearray):
                return unpack('>H', value)[0]
            value = int(value)
            if value < 0:
                raise ValueError
            if value not in range(0, (2**(8*cls.BYTES))):
                raise ValueError
            return date(year= 1990, month= 1, day= 1) + timedelta(days= value)
        except (ValueError, TypeError, StructError):
            pass
        cls._raise_value_error(value)

    @classmethod
    def get_bytes_array(cls, value: Any, *args, **kwargs) -> bytearray:
        try:
            if isinstance(value, date):
                value = (value - date(year= 1990, month= 1, day= 1)).days
            value = int(value)
            if value < 0:
                raise ValueError
            return bytearray(pack('>H', value))
        except (ValueError, TypeError, StructError):
            pass
        cls._raise_value_error(value)


@PLCVarTypesReg.register(name= 'DTL')
class PLCDTLType(PLCVarType):
    ... #TODO


@PLCVarTypesReg.register(name= 'CHAR')
class PLCCharType(PLCVarType):
    NAME: ClassVar[str] = 'Char'
    BYTES: ClassVar[int] = 1
    BITS: ClassVar[int] = 0

    @classmethod
    def validate_value(cls, value: Any, *args, **kwargs) -> Any:
        try:
            if isinstance(value, bytearray):
                return chr(unpack('>b', value)[0])
            if isinstance(value, str):
                return value[0]
            return chr(int(value))
        except (ValueError, TypeError, StructError):
            pass
        cls._raise_value_error(value)

    @classmethod
    def get_bytes_array(cls, value: Any, *args, **kwargs) -> bytearray:
        try:
            value = int(value)
            return bytearray(pack('>b', value))
        except (ValueError, TypeError, StructError):
            pass
        cls._raise_value_error(value)


@PLCVarTypesReg.register(name= 'STRING')
class PLCStringType(PLCVarType):
    ... #TODO
