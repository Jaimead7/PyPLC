from pytest import fixture, mark, raises

from ..src.plcMemoryAreas import *
from ..src.plcVar import PLCVar


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


class TestPLCMemoryArea():
    ... #TODO


class TestPLCInputs():
    ... #TODO


class TestPLCOutputs():
    ... #TODO


class TestPLCMarkers():
    ... #TODO


class TestPLCDB():
    ... #TODO
