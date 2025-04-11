from pytest import fixture, mark, raises

from ..src.plcVar import *
from ..src.plcVarTypes import *


class TestPLCReadWrite:
    @mark.parametrize('name, expected', [
        ('read', PLCReadWrite.READ),
        ('ReaD', PLCReadWrite.READ),
        ('READ', PLCReadWrite.READ),
        (1, PLCReadWrite.READ),
        ('readwrite', PLCReadWrite.READWRITE),
        ('ReaDwrIte', PLCReadWrite.READWRITE),
        ('READWRITE', PLCReadWrite.READWRITE),
        (0, PLCReadWrite.READWRITE),
    ])
    def test_validate(self, name: str, expected: int) -> None:
        assert PLCReadWrite.validate(name) == expected

    @mark.parametrize('name', [
        'hello',
        -1,
        10,
    ])
    def test_validateErrors(self, name: str) -> None:
        with raises(TypeError):
            _: int = PLCReadWrite.validate(name)


class TestPLCMemoryOffset:
    @mark.parametrize('input, bytesOffset, bitsOffset', [
        ('1.3', 1, 3),
        ((3, 7), 3, 7),
        ([4, 2], 4, 2),
    ])
    def test_initSingleArgs(self,
                            input: Any,
                            bytesOffset: int,
                            bitsOffset: int) -> None:
        offset = PLCMemoryOffset(input)
        assert offset.bytesOffset == bytesOffset
        assert offset.bitsOffset == bitsOffset

    @mark.parametrize('input, bytesOffset, bitsOffset', [
        ((3, 7), 3, 7),
    ])
    def test_initMultiArgs(self,
                           input: Any,
                           bytesOffset: int,
                           bitsOffset: int) -> None:
        offset = PLCMemoryOffset(*input)
        assert offset.bytesOffset == bytesOffset
        assert offset.bitsOffset == bitsOffset
        offset = PLCMemoryOffset(bytesOffset= input[0], bitsOffset= input[1])
        assert offset.bytesOffset == bytesOffset
        assert offset.bitsOffset == bitsOffset

    @mark.parametrize('input', [
        '1.8',
        (3, 8),
        [4, 8],
    ])
    def test_initSingleArgsErrors(self, input: Any) -> None:
        with raises(TypeError):
            _ = PLCMemoryOffset(input)

    @mark.parametrize('input', [
        (3, 8),
    ])
    def test_initMultiArgsErrors(self, input: Any) -> None:
        with raises(TypeError):
            _ = PLCMemoryOffset(*input)
        with raises(TypeError):
            _ = PLCMemoryOffset(bytesOffset= input[0], bitsOffset= input[1])

    @mark.parametrize('first, second, result', [
        (PLCMemoryOffset('3.1'), PLCMemoryOffset('3.1'), True),
        (PLCMemoryOffset('3.1'), '3.1', True),
        (PLCMemoryOffset('3.1'), (3, 1), True),
        (PLCMemoryOffset('3.1'), PLCMemoryOffset('5.2'), False),
        (PLCMemoryOffset('3.1'), '5.2', False),
        (PLCMemoryOffset('3.1'), (5, 2), False),
        (PLCMemoryOffset('3.1'), 5, False),
    ])
    def test_equals(self,
                    first: PLCMemoryOffset,
                    second: Any,
                    result: bool) -> None:
        assert (first == second) == result

class TestPLCVar:
    @fixture
    @staticmethod
    def plcVar() -> PLCVar:
        return PLCVar()

    @mark.parametrize('name', [
        'TestVar',
    ])
    def test_validateName(self, name: str, plcVar: PLCVar) -> None:
        plcVar.name = name
        assert plcVar.name == name

    @mark.parametrize('value', [])
    def test_validateNameErrors(self,
                                value: Any,
                                plcVar: PLCVar) -> None:
        with raises(TypeError):
            plcVar.name = value

    @mark.parametrize('offset, bytesOffset, bitsOffset', [
        (PLCMemoryOffset('1.4'), 1, 4),
        ((2, 3), 2, 3),
        ([2, 3], 2, 3),
        ('1.4', 1, 4),
    ])
    def test_validateOffset(self,
                            offset: Any,
                            bytesOffset: int,
                            bitsOffset: int,
                            plcVar: PLCVar) -> None:
        plcVar.offset = offset
        assert plcVar.offset.bytesOffset == bytesOffset
        assert plcVar.offset.bitsOffset == bitsOffset

    @mark.parametrize('value', [
        (3, 8),
        'noOffet',
    ])
    def test_validateOffsetErrors(self,
                                  value: Any,
                                  plcVar: PLCVar) -> None:
        with raises(TypeError):
            plcVar.offset = value

    @mark.parametrize('varType, expected', [
        (PLCIntType, PLCIntType),
        ('word', PLCWordType),
    ])
    def test_validateVarType(self,
                             varType: Any,
                             expected: PLCVarType,
                             plcVar: PLCVar) -> None:
        plcVar.varType = varType
        assert plcVar.varType == expected

    @mark.parametrize('value', [
        'noVarType',
    ])
    def test_validateVarTypeErrors(self,
                                   value: Any,
                                   plcVar: PLCVar) -> None:
        with raises(TypeError):
            plcVar.varType = value

    @mark.parametrize('rw, expected', [
        (PLCReadWrite.READWRITE, PLCReadWrite.READWRITE),
    ])
    def test_validateRW(self,
                        rw: Any,
                        expected: int,
                        plcVar: PLCVar) -> None:
        plcVar.rw = rw
        assert plcVar.rw == expected

    @mark.parametrize('value', [
        -1,
        'a',
    ])
    def test_validateRWErrors(self,
                              value: Any,
                              plcVar: PLCVar) -> None:
        with raises(TypeError):
            plcVar.rw = value

    def test_validateValueNone(self, plcVar: PLCVar) -> None:
        for varType in PLCVarTypesFactory.TYPES.values():
            plcVar.varType = varType
            plcVar.value = None
            assert plcVar.value == None

    @mark.parametrize('value, varType, result', [
        (12, PLCVarTypesFactory.get('usint'), 12),
        ('12', PLCVarTypesFactory.get('usint'), 12),
    ])  #TODO: create more tests
    def test_validateValue(self,
                           value: Any,
                           varType: PLCVarType,
                           result: Any,
                           plcVar: PLCVar) -> None:
        plcVar.varType = varType
        plcVar.value = value
        assert plcVar.value == result

    @mark.parametrize('value, varType', [
        (-12, PLCVarTypesFactory.get('usint')),
        ('-12', PLCVarTypesFactory.get('usint')),
    ])  #TODO: create more tests
    def test_validateValueErrors(self,
                                 value: Any,
                                 varType: PLCVarType,
                                 plcVar: PLCVar) -> None:
        plcVar.varType = varType
        with raises(TypeError):
            plcVar.value = value

    @mark.parametrize('fromDict, name, offset, varType, rw', [
        ({'Name': 'test',
          'Offset': '2.1',
          'Type': 'iNt',
          'R/W': 'read'},
         'test',
         PLCMemoryOffset('2.1'),
         PLCVarTypesFactory.get('INT'),
         PLCReadWrite.validate('REad')),
        ({'foo': 'bar'},
         'example',
         PLCMemoryOffset('1.3'),
         PLCVarTypesFactory.get('real'),
         PLCReadWrite.validate('readwrite'))
    ])
    def test_fromDict(self,
                      fromDict: dict,
                      name: str,
                      offset: PLCMemoryOffset,
                      varType: PLCVarType,
                      rw: int) -> None:
        var = PLCVar('example', '1.3', 'real', 'readwrite', fromDict= fromDict)
        assert var.name == name
        assert var.offset == offset
        assert var.varType == varType
        assert var.rw == rw

    @mark.parametrize('first, second', [
        (PLCVar(), PLCVar()),
        (PLCVar(name= 'test',
                offset= '1.2',
                varType= PLCVarTypesFactory.get('char'),
                rw= 'read',
                value= 'f'),
         PLCVar(name= 'test',
                offset= '1.2',
                varType= PLCVarTypesFactory.get('char'),
                rw= 'readwrite',
                value= 'b')),
        (PLCVar(name= 'test'), 'test'),
    ])
    def test_eq(self, first: Any, second: Any) -> None:
        assert first == second
        assert second == first

    def test_bytesSize(self, plcVar: PLCVar) -> None:
        for varType in PLCVarTypesFactory.TYPES.values():
            plcVar.varType = varType
            if varType.BYTES == 0:
                expected: int = 1
            else:
                expected: int = varType.BYTES
            assert plcVar.bytesSize == expected

class TestPLCVarDict():
    @fixture
    @staticmethod
    def plcVarDict() -> PLCVarDict:
        return PLCVarDict({0: PLCVar()})
    
    @mark.parametrize('key, value', [
        ('testVar', PLCVar()),
        (0, PLCVar()),
    ])
    def test_assignment(self,
                        key: str,
                        value: PLCVar,
                        plcVarDict: PLCVarDict) -> None:
        plcVarDict[key] = value
        assert plcVarDict[key] == value
        assert isinstance(plcVarDict, PLCVarDict)

    @mark.parametrize('key, value', [
        ('testVar', PLCVar()),
        (0, PLCVar()),
    ])
    def test_update(self,
                    key: str,
                    value: PLCVar,
                    plcVarDict: PLCVarDict) -> None:
        plcVarDict.update({key: value})
        assert plcVarDict[key] == value
        assert isinstance(plcVarDict, PLCVarDict)

    @mark.parametrize('key, value', [
        ('testVar', PLCVar()),
        (0, PLCVar()),
    ])
    def test_merge(self,
                   key: str,
                   value: PLCVar,
                   plcVarDict: PLCVarDict) -> None:
        plcVarDict = plcVarDict | {key: value}
        assert plcVarDict[key] == value
        assert isinstance(plcVarDict, PLCVarDict)

    @mark.parametrize('key, value', [
        ('testVar', PLCVar()),
        (0, PLCVar()),
    ])
    def test_selfMerge(self,
                   key: str,
                   value: PLCVar,
                   plcVarDict: PLCVarDict) -> None:
        plcVarDict |= {key: value}
        assert plcVarDict[key] == value
        assert isinstance(plcVarDict, PLCVarDict)

    @mark.parametrize('key, value', [
        ('testVar', 0),
        ('testVar', 'a'),
        ('testVar', (0, 1)),
        (0, 0),
    ])
    def test_assignmentErrors(self,
                              key: str,
                              value: PLCVar,
                              plcVarDict: PLCVarDict) -> None:
        with raises(TypeError):
            plcVarDict[key] = value
        with raises(TypeError):
            plcVarDict.update({key: value})
        with raises(TypeError):
            plcVarDict = plcVarDict | {key: value}
        with raises(TypeError):
            plcVarDict |= {key: value}
