import importlib.util
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any, ClassVar, Protocol

from typing_extensions import Self

from .logs import pyplc_logger


class FileReader(Protocol):
    def __call__(self, file_path: Path) -> dict[str, Any]: ...


class FileReaderReg:
    _file_readers: ClassVar[dict[str, FileReader]] = {}
    
    def __new__(cls) -> Self:
        msg: str = f'"{cls.__name__}" is not instantiable.'
        pyplc_logger.critical(msg)
        raise RuntimeError(msg)

    @staticmethod
    def _parse_name(name: str) -> str:
        return name.upper()

    @classmethod
    def register(cls, name: str) -> Callable[[FileReader], FileReader]:
        name = cls._parse_name(name)
        def decorator(func: FileReader) -> FileReader:
            if name in cls._file_readers:
                pyplc_logger.warning(f'FileReader "{name}" is already registered. It will be overwritten.')
            cls._file_readers[name] = func
            return func
        return decorator

    @classmethod
    def unregister(cls, name: str) -> None:
        name = cls._parse_name(name)
        cls._file_readers.pop(name, None)

    @classmethod
    def get(cls, name: str) -> FileReader:
        name = cls._parse_name(name)
        reader: FileReader | None = cls._file_readers.get(name, None)
        if reader is None:
            msg: str = f'"{name}" is not a valid FileReader.'
            pyplc_logger.error(msg)
            raise ValueError(msg)
        return reader

    @classmethod
    def from_file(cls, file: Path) -> FileReader:
        try:
            ex: str = file.suffix
            return cls.get(ex.replace('.', ''))
        except ValueError:
            msg: str = f'Could not obtain a FileReader for {file.name}.'
            pyplc_logger.error(msg)
            raise ValueError(msg)

    @classmethod
    def list(cls) -> list[str]:
        return sorted(cls._file_readers.keys())

    @classmethod
    def clear(cls) -> None:
        cls._file_readers.clear()


@FileReaderReg.register('YAML')
def yaml_reader(file_path: Path) -> dict[str, Any]:
    if importlib.util.find_spec('yaml') is None:
        msg: str = 'PyYAML required to read YAML files. Install with: pip install pyyaml.'
        pyplc_logger.critical(msg)
        raise ImportError(msg)
    import yaml
    if not file_path.is_file():
        msg: str = f'YAML file not found: {file_path}.'
        pyplc_logger.critical(msg)
        raise FileNotFoundError()
    try:
        with open(file_path, 'r') as f:
            data: Any = yaml.safe_load(f)
            if data is None:
                return {}
            if not isinstance(data, dict):
                msg: str = f'YAML file must contain a dictionary, got {type(data).__name__}.'
                pyplc_logger.critical(msg)
                raise ValueError(msg)
            return data
    except yaml.YAMLError as e:
        msg: str = f'Error parsing YAML file {file_path}: {e}.'
        pyplc_logger.critical(msg)
        raise RuntimeError(msg)

@FileReaderReg.register('TOML')
def toml_reader(file_path: Path) -> dict[str, Any]:
    if not file_path.is_file():
        msg: str = f'TOML file not found: {file_path}.'
        pyplc_logger.critical(msg)
        raise FileNotFoundError()
    if sys.version_info >= (3, 11):
        return _read_toml_ge311(file_path)
    else:
        return _read_toml_le310(file_path)

def _read_toml_ge311(file_path: Path) -> dict[str, Any]:
    try:
        import tomllib  # type: ignore
    except ImportError:
        msg: str = 'tomllib not available. Unexpected for Python 3.11+.'
        pyplc_logger.critical(msg)
        raise ImportError(msg)
    try:
        with open(file_path, 'rb') as f:
            data: dict[str, Any] = tomllib.load(f)
            return data
    except tomllib.TOMLDecodeError as e:
        msg: str = f'Error parsing TOML file {file_path}: {e}.'
        pyplc_logger.critical(msg)
        raise RuntimeError(msg)

def _read_toml_le310(file_path: Path) -> dict[str, Any]:
    if importlib.util.find_spec('tomli') is None:
        msg: str = 'tomli required to read TOML files in Python <3.11. Install with: pip install tomli.'
        pyplc_logger.critical(msg)
        raise ImportError(msg)
    import tomli  # type: ignore
    try:
        with open(file_path, 'rb') as f:
            data: dict[str, Any] = tomli.load(f)
            return data
    except tomli.TOMLDecodeError as e:
        msg: str = f'Error parsing TOML file {file_path}: {e}.'
        pyplc_logger.critical(msg)
        raise RuntimeError(msg)
