from os import path
from pathlib import Path

import tomli
from setuptools import find_packages, setup

with open("README.md", "r") as f:
    longDescription: str = f.read()

configFilePath: str = Path(__file__).parent / 'pyPLC' / 'dist' / 'config' / 'config.toml'
try:
    with open(configFilePath, 'rb') as f:
        myPyUtilsConfig: dict = tomli.load(f)
except tomli.TOMLDecodeError:
    raise tomli.TOMLDecodeError(f'Error with config file')

with open('requirements.txt') as f:
    requires: list = [line.replace('\n', '')
                      for line in f.readlines()
                      if line != '\n']

setup(
    name= myPyUtilsConfig['app']['name'],
    version= myPyUtilsConfig['app']['version'],
    description= 'Siemens S7 PLCs communication with python-snap7',
    long_description= longDescription,
    long_description_content_type= 'text/markdown',
    author= 'Jaimead7',
    author_email= 'alvarez.diaz.jaime1@gmail.com',
    url= 'https://github.com/Jaimead7/PyPLC',
    packages= find_packages(),
    package_data= {'pyPLC': ['dist/config/*.toml',]},
    include_package_data= True,
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.10',
    ],
    license= 'MIT',
    install_requires= requires,
    extras_require= {
        'dev': [
            'pytest>=8.3.4',
            'wheel>=0.45.1',
            'twine>=6.1.0'
        ],
    },
    python_requires= '>=3.10',
)
