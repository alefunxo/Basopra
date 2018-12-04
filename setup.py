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
    install_requires=['pip>=6.0',
						'numpy>=1.15.1', 
						'Pyomo==5.4.3',
						'setuptools>=40.2.0'],

    classifiers=[
        'Development Status :: Alpha',
        'License :: OSI Approved :: GNU GPLv3',
        'Programming Language :: Python'])