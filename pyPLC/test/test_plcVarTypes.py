from struct import error as StructError

from pytest import mark, raises

from ..src.plcVarTypes import *


class TestPLCBoolType:
    @mark.parametrize('name', [
        'bool',
        'BoOl',
        'BOOL',
    ])
    def test_factory(self, name: str) -> None:
        assert PLCVarTypesFactory.get(name) == PLCBoolType

    @mark.parametrize('byte, pos, expected', [
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
        ('False', 0, False),
    ])
    def test_validateValue(self, byte: Any, pos: int, expected: bool) -> None:
        assert PLCBoolType.validateValue(byte, pos) == expected

    @mark.parametrize('byte, pos, error', [
        (5, 0, TypeError),
    ])
    def test_validateValueErrors(self, byte: Any, pos: int, error: BaseException) -> None:
        with raises(error):
            PLCBoolType.validateValue(byte, pos)

    @mark.parametrize('newValue, lastValue, pos, expected', [
        (False, bytearray([5]), 2, bytearray([1])),
        (True, bytearray([5]), 2, bytearray([5])),
        (0, bytearray([5]), 2, bytearray([1])),
        (1, bytearray([5]), 2, bytearray([5])),
        ('False', bytearray([5]), 2, bytearray([1])),
        ('True', bytearray([5]), 2, bytearray([5])),
    ])
    def test_getBytearray(self,
                          newValue: Any,
                          lastValue: bytearray,
                          pos: int,
                          expected: bytearray) -> None:
        assert PLCBoolType.getBytearray(newValue, lastValue, pos) == expected

    @mark.parametrize('newValue, lastValue, pos, error', [
        (True, bytearray([1, 0]), 7, TypeError),
        (5, bytearray([5]), 2, TypeError),
    ])
    def test_getBytearrayErrors(self,
                                newValue: Any,
                                lastValue: bytearray,
                                pos: int,
                                error: BaseException) -> None:
        with raises(error):
            PLCBoolType.getBytearray(newValue, lastValue, pos)


class TestPLCByteType:
    @mark.parametrize('name', [
        'byte',
        'ByTe',
        'BYTE',
    ])
    def test_factory(self, name: str) -> None:
        assert PLCVarTypesFactory.get(name) == PLCByteType

    @mark.parametrize('byte, expected', [
        (bytearray([5]), 5),
        (bytearray([127]), 127),
        (bytearray([128]), -128),
        (bytearray([200]), -56),
        (5, 5),
        (-5, -5),
        ('5', 5),
        ('-5', -5),
    ])
    def test_validateValue(self, byte: Any, expected: bool) -> None:
        assert PLCByteType.validateValue(byte) == expected

    @mark.parametrize('byte, error', [
        (128, TypeError),
        (-129, TypeError),
        (bytearray([1, 0]), TypeError),
    ])
    def test_validateValueErrors(self, byte: Any, error: BaseException) -> None:
        with raises(error):
            PLCByteType.validateValue(byte)

    @mark.parametrize('newValue, expected', [
        (5, bytearray([5])),
        (127, bytearray([127])),
        (-128, bytearray([128])),
        (-56, bytearray([200])),
    ])
    def test_getBytearray(self, newValue: Any, expected: bytearray) -> None:
        assert PLCByteType.getBytearray(newValue) == expected

    @mark.parametrize('newValue, error', [
        (128, TypeError),
        (-129, TypeError),
    ])
    def test_getBytearrayErrors(self, newValue: Any, error: BaseException) -> None:
        with raises(error):
            PLCByteType.getBytearray(newValue)


class TestPLCWordType:
    @mark.parametrize('name', [
        'word',
        'wOrD',
        'WORD',
    ])
    def test_factory(self, name: str) -> None:
        assert PLCVarTypesFactory.get(name) == PLCWordType

    @mark.parametrize('byte, expected', [
        (bytearray([0, 5]), 5),
        (bytearray([127, 255]), 32767),
        (bytearray([128, 0]), -32768),
        (bytearray([146, 36]), -28124),
        (32767, 32767),
        (-32768, -32768),
        ('32767', 32767),
        ('-32768', -32768),
    ])
    def test_validateValue(self, byte: Any, expected: bool) -> None:
        assert PLCWordType.validateValue(byte) == expected

    @mark.parametrize('byte, error', [
        (bytearray([5]), TypeError),
        (32768, TypeError),
        (-32769, TypeError),
        (bytearray([1, 0, 0]), TypeError),
    ])
    def test_validateValueErrors(self, byte: Any, error: BaseException) -> None:
        with raises(error):
            PLCWordType.validateValue(byte)

    @mark.parametrize('newValue, expected', [
        (5, bytearray([0, 5])),
        (32767, bytearray([127, 255])),
        (-32768, bytearray([128, 0])),
        (-28124, bytearray([146, 36])),
    ])
    def test_getBytearray(self, newValue: Any, expected: bytearray) -> None:
        assert PLCWordType.getBytearray(newValue) == expected

    @mark.parametrize('newValue, error', [
        (32768, TypeError),
        (-32769, TypeError),
    ])
    def test_getBytearrayErrors(self, newValue: Any, error: BaseException) -> None:
        with raises(error):
            PLCWordType.getBytearray(newValue)


class TestPLCDWordType:
    @mark.parametrize('name', [
        'dword',
        'DwOrD',
        'DWORD',
    ])
    def test_factory(self, name: str) -> None:
        assert PLCVarTypesFactory.get(name) == PLCDWordType

    @mark.parametrize('byte, expected', [
        (bytearray([0, 0, 0, 5]), 5),
        (bytearray([127, 255, 255, 255]), 2147483647),
        (bytearray([128, 0, 0, 0]), -2147483648),
        (bytearray([146, 0, 36, 0]), -1845484544),
        (2147483647, 2147483647),
        (-2147483648, -2147483648),
        ('2147483647', 2147483647),
        ('-2147483648', -2147483648),
    ])
    def test_validateValue(self, byte: Any, expected: bool) -> None:
        assert PLCDWordType.validateValue(byte) == expected

    @mark.parametrize('byte, error', [
        (bytearray([0, 0, 5]), TypeError),
        (2147483648, TypeError),
        (-2147483649, TypeError),
        (bytearray([1, 0, 0, 0, 0]), TypeError),
    ])
    def test_validateValueErrors(self, byte: Any, error: BaseException) -> None:
        with raises(error):
            PLCDWordType.validateValue(byte)

    @mark.parametrize('newValue, expected', [
        (5, bytearray([0, 0, 0, 5])),
        (2147483647, bytearray([127, 255, 255, 255])),
        (-2147483648, bytearray([128, 0, 0, 0])),
        (-1845484544, bytearray([146, 0, 36, 0])),
    ])
    def test_getBytearray(self, newValue: Any, expected: bytearray) -> None:
        assert PLCDWordType.getBytearray(newValue) == expected

    @mark.parametrize('newValue, error', [
        (2147483648, TypeError),
        (-2147483649, TypeError),
    ])
    def test_getBytearrayErrors(self, newValue: Any, error: BaseException) -> None:
        with raises(error):
            PLCDWordType.getBytearray(newValue)


class TestPLCIntType:
    @mark.parametrize('name', [
        'int',
        'iNt',
        'INT',
    ])
    def test_factory(self, name: str) -> None:
        assert PLCVarTypesFactory.get(name) == PLCIntType

    @mark.parametrize('byte, expected', [
        (bytearray([0, 5]), 5),
        (bytearray([127, 255]), 32767),
        (bytearray([128, 0]), -32768),
        (bytearray([146, 36]), -28124),
        (32767, 32767),
        (-32768, -32768),
        ('32767', 32767),
        ('-32768', -32768),
    ])
    def test_validateValue(self, byte: Any, expected: bool) -> None:
        assert PLCIntType.validateValue(byte) == expected

    @mark.parametrize('byte, error', [
        (bytearray([5]), TypeError),
        (32768, TypeError),
        (-32769, TypeError),
        (bytearray([1, 0, 0]), TypeError),
    ])
    def test_validateValueErrors(self, byte: Any, error: BaseException) -> None:
        with raises(error):
            PLCIntType.validateValue(byte)

    @mark.parametrize('newValue, expected', [
        (5, bytearray([0, 5])),
        (32767, bytearray([127, 255])),
        (-32768, bytearray([128, 0])),
        (-28124, bytearray([146, 36])),
    ])
    def test_getBytearray(self, newValue: Any, expected: bytearray) -> None:
        assert PLCIntType.getBytearray(newValue) == expected

    @mark.parametrize('newValue, error', [
        (32768, TypeError),
        (-32769, TypeError),
    ])
    def test_getBytearrayErrors(self, newValue: Any, error: BaseException) -> None:
        with raises(error):
            PLCIntType.getBytearray(newValue)


class TestPLCUIntType:
    @mark.parametrize('name', [
        'uint',
        'UiNt',
        'UINT',
    ])
    def test_factory(self, name: str) -> None:
        assert PLCVarTypesFactory.get(name) == PLCUIntType

    @mark.parametrize('byte, expected', [
        (bytearray([0, 5]), 5),
        (bytearray([255, 255]), 65535),
        (65535, 65535),
        ('65535', 65535),
    ])
    def test_validateValue(self, byte: Any, expected: bool) -> None:
        assert PLCUIntType.validateValue(byte) == expected

    @mark.parametrize('byte, error', [
        (bytearray([5]), TypeError),
        (65536, TypeError),
        (-1, TypeError),
        (bytearray([1, 0, 0]), TypeError),
    ])
    def test_validateValueErrors(self, byte: Any, error: BaseException) -> None:
        with raises(error):
            PLCUIntType.validateValue(byte)

    @mark.parametrize('newValue, expected', [
        (5, bytearray([0, 5])),
        (65535, bytearray([255, 255])),
    ])
    def test_getBytearray(self, newValue: Any, expected: bytearray) -> None:
        assert PLCUIntType.getBytearray(newValue) == expected

    @mark.parametrize('newValue, error', [
        (65536, TypeError),
        (-1, TypeError),
    ])
    def test_getBytearrayErrors(self, newValue: Any, error: BaseException) -> None:
        with raises(error):
            PLCUIntType.getBytearray(newValue)


class TestPLCSIntType:
    @mark.parametrize('name', [
        'sint',
        'sInT',
        'SINT',
    ])
    def test_factory(self, name: str) -> None:
        assert PLCVarTypesFactory.get(name) == PLCSIntType

    @mark.parametrize('byte, expected', [
        (bytearray([5]), 5),
        (bytearray([127]), 127),
        (bytearray([128]), -128),
        (bytearray([200]), -56),
        (5, 5),
        (-5, -5),
        ('5', 5),
        ('-5', -5),
    ])
    def test_validateValue(self, byte: Any, expected: bool) -> None:
        assert PLCSIntType.validateValue(byte) == expected

    @mark.parametrize('byte, error', [
        (128, TypeError),
        (-129, TypeError),
        (bytearray([1, 0]), TypeError),
    ])
    def test_validateValueErrors(self, byte: Any, error: BaseException) -> None:
        with raises(error):
            PLCSIntType.validateValue(byte)

    @mark.parametrize('newValue, expected', [
        (5, bytearray([5])),
        (127, bytearray([127])),
        (-128, bytearray([128])),
        (-56, bytearray([200])),
    ])
    def test_getBytearray(self, newValue: Any, expected: bytearray) -> None:
        assert PLCSIntType.getBytearray(newValue) == expected

    @mark.parametrize('newValue, error', [
        (128, TypeError),
        (-129, TypeError),
    ])
    def test_getBytearrayErrors(self, newValue: Any, error: BaseException) -> None:
        with raises(error):
            PLCSIntType.getBytearray(newValue)


class TestPLCUSIntType:
    @mark.parametrize('name', [
        'usint',
        'UsInT',
        'USINT',
    ])
    def test_factory(self, name: str) -> None:
        assert PLCVarTypesFactory.get(name) == PLCUSIntType

    @mark.parametrize('byte, expected', [
        (bytearray([5]), 5),
        (bytearray([255]), 255),
        (5, 5),
        ('5', 5),
    ])
    def test_validateValue(self, byte: Any, expected: bool) -> None:
        assert PLCUSIntType.validateValue(byte) == expected

    @mark.parametrize('byte, error', [
        (256, TypeError),
        (-1, TypeError),
        (bytearray([1, 0]), TypeError),
    ])
    def test_validateValueErrors(self, byte: Any, error: BaseException) -> None:
        with raises(error):
            PLCUSIntType.validateValue(byte)

    @mark.parametrize('newValue, expected', [
        (5, bytearray([5])),
        (255, bytearray([255])),
    ])
    def test_getBytearray(self, newValue: Any, expected: bytearray) -> None:
        assert PLCUSIntType.getBytearray(newValue) == expected

    @mark.parametrize('newValue, error', [
        (256, TypeError),
        (-1, TypeError),
    ])
    def test_getBytearrayErrors(self, newValue: Any, error: BaseException) -> None:
        with raises(error):
            PLCUSIntType.getBytearray(newValue)


class TestPLCDIntType:
    @mark.parametrize('name', [
        'dint',
        'DiNt',
        'DINT',
    ])
    def test_factory(self, name: str) -> None:
        assert PLCVarTypesFactory.get(name) == PLCDIntType

    @mark.parametrize('byte, expected', [
        (bytearray([0, 0, 0, 5]), 5),
        (bytearray([127, 255, 255, 255]), 2147483647),
        (bytearray([128, 0, 0, 0]), -2147483648),
        (bytearray([146, 0, 36, 0]), -1845484544),
        (2147483647, 2147483647),
        (-2147483648, -2147483648),
        ('2147483647', 2147483647),
        ('-2147483648', -2147483648),
    ])
    def test_validateValue(self, byte: Any, expected: bool) -> None:
        assert PLCDIntType.validateValue(byte) == expected

    @mark.parametrize('byte, error', [
        (bytearray([0, 0, 5]), TypeError),
        (2147483648, TypeError),
        (-2147483649, TypeError),
        (bytearray([1, 0, 0, 0, 0]), TypeError),
    ])
    def test_validateValueErrors(self, byte: Any, error: BaseException) -> None:
        with raises(error):
            PLCDIntType.validateValue(byte)

    @mark.parametrize('newValue, expected', [
        (5, bytearray([0, 0, 0, 5])),
        (2147483647, bytearray([127, 255, 255, 255])),
        (-2147483648, bytearray([128, 0, 0, 0])),
        (-1845484544, bytearray([146, 0, 36, 0])),
    ])
    def test_getBytearray(self, newValue: Any, expected: bytearray) -> None:
        assert PLCDIntType.getBytearray(newValue) == expected

    @mark.parametrize('newValue, error', [
        (2147483648, TypeError),
        (-2147483649, TypeError),
    ])
    def test_getBytearrayErrors(self, newValue: Any, error: BaseException) -> None:
        with raises(error):
            PLCDIntType.getBytearray(newValue)


class TestPLCUDIntType:
    @mark.parametrize('name', [
        'udint',
        'uDiNt',
        'UDINT',
    ])
    def test_factory(self, name: str) -> None:
        assert PLCVarTypesFactory.get(name) == PLCUDIntType

    @mark.parametrize('byte, expected', [
        (bytearray([0, 0, 0, 5]), 5),
        (bytearray([255, 255, 255, 255]), 4294967295),
        (4294967295, 4294967295),
        ('4294967295', 4294967295),
    ])
    def test_validateValue(self, byte: Any, expected: bool) -> None:
        assert PLCUDIntType.validateValue(byte) == expected

    @mark.parametrize('byte, error', [
        (bytearray([0, 0, 5]), TypeError),
        (4294967296, TypeError),
        (-1, TypeError),
        (bytearray([1, 0, 0, 0, 0]), TypeError),
    ])
    def test_validateValueErrors(self, byte: Any, error: BaseException) -> None:
        with raises(error):
            PLCUDIntType.validateValue(byte)

    @mark.parametrize('newValue, expected', [
        (5, bytearray([0, 0, 0, 5])),
        (4294967295, bytearray([255, 255, 255, 255])),
    ])
    def test_getBytearray(self, newValue: Any, expected: bytearray) -> None:
        assert PLCUDIntType.getBytearray(newValue) == expected

    @mark.parametrize('newValue, error', [
        (4294967296, TypeError),
        (-1, TypeError),
    ])
    def test_getBytearrayErrors(self, newValue: Any, error: BaseException) -> None:
        with raises(error):
            PLCUDIntType.getBytearray(newValue)


class TestPLCRealType:
    @mark.parametrize('name', [
        'real',
        'rEaL',
        'REAL',
    ])
    def test_factory(self, name: str) -> None:
        assert PLCVarTypesFactory.get(name) == PLCRealType

    @mark.parametrize('byte, expected', [
        (bytearray([12, 56, 0, 13]), 1.4174859672116617e-31),
        (bytearray([127, 127, 255, 255]), 3.4028234663852886e+38),
        (bytearray([255, 127, 255, 255]), -3.4028234663852886e+38),
        (bytearray([128, 0, 0, 0]), -0),
        (2147483647.1, 2147483647.1),
        (-2147483648., -2147483648.),
        ('2147483647.4', 2147483647.4),
        ('-2147483648.25', -2147483648.25),
    ])
    def test_validateValue(self, byte: Any, expected: bool) -> None:
        assert PLCRealType.validateValue(byte) == expected

    @mark.parametrize('byte, error', [
        (bytearray([0, 0, 5]), TypeError),
        (bytearray([1, 0, 0, 0, 0]), TypeError),
    ])
    def test_validateValueErrors(self, byte: Any, error: BaseException) -> None:
        with raises(error):
            PLCRealType.validateValue(byte)

    @mark.parametrize('newValue, expected', [
        (-3.4028234663852886e+38, bytearray([255, 127, 255, 255])),
        (3.4028234663852886e+38, bytearray([127, 127, 255, 255])),
        (-0., bytearray([128, 0, 0, 0])),
    ])
    def test_getBytearray(self, newValue: Any, expected: bytearray) -> None:
        assert PLCRealType.getBytearray(newValue) == expected

    @mark.parametrize('newValue, error', [
        (-3.402824e+38, TypeError),
        (3.402824e+38, TypeError),
    ])
    def test_getBytearrayErrors(self, newValue: Any, error: BaseException) -> None:
        with raises(error):
            PLCRealType.getBytearray(newValue)


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
