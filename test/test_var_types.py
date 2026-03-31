from struct import error as StructError

from pytest import mark, raises

from pyPLC.var_types import *


class TestPLCVarTypesReg:
    #TODO:
    ...


class TestPLCBoolType:
    @mark.parametrize(
        'name',
        [
            'bool',
            'BoOl',
            'BOOL',
        ]
    )
    def test_factory(self, name: str) -> None:
        assert PLCVarTypesReg.get(name) == PLCBoolType

    @mark.parametrize(
        'byte, pos, expected',
        [
            (bytearray([5]), 2, True),
            (bytearray([5]), 1, False),
            (bytearray([77]), 6, True),
            (bytearray([255]), 0, True),
            (bytearray([255]), 7, True),
            (bytearray([1, 0]), 8, True),
            (True, 0, True),
            (1, 0, True),
            ('True', 0, True),
            (False, 0, False),
            (0, 0, False),
            ('False', 0, True),  #CHECK: Maybe an unexpected behaviour
            (5, 0, True),
        ]
    )
    def test_validate_value(self, byte: Any, pos: int, expected: bool) -> None:
        assert PLCBoolType.validate_value(byte, pos) == expected

    @mark.parametrize('byte, pos, error', [])
    def test_validate_value_errors(
        self,
        byte: Any,
        pos: int,
        error: type[BaseException]
    ) -> None:
        with raises(error):
            PLCBoolType.validate_value(byte, pos)

    @mark.parametrize(
        'new_value, last_value, pos, expected',
        [
            (False, bytearray([5]), 2, bytearray([1])),
            (True, bytearray([5]), 2, bytearray([5])),
            (0, bytearray([5]), 2, bytearray([1])),
            (1, bytearray([5]), 2, bytearray([5])),
            ('False', bytearray([5]), 2, bytearray([5])),  #CHECK: Maybe an unexpected behaviour
            ('True', bytearray([5]), 2, bytearray([5])),
            (5, bytearray([5]), 1, bytearray([7])),
        ]
    )
    def test_get_bytes_array(
        self,
        new_value: Any,
        last_value: bytearray,
        pos: int,
        expected: bytearray
    ) -> None:
        assert PLCBoolType.get_bytes_array(new_value, last_value, pos) == expected

    @mark.parametrize(
        'new_value, last_value, pos, error',
        [
            (True, bytearray([1, 0]), 7, ValueError),
        ]
    )
    def test_get_bytes_array_errors(
        self,
        new_value: Any,
        last_value: bytearray,
        pos: int,
        error: type[BaseException]
    ) -> None:
        with raises(error):
            PLCBoolType.get_bytes_array(new_value, last_value, pos)


class TestPLCByteType:
    @mark.parametrize(
        'name',
        [
            'byte',
            'ByTe',
            'BYTE',
        ]
    )
    def test_factory(self, name: str) -> None:
        assert PLCVarTypesReg.get(name) == PLCByteType

    @mark.parametrize(
        'byte, expected',
        [
            (bytearray([5]), 5),
            (bytearray([127]), 127),
            (bytearray([128]), -128),
            (bytearray([200]), -56),
            (5, 5),
            (-5, -5),
            ('5', 5),
            ('-5', -5),
        ]
    )
    def test_validate_value(self, byte: Any, expected: bool) -> None:
        assert PLCByteType.validate_value(byte) == expected

    @mark.parametrize(
        'byte, error',
        [
            (128, ValueError),
            (-129, ValueError),
            (bytearray([1, 0]), ValueError),
        ]
    )
    def test_validate_value_errors(self, byte: Any, error: type[BaseException]) -> None:
        with raises(error):
            PLCByteType.validate_value(byte)

    @mark.parametrize(
        'new_value, expected',
        [
            (5, bytearray([5])),
            (127, bytearray([127])),
            (-128, bytearray([128])),
            (-56, bytearray([200])),
        ]
    )
    def test_get_bytes_array(self, new_value: Any, expected: bytearray) -> None:
        assert PLCByteType.get_bytes_array(new_value) == expected

    @mark.parametrize(
        'new_value, error',
        [
            (128, ValueError),
            (-129, ValueError),
        ]
    )
    def test_get_bytes_array_errors(
        self,
        new_value: Any,
        error: type[BaseException]
    ) -> None:
        with raises(error):
            PLCByteType.get_bytes_array(new_value)


class TestPLCWordType:
    @mark.parametrize(
        'name',
        [
            'word',
            'wOrD',
            'WORD',
        ]
    )
    def test_factory(self, name: str) -> None:
        assert PLCVarTypesReg.get(name) == PLCWordType

    @mark.parametrize(
        'byte, expected',
        [
            (bytearray([0, 5]), 5),
            (bytearray([127, 255]), 32767),
            (bytearray([128, 0]), -32768),
            (bytearray([146, 36]), -28124),
            (32767, 32767),
            (-32768, -32768),
            ('32767', 32767),
            ('-32768', -32768),
        ]
    )
    def test_validate_value(self, byte: Any, expected: bool) -> None:
        assert PLCWordType.validate_value(byte) == expected

    @mark.parametrize(
        'byte, error',
        [
            (bytearray([5]), ValueError),
            (32768, ValueError),
            (-32769, ValueError),
            (bytearray([1, 0, 0]), ValueError),
        ]
    )
    def test_validate_value_errors(self, byte: Any, error: type[BaseException]) -> None:
        with raises(error):
            PLCWordType.validate_value(byte)

    @mark.parametrize(
        'new_value, expected',
        [
            (5, bytearray([0, 5])),
            (32767, bytearray([127, 255])),
            (-32768, bytearray([128, 0])),
            (-28124, bytearray([146, 36])),
        ]
    )
    def test_get_bytes_array(self, new_value: Any, expected: bytearray) -> None:
        assert PLCWordType.get_bytes_array(new_value) == expected

    @mark.parametrize(
        'new_value, error',
        [
            (32768, ValueError),
            (-32769, ValueError),
        ]
    )
    def test_get_bytes_array_errors(
        self,
        new_value: Any,
        error: type[BaseException]
    ) -> None:
        with raises(error):
            PLCWordType.get_bytes_array(new_value)


class TestPLCDWordType:
    @mark.parametrize(
        'name',
        [
            'dword',
            'DwOrD',
            'DWORD',
        ]
    )
    def test_factory(self, name: str) -> None:
        assert PLCVarTypesReg.get(name) == PLCDWordType

    @mark.parametrize(
        'byte, expected',
        [
            (bytearray([0, 0, 0, 5]), 5),
            (bytearray([127, 255, 255, 255]), 2147483647),
            (bytearray([128, 0, 0, 0]), -2147483648),
            (bytearray([146, 0, 36, 0]), -1845484544),
            (2147483647, 2147483647),
            (-2147483648, -2147483648),
            ('2147483647', 2147483647),
            ('-2147483648', -2147483648),
        ]
    )
    def test_validate_value(self, byte: Any, expected: bool) -> None:
        assert PLCDWordType.validate_value(byte) == expected

    @mark.parametrize(
        'byte, error',
        [
            (bytearray([0, 0, 5]), ValueError),
            (2147483648, ValueError),
            (-2147483649, ValueError),
            (bytearray([1, 0, 0, 0, 0]), ValueError),
        ]
    )
    def test_validate_value_errors(self, byte: Any, error: type[BaseException]) -> None:
        with raises(error):
            PLCDWordType.validate_value(byte)

    @mark.parametrize(
        'new_value, expected',
        [
            (5, bytearray([0, 0, 0, 5])),
            (2147483647, bytearray([127, 255, 255, 255])),
            (-2147483648, bytearray([128, 0, 0, 0])),
            (-1845484544, bytearray([146, 0, 36, 0])),
        ]
    )
    def test_get_bytes_array(self, new_value: Any, expected: bytearray) -> None:
        assert PLCDWordType.get_bytes_array(new_value) == expected

    @mark.parametrize(
        'new_value, error',
        [
            (2147483648, ValueError),
            (-2147483649, ValueError),
        ]
    )
    def test_get_bytes_array_errors(
        self,
        new_value: Any,
        error: type[BaseException]
    ) -> None:
        with raises(error):
            PLCDWordType.get_bytes_array(new_value)


class TestPLCIntType:
    @mark.parametrize(
        'name',
        [
            'int',
            'iNt',
            'INT',
        ]
    )
    def test_factory(self, name: str) -> None:
        assert PLCVarTypesReg.get(name) == PLCIntType

    @mark.parametrize(
        'byte, expected',
        [
            (bytearray([0, 5]), 5),
            (bytearray([127, 255]), 32767),
            (bytearray([128, 0]), -32768),
            (bytearray([146, 36]), -28124),
            (32767, 32767),
            (-32768, -32768),
            ('32767', 32767),
            ('-32768', -32768),
        ]
    )
    def test_validate_value(self, byte: Any, expected: bool) -> None:
        assert PLCIntType.validate_value(byte) == expected

    @mark.parametrize(
        'byte, error',
        [
            (bytearray([5]), ValueError),
            (32768, ValueError),
            (-32769, ValueError),
            (bytearray([1, 0, 0]), ValueError),
        ]
    )
    def test_validate_value_errors(
        self,
        byte: Any,
        error: type[BaseException]
    ) -> None:
        with raises(error):
            PLCIntType.validate_value(byte)

    @mark.parametrize(
        'new_value, expected',
        [
            (5, bytearray([0, 5])),
            (32767, bytearray([127, 255])),
            (-32768, bytearray([128, 0])),
            (-28124, bytearray([146, 36])),
        ]
    )
    def test_get_bytes_array(self, new_value: Any, expected: bytearray) -> None:
        assert PLCIntType.get_bytes_array(new_value) == expected

    @mark.parametrize(
        'new_value, error',
        [
            (32768, ValueError),
            (-32769, ValueError),
        ]
    )
    def test_get_bytes_array_errors(
        self,
        new_value: Any,
        error: type[BaseException]
    ) -> None:
        with raises(error):
            PLCIntType.get_bytes_array(new_value)


class TestPLCUIntType:
    @mark.parametrize(
        'name',
        [
            'uint',
            'UiNt',
            'UINT',
        ]
    )
    def test_factory(self, name: str) -> None:
        assert PLCVarTypesReg.get(name) == PLCUIntType

    @mark.parametrize(
        'byte, expected',
        [
            (bytearray([0, 5]), 5),
            (bytearray([255, 255]), 65535),
            (65535, 65535),
            ('65535', 65535),
        ]
    )
    def test_validate_value(self, byte: Any, expected: bool) -> None:
        assert PLCUIntType.validate_value(byte) == expected

    @mark.parametrize(
        'byte, error',
        [
            (bytearray([5]), ValueError),
            (65536, ValueError),
            (-1, ValueError),
            (bytearray([1, 0, 0]), ValueError),
        ]
    )
    def test_validate_value_errors(
        self,
        byte: Any,
        error: type[BaseException]
    ) -> None:
        with raises(error):
            PLCUIntType.validate_value(byte)

    @mark.parametrize(
        'new_value, expected',
        [
            (5, bytearray([0, 5])),
            (65535, bytearray([255, 255])),
        ]
    )
    def test_get_bytes_array(self, new_value: Any, expected: bytearray) -> None:
        assert PLCUIntType.get_bytes_array(new_value) == expected

    @mark.parametrize(
        'new_value, error',
        [
            (65536, ValueError),
            (-1, ValueError),
        ]
    )
    def test_get_bytes_array_errors(
        self,
        new_value: Any,
        error: type[BaseException]
    ) -> None:
        with raises(error):
            PLCUIntType.get_bytes_array(new_value)


class TestPLCSIntType:
    @mark.parametrize(
        'name',
        [
            'sint',
            'sInT',
            'SINT',
        ]
    )
    def test_factory(self, name: str) -> None:
        assert PLCVarTypesReg.get(name) == PLCSIntType

    @mark.parametrize(
        'byte, expected',
        [
            (bytearray([5]), 5),
            (bytearray([127]), 127),
            (bytearray([128]), -128),
            (bytearray([200]), -56),
            (5, 5),
            (-5, -5),
            ('5', 5),
            ('-5', -5),
        ]
    )
    def test_validate_value(self, byte: Any, expected: bool) -> None:
        assert PLCSIntType.validate_value(byte) == expected

    @mark.parametrize(
        'byte, error',
        [
            (128, ValueError),
            (-129, ValueError),
            (bytearray([1, 0]), ValueError),
        ]
    )
    def test_validate_value_errors(self, byte: Any, error: type[BaseException]) -> None:
        with raises(error):
            PLCSIntType.validate_value(byte)

    @mark.parametrize(
        'new_value, expected',
        [
            (5, bytearray([5])),
            (127, bytearray([127])),
            (-128, bytearray([128])),
            (-56, bytearray([200])),
        ]
    )
    def test_get_bytes_array(self, new_value: Any, expected: bytearray) -> None:
        assert PLCSIntType.get_bytes_array(new_value) == expected

    @mark.parametrize(
        'new_value, error',
        [
            (128, ValueError),
            (-129, ValueError),
        ]
    )
    def test_get_bytes_array_errors(
        self,
        new_value: Any,
        error: type[BaseException]
    ) -> None:
        with raises(error):
            PLCSIntType.get_bytes_array(new_value)


class TestPLCUSIntType:
    @mark.parametrize(
        'name',
        [
            'usint',
            'UsInT',
            'USINT',
        ]
    )
    def test_factory(self, name: str) -> None:
        assert PLCVarTypesReg.get(name) == PLCUSIntType

    @mark.parametrize(
        'byte, expected',
        [
            (bytearray([5]), 5),
            (bytearray([255]), 255),
            (5, 5),
            ('5', 5),
        ]
    )
    def test_validate_value(self, byte: Any, expected: bool) -> None:
        assert PLCUSIntType.validate_value(byte) == expected

    @mark.parametrize(
        'byte, error',
        [
            (256, ValueError),
            (-1, ValueError),
            (bytearray([1, 0]), ValueError),
        ]
    )
    def test_validate_value_errors(
        self,
        byte: Any,
        error: type[BaseException]
    ) -> None:
        with raises(error):
            PLCUSIntType.validate_value(byte)

    @mark.parametrize(
        'new_value, expected',
        [
            (5, bytearray([5])),
            (255, bytearray([255])),
        ]
    )
    def test_get_bytes_array(self, new_value: Any, expected: bytearray) -> None:
        assert PLCUSIntType.get_bytes_array(new_value) == expected

    @mark.parametrize(
        'new_value, error',
        [
            (256, ValueError),
            (-1, ValueError),
        ]
    )
    def test_get_bytes_array_errors(
        self,
        new_value: Any,
        error: type[BaseException]
    ) -> None:
        with raises(error):
            PLCUSIntType.get_bytes_array(new_value)


class TestPLCDIntType:
    @mark.parametrize(
        'name',
        [
            'dint',
            'DiNt',
            'DINT',
        ]
    )
    def test_factory(self, name: str) -> None:
        assert PLCVarTypesReg.get(name) == PLCDIntType

    @mark.parametrize(
        'byte, expected',
        [
            (bytearray([0, 0, 0, 5]), 5),
            (bytearray([127, 255, 255, 255]), 2147483647),
            (bytearray([128, 0, 0, 0]), -2147483648),
            (bytearray([146, 0, 36, 0]), -1845484544),
            (2147483647, 2147483647),
            (-2147483648, -2147483648),
            ('2147483647', 2147483647),
            ('-2147483648', -2147483648),
        ]
    )
    def test_validate_value(self, byte: Any, expected: bool) -> None:
        assert PLCDIntType.validate_value(byte) == expected

    @mark.parametrize(
        'byte, error',
        [
            (bytearray([0, 0, 5]), ValueError),
            (2147483648, ValueError),
            (-2147483649, ValueError),
            (bytearray([1, 0, 0, 0, 0]), ValueError),
        ]
    )
    def test_validate_value_errors(
        self,
        byte: Any,
        error: type[BaseException]
    ) -> None:
        with raises(error):
            PLCDIntType.validate_value(byte)

    @mark.parametrize(
        'new_value, expected',
        [
            (5, bytearray([0, 0, 0, 5])),
            (2147483647, bytearray([127, 255, 255, 255])),
            (-2147483648, bytearray([128, 0, 0, 0])),
            (-1845484544, bytearray([146, 0, 36, 0])),
        ]
    )
    def test_get_bytes_array(self, new_value: Any, expected: bytearray) -> None:
        assert PLCDIntType.get_bytes_array(new_value) == expected

    @mark.parametrize(
        'new_value, error',
        [
            (2147483648, ValueError),
            (-2147483649, ValueError),
        ]
    )
    def test_get_bytes_array_errors(self, new_value: Any, error: type[BaseException]) -> None:
        with raises(error):
            PLCDIntType.get_bytes_array(new_value)


class TestPLCUDIntType:
    @mark.parametrize(
        'name',
        [
            'udint',
            'uDiNt',
            'UDINT',
        ]
    )
    def test_factory(self, name: str) -> None:
        assert PLCVarTypesReg.get(name) == PLCUDIntType

    @mark.parametrize(
        'byte, expected',
        [
            (bytearray([0, 0, 0, 5]), 5),
            (bytearray([255, 255, 255, 255]), 4294967295),
            (4294967295, 4294967295),
            ('4294967295', 4294967295),
        ]
    )
    def test_validate_value(self, byte: Any, expected: bool) -> None:
        assert PLCUDIntType.validate_value(byte) == expected

    @mark.parametrize(
        'byte, error', [
            (bytearray([0, 0, 5]), ValueError),
            (4294967296, ValueError),
            (-1, ValueError),
            (bytearray([1, 0, 0, 0, 0]), ValueError),
        ]
    )
    def test_validate_value_errors(
        self,
        byte: Any,
        error: type[BaseException]
    ) -> None:
        with raises(error):
            PLCUDIntType.validate_value(byte)

    @mark.parametrize(
        'new_value, expected',
        [
            (5, bytearray([0, 0, 0, 5])),
            (4294967295, bytearray([255, 255, 255, 255])),
        ]
    )
    def test_get_bytes_array(self, new_value: Any, expected: bytearray) -> None:
        assert PLCUDIntType.get_bytes_array(new_value) == expected

    @mark.parametrize(
        'new_value, error', [
            (4294967296, ValueError),
            (-1, ValueError),
        ]
    )
    def test_get_bytes_array_errors(
        self,
        new_value: Any,
        error: type[BaseException]
    ) -> None:
        with raises(error):
            PLCUDIntType.get_bytes_array(new_value)


class TestPLCRealType:
    @mark.parametrize(
        'name',
        [
            'real',
            'rEaL',
            'REAL',
        ]
    )
    def test_factory(self, name: str) -> None:
        assert PLCVarTypesReg.get(name) == PLCRealType

    @mark.parametrize(
        'byte, expected',
        [
            (bytearray([12, 56, 0, 13]), 1.4174859672116617e-31),
            (bytearray([127, 127, 255, 255]), 3.4028234663852886e+38),
            (bytearray([255, 127, 255, 255]), -3.4028234663852886e+38),
            (bytearray([128, 0, 0, 0]), -0),
            (2147483647.1, 2147483647.1),
            (-2147483648., -2147483648.),
            ('2147483647.4', 2147483647.4),
            ('-2147483648.25', -2147483648.25),
        ]
    )
    def test_validate_value(self, byte: Any, expected: bool) -> None:
        assert PLCRealType.validate_value(byte) == expected

    @mark.parametrize(
        'byte, error',
        [
            (bytearray([0, 0, 5]), ValueError),
            (bytearray([1, 0, 0, 0, 0]), ValueError),
        ]
    )
    def test_validate_value_errors(
        self,
        byte: Any,
        error: type[BaseException]
    ) -> None:
        with raises(error):
            PLCRealType.validate_value(byte)

    @mark.parametrize(
        'new_value, expected',
        [
            (-3.4028234663852886e+38, bytearray([255, 127, 255, 255])),
            (3.4028234663852886e+38, bytearray([127, 127, 255, 255])),
            (-0., bytearray([128, 0, 0, 0])),
        ]
    )
    def test_get_bytes_array(self, new_value: Any, expected: bytearray) -> None:
        assert PLCRealType.get_bytes_array(new_value) == expected

    @mark.parametrize(
        'new_value, error',
        [
            (-3.402824e+38, ValueError),
            (3.402824e+38, ValueError),
        ]
    )
    def test_get_bytes_array_errors(
        self,
        new_value: Any,
        error: type[BaseException]
    ) -> None:
        with raises(error):
            PLCRealType.get_bytes_array(new_value)


class TestPLCLRealType:
    ...  #TODO


class TestPLCTimeType:
    ...  #TODO


class TestPLCDateType:
    ...  #TODO


class TestPLCDTLType:
    ...  #TODO


class TestPLCCharType:
    ...  #TODO


class TestPLCStringType:
    ...  #TODO
