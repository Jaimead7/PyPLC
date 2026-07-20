import re
from collections.abc import Callable
from datetime import date, time, timedelta
from struct import error as StructError
from struct import pack, unpack
from typing import Any, ClassVar, NoReturn

from typing_extensions import Self

from .logs import pyplc_logger


class PLCVarType:
    def __init__(self, *args, **kwargs) -> None:
        pass
    
    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self.NAME}, {self.BYTES}, {self.BITS})'

    def __str__(self) -> str:
        return self.NAME

    def __eq__(self, value: object) -> bool:
        return type(self) == type(value)

    @property
    def NAME(self) -> str:
        return ''

    @property
    def BYTES(self) -> int:
        return 0

    @property
    def BITS(self) -> int:
        return 0

    def _raise_value_error(self, value: Any) -> NoReturn:
        msg: str = f'{value} is not type {self.NAME}.'
        pyplc_logger.error(msg)
        raise ValueError(msg)

    def validate_value(self, value: Any, *args, **kwargs) -> Any:
        msg: str = f'{self.__class__.__name__} has no validate_value method.'
        pyplc_logger.critical(msg)
        raise NotImplementedError(msg)

    def get_bytes_array(self, value: Any, *args, **kwargs) -> bytearray:
        msg: str = f'{self.__class__.__name__} has no get_bytes_array method.'
        pyplc_logger.critical(msg)
        raise NotImplementedError(msg)


class PLCVarTypesReg:
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
    def get(cls, name: str, *args, **kwargs) -> PLCVarType | None:
        name = cls._parse_name(name)
        var_type: type[PLCVarType] | None = cls._plc_var_types.get(name, None)
        if var_type is not None:
            return var_type()
        try:
            if name.startswith('ARRAYOF'):
                res: list[str | Any] = re.split(r'(\d+)', name)
                new_name: str = res[0]
                lenght: int = int(res[1])
                var_type = cls._plc_var_types.get(new_name, None)
                if var_type is not None:
                    return var_type(lenght)
        except Exception:
            pass
        msg: str = f'"{name}" is not a valid PLCVarType.'
        pyplc_logger.error(msg)
        return None

    @classmethod
    def list(cls) -> list[str]:
        return sorted(cls._plc_var_types.keys())

    @classmethod
    def clear(cls) -> None:
        cls._plc_var_types.clear()


@PLCVarTypesReg.register(name= 'BOOL')
class PLCBoolType(PLCVarType):
    @property
    def NAME(self) -> str:
        return 'Bool'

    @property
    def BYTES(self) -> int:
        return 0

    @property
    def BITS(self) -> int:
        return 1

    def validate_value(self, value: Any, pos: int = 0, *args, **kwargs) -> bool:
        try:
            if isinstance(value, bytearray):
                return int.from_bytes(value, 'big') & 2 ** pos != 0
            return bool(value)
        except (ValueError, TypeError, StructError, OverflowError):
            pass
        self._raise_value_error(value)

    def get_bytes_array(
        self,
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
        except (ValueError, TypeError, StructError, OverflowError):
            pass
        self._raise_value_error(value)


@PLCVarTypesReg.register(name= 'BYTE')
class PLCByteType(PLCVarType):
    @property
    def NAME(self) -> str:
        return 'Byte'

    @property
    def BYTES(self) -> int:
        return 1

    @property
    def BITS(self) -> int:
        return 0

    def validate_value(self, value: Any, *args, **kwargs) -> Any:
        try:
            if isinstance(value, bytearray):
                return unpack('>b', value)[0]
            value = int(value)
            if value not in range(-((2**(8*self.BYTES))//2), (2**(8*self.BYTES))//2):
                raise ValueError
            return value
        except (ValueError, TypeError, StructError, OverflowError):
            pass
        self._raise_value_error(value)

    def get_bytes_array(self, value: Any, *args, **kwargs) -> bytearray:
        try:
            value = int(value)
            return bytearray(pack('>b', value))
        except (ValueError, TypeError, StructError, OverflowError):
            pass
        self._raise_value_error(value)


@PLCVarTypesReg.register(name= 'WORD')
class PLCWordType(PLCVarType):
    @property
    def NAME(self) -> str:
        return 'Word'

    @property
    def BYTES(self) -> int:
        return 2

    @property
    def BITS(self) -> int:
        return 0

    def validate_value(self, value: Any, *args, **kwargs) -> Any:
        try:
            if isinstance(value, bytearray):
                return unpack('>h', value)[0]
            value = int(value)
            if value not in range(-((2**(8*self.BYTES))//2), (2**(8*self.BYTES))//2):
                raise ValueError
            return value
        except (ValueError, TypeError, StructError, OverflowError):
            pass
        self._raise_value_error(value)

    def get_bytes_array(self, value: Any, *args, **kwargs) -> bytearray:
        try:
            value = int(value)
            return bytearray(pack('>h', value))
        except (ValueError, TypeError, StructError, OverflowError):
            pass
        self._raise_value_error(value)


@PLCVarTypesReg.register(name= 'DWORD')
class PLCDWordType(PLCVarType):
    @property
    def NAME(self) -> str:
        return 'DWord'

    @property
    def BYTES(self) -> int:
        return 4

    @property
    def BITS(self) -> int:
        return 0

    def validate_value(self, value: Any, *args, **kwargs) -> Any:
        try:
            if isinstance(value, bytearray):
                return unpack('>l', value)[0]
            value = int(value)
            if value not in range(-((2**(8*self.BYTES))//2), (2**(8*self.BYTES))//2):
                raise ValueError
            return value
        except (ValueError, TypeError, StructError, OverflowError):
            pass
        self._raise_value_error(value)

    def get_bytes_array(self, value: Any, *args, **kwargs) -> bytearray:
        try:
            value = int(value)
            return bytearray(pack('>l', value))
        except (ValueError, TypeError, StructError, OverflowError):
            pass
        self._raise_value_error(value)


@PLCVarTypesReg.register(name= 'INT')
class PLCIntType(PLCVarType):
    @property
    def NAME(self) -> str:
        return 'Int'

    @property
    def BYTES(self) -> int:
        return 2

    @property
    def BITS(self) -> int:
        return 0

    def validate_value(self, value: Any, *args, **kwargs) -> Any:
        try:
            if isinstance(value, bytearray):
                return unpack('>h', value)[0]
            value = int(value)
            if value not in range(-((2**(8*self.BYTES))//2), (2**(8*self.BYTES))//2):
                raise ValueError
            return value
        except (ValueError, TypeError, StructError, OverflowError):
            pass
        self._raise_value_error(value)

    def get_bytes_array(self, value: Any, *args, **kwargs) -> bytearray:
        try:
            value = int(value)
            return bytearray(pack('>h', value))
        except (ValueError, TypeError, StructError, OverflowError):
            pass
        self._raise_value_error(value)


@PLCVarTypesReg.register(name= 'UINT')
class PLCUIntType(PLCVarType):
    @property
    def NAME(self) -> str:
        return 'UInt'

    @property
    def BYTES(self) -> int:
        return 2

    @property
    def BITS(self) -> int:
        return 0

    def validate_value(self, value: Any, *args, **kwargs) -> Any:
        try:
            if isinstance(value, bytearray):
                return unpack('>H', value)[0]
            value = int(value)
            if value < 0:
                raise ValueError
            if value not in range(0, (2**(8*self.BYTES))):
                raise ValueError
            return value
        except (ValueError, TypeError, StructError, OverflowError):
            pass
        self._raise_value_error(value)

    def get_bytes_array(self, value: Any, *args, **kwargs) -> bytearray:
        try:
            value = int(value)
            if value < 0:
                raise ValueError
            return bytearray(pack('>H', value))
        except (ValueError, TypeError, StructError, OverflowError):
            pass
        self._raise_value_error(value)


@PLCVarTypesReg.register(name= 'SINT')
class PLCSIntType(PLCVarType):
    @property
    def NAME(self) -> str:
        return 'SInt'

    @property
    def BYTES(self) -> int:
        return 1

    @property
    def BITS(self) -> int:
        return 0

    def validate_value(self, value: Any, *args, **kwargs) -> Any:
        try:
            if isinstance(value, bytearray):
                return unpack('>b', value)[0]
            value = int(value)
            if value not in range(-((2**(8*self.BYTES))//2), (2**(8*self.BYTES))//2):
                raise ValueError
            return value
        except (ValueError, TypeError, StructError, OverflowError):
            pass
        self._raise_value_error(value)

    def get_bytes_array(self, value: Any, *args, **kwargs) -> bytearray:
        try:
            value = int(value)
            return bytearray(pack('>b', value))
        except (ValueError, TypeError, StructError, OverflowError):
            pass
        self._raise_value_error(value)


@PLCVarTypesReg.register(name= 'USINT')
class PLCUSIntType(PLCVarType):
    @property
    def NAME(self) -> str:
        return 'USInt'

    @property
    def BYTES(self) -> int:
        return 1

    @property
    def BITS(self) -> int:
        return 0

    def validate_value(self, value: Any, *args, **kwargs) -> Any:
        try:
            if isinstance(value, bytearray):
                return unpack('>B', value)[0]
            value = int(value)
            if value < 0:
                raise ValueError
            if value not in range(0, (2**(8*self.BYTES))):
                raise ValueError
            return value
        except (ValueError, TypeError, StructError, OverflowError):
            pass
        self._raise_value_error(value)

    def get_bytes_array(self, value: Any, *args, **kwargs) -> bytearray:
        try:
            value = int(value)
            if value < 0:
                raise ValueError
            return bytearray(pack('>B', value))
        except (ValueError, TypeError, StructError, OverflowError):
            pass
        self._raise_value_error(value)


@PLCVarTypesReg.register(name= 'DINT')
class PLCDIntType(PLCVarType):
    @property
    def NAME(self) -> str:
        return 'DInt'

    @property
    def BYTES(self) -> int:
        return 4

    @property
    def BITS(self) -> int:
        return 0

    def validate_value(self, value: Any, *args, **kwargs) -> Any:
        try:
            if isinstance(value, bytearray):
                return unpack('>l', value)[0]
            value = int(value)
            if value not in range(-((2**(8*self.BYTES))//2), (2**(8*self.BYTES))//2):
                raise ValueError
            return value
        except (ValueError, TypeError, StructError, OverflowError):
            pass
        self._raise_value_error(value)

    def get_bytes_array(self, value: Any, *args, **kwargs) -> bytearray:
        try:
            value = int(value)
            return bytearray(pack('>l', value))
        except (ValueError, TypeError, StructError, OverflowError):
            pass
        self._raise_value_error(value)


@PLCVarTypesReg.register(name= 'UDINT')
class PLCUDIntType(PLCVarType):
    @property
    def NAME(self) -> str:
        return 'UDInt'

    @property
    def BYTES(self) -> int:
        return 4

    @property
    def BITS(self) -> int:
        return 0

    def validate_value(self, value: Any, *args, **kwargs) -> Any:
        try:
            if isinstance(value, bytearray):
                return unpack('>L', value)[0]
            value = int(value)
            if value < 0:
                raise ValueError
            if value not in range(0, (2**(8*self.BYTES))):
                raise ValueError
            return value
        except (ValueError, TypeError, StructError, OverflowError):
            pass
        self._raise_value_error(value)

    def get_bytes_array(self, value: Any, *args, **kwargs) -> bytearray:
        try:
            value = int(value)
            if value < 0:
                raise ValueError
            return bytearray(pack('>L', value))
        except (ValueError, TypeError, StructError, OverflowError):
            pass
        self._raise_value_error(value)


@PLCVarTypesReg.register(name= 'REAL')
class PLCRealType(PLCVarType):
    @property
    def NAME(self) -> str:
        return 'Real'

    @property
    def BYTES(self) -> int:
        return 4

    @property
    def BITS(self) -> int:
        return 0

    def validate_value(self, value: Any, *args, **kwargs) -> Any:
        try:
            if isinstance(value, bytearray):
                return unpack('>f', value)[0]
            return float(value)
        except (ValueError, TypeError, StructError, OverflowError):
            pass
        self._raise_value_error(value)

    def get_bytes_array(self, value: Any, *args, **kwargs) -> bytearray:
        try:
            value = float(value)
            return bytearray(pack('>f', value))
        except (ValueError, TypeError, StructError, OverflowError):
            pass
        self._raise_value_error(value)


@PLCVarTypesReg.register(name= 'LREAL')
class PLCLRealType(PLCVarType):
    @property
    def NAME(self) -> str:
        return 'LReal'

    @property
    def BYTES(self) -> int:
        return 8

    @property
    def BITS(self) -> int:
        return 0

    def validate_value(self, value: Any, *args, **kwargs) -> Any:
        try:
            if isinstance(value, bytearray):
                return unpack('>d', value)[0]
            return float(value)
        except (ValueError, TypeError, StructError, OverflowError):
            pass
        self._raise_value_error(value)

    def get_bytes_array(self, value: Any, *args, **kwargs) -> bytearray:
        try:
            value = float(value)
            return bytearray(pack('>d', value))
        except (ValueError, TypeError, StructError, OverflowError):
            pass
        self._raise_value_error(value)


@PLCVarTypesReg.register(name= 'TIME')
class PLCTimeType(PLCVarType):
    @property
    def NAME(self) -> str:
        return 'Time'

    @property
    def BYTES(self) -> int:
        return 4

    @property
    def BITS(self) -> int:
        return 0

    def validate_value(self, value: Any, *args, **kwargs) -> Any:
        try:
            if isinstance(value, bytearray):
                return unpack('>l', value)[0]
            value = int(value)
            if value not in range(-((2**(8*self.BYTES))//2), (2**(8*self.BYTES))//2):
                raise ValueError
            return time(second= value/1000)
        except (ValueError, TypeError, StructError, OverflowError):
            pass
        self._raise_value_error(value)

    def get_bytes_array(self, value: Any, *args, **kwargs) -> bytearray:
        try:
            if isinstance(value, time):
                value = value.hour * 360000
                value += value.minute * 60000
                value += value.second * 1000
                value += value.microsecond / 1000
            value = int(value)
            return bytearray(pack('>l', value))
        except (ValueError, TypeError, StructError, OverflowError):
            pass
        self._raise_value_error(value)


@PLCVarTypesReg.register(name= 'DATE')
class PLCDateType(PLCVarType):
    @property
    def NAME(self) -> str:
        return 'Date'

    @property
    def BYTES(self) -> int:
        return 2

    @property
    def BITS(self) -> int:
        return 0

    def validate_value(self, value: Any, *args, **kwargs) -> Any:
        try:
            if isinstance(value, bytearray):
                return unpack('>H', value)[0]
            value = int(value)
            if value < 0:
                raise ValueError
            if value not in range(0, (2**(8*self.BYTES))):
                raise ValueError
            return date(year= 1990, month= 1, day= 1) + timedelta(days= value)
        except (ValueError, TypeError, StructError, OverflowError):
            pass
        self._raise_value_error(value)

    def get_bytes_array(self, value: Any, *args, **kwargs) -> bytearray:
        try:
            if isinstance(value, date):
                value = (value - date(year= 1990, month= 1, day= 1)).days
            value = int(value)
            if value < 0:
                raise ValueError
            return bytearray(pack('>H', value))
        except (ValueError, TypeError, StructError, OverflowError):
            pass
        self._raise_value_error(value)


@PLCVarTypesReg.register(name= 'DTL')
class PLCDTLType(PLCVarType):
    ... #TODO


@PLCVarTypesReg.register(name= 'CHAR')
class PLCCharType(PLCVarType):
    @property
    def NAME(self) -> str:
        return 'Char'

    @property
    def BYTES(self) -> int:
        return 1

    @property
    def BITS(self) -> int:
        return 0

    def validate_value(self, value: Any, *args, **kwargs) -> Any:
        try:
            if isinstance(value, bytearray):
                return chr(unpack('>b', value)[0])
            if isinstance(value, str):
                return value[0]
        except (ValueError, TypeError, StructError, OverflowError):
            pass
        self._raise_value_error(value)

    def get_bytes_array(self, value: Any, *args, **kwargs) -> bytearray:
        try:
            value = str(value)
            return bytearray(pack('>b', value))
        except (ValueError, TypeError, StructError, OverflowError):
            pass
        self._raise_value_error(value)


@PLCVarTypesReg.register(name= 'ARRAYOFCHAR')
class PLCArrayOfChar(PLCVarType):
    def __init__(self, lenght: int = 1, *args, **kwargs) -> None:
        self.length: int = lenght

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self.NAME}, {self.BYTES}, {self.BITS}, {self.length})'

    @property
    def NAME(self) -> str:
        return f'ArrayOfChar{self.length}'

    @property
    def BYTES(self) -> int:
        return 1 * self.length

    @property
    def BITS(self) -> int:
        return 0

    def validate_value(self, value: Any, *args, **kwargs) -> Any:
        try:
            if isinstance(value, bytearray):
                return value.decode('utf-8').strip('\x00').strip()[:self.length]
            if isinstance(value, str):
                return value.strip()[:self.length]
        except (ValueError, TypeError, StructError, OverflowError, UnicodeDecodeError):
            pass
        self._raise_value_error(value)

    def get_bytes_array(self, value: Any, *args, **kwargs) -> bytearray:
        try:
            value_str: str = str(value)
            encoded: bytes = value_str.encode('utf-8')[:self.length]
            if len(encoded) < self.length:
                encoded += b'\x20' * (self.length - len(encoded))
            return bytearray(encoded)
        except (ValueError, TypeError, StructError, OverflowError):
            pass
        self._raise_value_error(value)


@PLCVarTypesReg.register(name= 'STRING')
class PLCStringType(PLCVarType):
    ... #TODO
