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
        with raises(AssertionError):
            assert PLCBoolType.validateValue(byte, pos) != expected

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
        (True, bytearray([1, 0]), 7, StructError),
        (5, bytearray([5]), 2, TypeError),
    ])
    def test_getBytearrayErrors(self,
                                newValue: Any,
                                lastValue: bytearray,
                                pos: int,
                                error: BaseException) -> None:
        with raises(error):
            PLCBoolType.getBytearray(newValue, lastValue, pos)
