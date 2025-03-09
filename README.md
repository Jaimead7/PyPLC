# PyPLC

Siemens S7 PLCs communication with python-snap7.  
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
py -m pip install wheel tomli
py setup.py bdist_wheel
py -m pip install ./dist/jaimead7_pyplc-x.x.x-py3-none-any.whl
cd ..
rm -r PyPLC
```

Install as a package from pypi
```
py -m pip install jaimead7-pyplc
```

## Usage


## Contributing
Pull requests are welcome. For major changes, please open an issue first
to discuss what you would like to change.

Please make sure to update tests as appropriate.
