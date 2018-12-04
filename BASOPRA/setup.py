import sys
from cx_Freeze import setup,Executable

build_exe_options={"packages":['numpy', 'sys', 'glob','os', 
					'csv', 'pickle', 'functools', 'argparse',
					'itertools', 'time', 'math', 'multiprocessing'],
					"excludes":["tkinter"]}

base=None

setup(
    name="BASOPRA",
    version="0.1",
    url="",
    license='GNU GPLv3',

    author="Alejandro Pena-Bello",
    author_email="alefunxo@gmail.com",

    description="BASOPRA - BAttery Schedule OPtimizer for Residential Applications",
    #long_description=read("README.txt"),
    options={"build_exe":build_exe_options},
    executables=[Executable("Main.py",base=base)])