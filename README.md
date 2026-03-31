# PyPLC

Wrapper for [python-snap7](https://python-snap7.readthedocs.io/en/latest/) library.  
<br>
[![Tests indicator](https://github.com/Jaimead7/PyPLC/actions/workflows/python310-lint-test.yml/badge.svg)](https://github.com/Jaimead7/PyPLC/actions/workflows/python310-lint-test.yml)  
[![License](https://img.shields.io/static/v1.svg?label=LICENSE&message=MIT&color=2dba4e&colorA=2b3137)](https://github.com/Jaimead7/PyPLC/blob/master/LICENSE)  
[![PyPI Latest Release](https://img.shields.io/pypi/v/jaimead7-pyplc.svg?color=2dba4e)](https://pypi.org/project/jaimead7-pyplc/)

## Authors
> Jaime Alvarez Diaz  
> [![email](https://img.shields.io/static/v1.svg?label=Gmail&message=alvarez.diaz.jaime1@gmail.com&logo=gmail&color=2dba4e&logoColor=white&colorA=c71610)](mailto:alvarez.diaz.jaime1@gmail.com)  
[![GitHub Profile](https://img.shields.io/static/v1.svg?label=GitHub&message=Jaimead7&logo=github&color=2dba4e&colorA=2b3137)](https://github.com/Jaimead7)  

## Installation
Install as a package from source files
```powershell
git clone https://github.com/Jaimead7/PyPLC.git
cd PyPLC
py -m pip install .
```

Install as a package from pypi
```
py -m pip install jaimead7-pyplc
```

## Usage
Create a `.toml` file with the structure descrived in [./docs/examples/plc.toml](./docs/examples/plc.toml).

```python
from pathlib import Path
import pyPLC

file_path: Path = Path('./docs/examples/plc.toml')
manager: PyPLC = PyPLC.from_file(file_path)
ret = manager.connect()

ret, value = manager.read_var(var= 'Var1')  # value = 10.5
ret, value = manager.write_var(var= 'Var1', value= 3.4)
ret, value = manager.read_var(var= 'Var1')  # value = 3.4
```

## Contributing
Pull requests are welcome. For major changes, please open an issue first
to discuss what you would like to change.

Please make sure to update tests as appropriate.
