# -*- coding: utf-8 -*-


from setuptools import setup,find_packages



	
setup(
    name="BASOPRA",
    version="0.1",
    url="",
    license='GNU GPLv3',

    author="Alejandro Pena-Bello",
    author_email="alefunxo@gmail.com",

    description="BASOPRA - BAttery Schedule OPtimizer for Residential Applications",
    #long_description=read("README.txt"),
    packages=find_packages(exclude=['docs','tests*']),
    install_requires=['numpy', 
						'sys', 
						'glob',
						'os', 
						'csv', 
						'pickle', 
						'functools', 
						'argparse',
						'itertools', 
						'time', 
						'math', 
						'pyomo<=5.5', 
						'multiprocessing'],

    classifiers=[
        'Development Status :: Alpha',
        'License :: OSI Approved :: GNU GPLv3',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.6'])