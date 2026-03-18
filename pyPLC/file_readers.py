import importlib.util
import sys
from pathlib import Path
from typing import Any, Protocol

from .logging import pyplc_logger


class FileReader(Protocol):
    def __call__(self, file_path: Path) -> dict[str, Any]: ...

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
