from pytest import fixture, mark, raises

from pyPLC.var_types import *
from pyPLC.var_types import PLCVarType
from pyPLC.vars import *
from pyPLC.vars import PLCVar


class TestPLCReadWrite:
    @mark.parametrize(
        'value, expected',
        [
            ('read', PLCReadWrite.READ),
            ('ReaD', PLCReadWrite.READ),
            ('READ', PLCReadWrite.READ),
            (1, PLCReadWrite.READ),
            ('1', PLCReadWrite.READ),
            ('read_write', PLCReadWrite.READ_WRITE),
            ('ReaD_wrIte', PLCReadWrite.READ_WRITE),
            ('READ_WRITE', PLCReadWrite.READ_WRITE),
            (0, PLCReadWrite.READ_WRITE),
            ('0', PLCReadWrite.READ_WRITE),
            ('hello', PLCReadWrite.READ),
            (-1, PLCReadWrite.READ),
            (10, PLCReadWrite.READ),
        ]
    )
    def test_validate(self, value: str, expected: int) -> None:
        assert PLCReadWrite.validate(value) == expected


class TestPLCMemoryOffset:
    @mark.parametrize(
        'input, bytes_offset, bits_offset',
        [
            ('1.3', 1, 3),
            ((3, 7), 3, 7),
            ([4, 2], 4, 2),
            ([12, 2], 12, 2),
        ]
    )
    def test_init_single_args(
        self,
        input: Any,
        bytes_offset: int,
        bits_offset: int
    ) -> None:
        offset = PLCMemoryOffset(input)
        assert offset.bytes_offset == bytes_offset
        assert offset.bits_offset == bits_offset

    @mark.parametrize(
        'input, bytes_offset, bits_offset',
        [
            ((3, 7), 3, 7),
            (('3', '7'), 3, 7),
        ]
    )
    def test_init_multi_args(
        self,
        input: Any,
        bytes_offset: int,
        bits_offset: int
    ) -> None:
        offset = PLCMemoryOffset(*input)
        assert offset.bytes_offset == bytes_offset
        assert offset.bits_offset == bits_offset
        offset = PLCMemoryOffset(bytes_offset= input[0], bits_offset= input[1])
        assert offset.bytes_offset == bytes_offset
        assert offset.bits_offset == bits_offset

    @mark.parametrize(
        'input', 
        [
            '1.8',
            (3, 8),
            [4, 8],
            [4, -1],
            [-1, 0],
            ['a', 0],
            [0, 'a'],
        ]
    )
    def test_init_single_args_errors(self, input: Any) -> None:
        with raises(ValueError):
            _ = PLCMemoryOffset(input)

    @mark.parametrize(
        'input',
        [
            (3, 8),
            [4, 8],
            [4, -1],
            [-1, 0],
            ['a', 0],
            [0, 'a'],
        ]
    )
    def test_init_multi_args_errors(self, input: Any) -> None:
        with raises(ValueError):
            _ = PLCMemoryOffset(*input)
        with raises(ValueError):
            _ = PLCMemoryOffset(bytes_offset= input[0], bits_offset= input[1])

    @mark.parametrize(
        'first, second, result',
        [
            (PLCMemoryOffset('3.1'), PLCMemoryOffset('3.1'), True),
            (PLCMemoryOffset('3.1'), '3.1', True),
            (PLCMemoryOffset('3.1'), (3, 1), True),
            (PLCMemoryOffset('3.1'), PLCMemoryOffset('5.2'), False),
            (PLCMemoryOffset('3.1'), '5.2', False),
            (PLCMemoryOffset('3.1'), (5, 2), False),
            (PLCMemoryOffset('3.1'), 5, False),
        ]
    )
    def test_equals(
        self,
        first: PLCMemoryOffset,
        second: Any,
        result: bool
    ) -> None:
        assert (first == second) == result

class TestPLCVar:
    @fixture
    @staticmethod
    def default_var() -> PLCVar:
        return PLCVar(
            name= 'test',
            offset= PLCMemoryOffset((0, 0)),
            var_type= PLCBoolType,
            rw= PLCReadWrite.READ,
            value= None
        )

    @mark.parametrize(
        'name',
        [
            'NewName',
        ]
    )
    def test_validate_name(self, name: str, default_var: PLCVar) -> None:
        default_var.name = name
        assert default_var.name == name

    @mark.parametrize('value', [])
    def test_validate_name_errors(self, value: Any, default_var: PLCVar) -> None:
        with raises(ValueError):
            default_var.name = value

    @mark.parametrize(
        'offset, bytes_offset, bits_offset',
        [
            (PLCMemoryOffset('1.4'), 1, 4),
            ((2, 3), 2, 3),
            ([2, 3], 2, 3),
            ('1.4', 1, 4),
        ]
    )
    def test_validate_offset(
        self,
        offset: Any,
        bytes_offset: int,
        bits_offset: int,
        default_var: PLCVar
    ) -> None:
        default_var.offset = offset
        assert default_var.offset.bytes_offset == bytes_offset
        assert default_var.offset.bits_offset == bits_offset

    @mark.parametrize(
        'value',
        [
            (3, 8),
            (-3, 5),
            '3.8',
            'noOffet',
        ]
    )
    def test_validate_offset_errors(self, value: Any, default_var: PLCVar) -> None:
        with raises(ValueError):
            default_var.offset = value

    @mark.parametrize(
        'var_type, expected',
        [
            (PLCIntType, PLCIntType),
            ('word', PLCWordType),
        ]
    )
    def test_validate_var_type(
        self,
        var_type: Any,
        expected: PLCVarType,
        default_var: PLCVar
    ) -> None:
        default_var.var_type = var_type
        assert default_var.var_type == expected

    @mark.parametrize(
        'value',
        [
            'noVarType',
        ]
    )
    def test_validate_var_type_errors(
        self,
        value: Any,
        default_var: PLCVar
    ) -> None:
        with raises(ValueError):
            default_var.var_type = value

    @mark.parametrize(
        'rw, expected',
        [
            (PLCReadWrite.READ_WRITE, PLCReadWrite.READ_WRITE),
            ('read', PLCReadWrite.READ),
            ('1', PLCReadWrite.READ),
            (1, PLCReadWrite.READ),
            ('read_write', PLCReadWrite.READ_WRITE),
            ('0', PLCReadWrite.READ_WRITE),
            (0, PLCReadWrite.READ_WRITE),
        ]
    )
    def test_validate_rw(
        self,
        rw: Any,
        expected: PLCReadWrite,
        default_var: PLCVar
    ) -> None:
        default_var.rw = rw
        assert default_var.rw == expected

    @mark.parametrize(
        'value',
        [
            -1,
            'a',
            10
        ]
    )
    def test_validate_rw_errors(
        self,
        value: Any,
        default_var: PLCVar
    ) -> None:
        assert default_var.rw == PLCReadWrite.READ

    def test_validate_value_none(self, default_var: PLCVar) -> None:
        for var_type in PLCVarTypesReg.list():
            default_var.var_type = PLCVarTypesReg.get(var_type)
            default_var.value = None
            assert default_var.value == None

    @mark.parametrize(
        'value, var_type, result',
        [
            #(12, PLCVarTypesReg.get('usint'), 12),
            ('12', PLCVarTypesReg.get('usint'), 12),
        ]
    )  #TODO: create more tests
    def test_validate_value(
        self,
        value: Any,
        var_type: type[PLCVarType],
        result: Any,
        default_var: PLCVar
    ) -> None:
        print(default_var.value)
        default_var.var_type = var_type
        default_var.value = value
        print('-----------')
        print(value, type(value))
        print(default_var.value, type(default_var.value))
        print(result, type(result))
        print('*************')
        assert default_var.value == result

    @mark.parametrize(
        'value, var_type',
        [
            (-12, PLCVarTypesReg.get('usint')),
            ('-12', PLCVarTypesReg.get('usint')),
        ]
    )  #TODO: create more tests
    def test_validate_valueErrors(
        self,
        value: Any,
        var_type: type[PLCVarType],
        default_var: PLCVar
    ) -> None:
        default_var.var_type = var_type
        with raises(ValueError):
            default_var.value = value

    @mark.parametrize(
        'data, name, offset, var_type, rw',
        [
            (
                {
                    'Name': 'test',
                    'Offset': '2.1',
                    'Type': 'iNt',
                    'RW': 'read'
                },
                'test',
                PLCMemoryOffset('2.1'),
                PLCVarTypesReg.get('INT'),
                PLCReadWrite.validate('REad')
            )
        ]
    )
    def test_from_dict(
        self,
        data: dict,
        name: str,
        offset: PLCMemoryOffset,
        var_type: PLCVarType,
        rw: PLCReadWrite
    ) -> None:
        var: PLCVar = PLCVar.from_dict(data)
        assert var.name == name
        assert var.offset == offset
        assert var.var_type == var_type
        assert var.rw == rw

    @mark.parametrize(
        'comp',
        [
            PLCVar(
                name= 'test',
                offset= PLCMemoryOffset((0, 0)),
                var_type= PLCBoolType,
                rw= PLCReadWrite.READ,
                value= None
            ),
            'test',
        ]
    )
    def test_eq(self, comp: Any, default_var: PLCVar) -> None:
        assert comp == default_var
        assert default_var == comp

    def test_bytes_size(self, default_var: PLCVar) -> None:
        for type_class in PLCVarTypesReg.list():
            var_type: type[PLCVarType] = PLCVarTypesReg.get(type_class)
            default_var.var_type = var_type
            if var_type.BYTES == 0:
                expected: int = 1
            else:
                expected: int = var_type.BYTES
            assert default_var.bytes_size == expected

class TestPLCVarDict():
    @fixture
    @staticmethod
    def default_var() -> PLCVar:
        return PLCVar(
            name= 'test',
            offset= PLCMemoryOffset((0, 0)),
            var_type= PLCBoolType,
            rw= PLCReadWrite.READ,
            value= None
        )

    @fixture
    @staticmethod
    def plc_var_dict(default_var: PLCVar) -> PLCVarDict:
        return PLCVarDict({0: default_var})

    @mark.parametrize(
        'key',
        [
            'testVar',
            0,
        ]
    )
    def test_update(
        self,
        key: str,
        default_var: PLCVar
    ) -> None:
        plc_var_dict: PLCVarDict = PLCVarDict()
        plc_var_dict.update({key: default_var})
        assert plc_var_dict[key] == default_var
        assert isinstance(plc_var_dict, PLCVarDict)

    @mark.parametrize(
        'key',
        [
            'testVar',
            0,
        ]
    )
    def test_merge(
        self,
        key: str,
        default_var: PLCVar
    ) -> None:
        plc_var_dict: PLCVarDict = PLCVarDict()
        plc_var_dict = plc_var_dict | {key: default_var}
        assert plc_var_dict[key] == default_var
        assert isinstance(plc_var_dict, PLCVarDict)

    @mark.parametrize(
        'key',
        [
            'testVar',
            0,
        ]
    )
    def test_self_merge(
        self,
        key: str,
        default_var: PLCVar
    ) -> None:
        plc_var_dict: PLCVarDict = PLCVarDict()
        plc_var_dict |= {key: default_var}
        assert plc_var_dict[key] == default_var
        assert isinstance(plc_var_dict, PLCVarDict)

    @mark.parametrize(
        'key, value',
        [
            ('test', 0),
            ('test', 'a'),
            ('test', (0, 1)),
            (0, 0),
        ]
    )
    def test_assignment_errors(
        self,
        key: str,
        value: PLCVar,
    ) -> None:
        plc_var_dict: PLCVarDict = PLCVarDict()
        with raises(ValueError):
            plc_var_dict[key] = value
        with raises(ValueError):
            plc_var_dict.update({key: value})
        with raises(ValueError):
            plc_var_dict = plc_var_dict | {key: value}
        with raises(ValueError):
            plc_var_dict |= {key: value}
