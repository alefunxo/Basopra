# -*- coding: utf-8 -*-


from setuptools import setup,find_packages


	  

	
setup(
    name="BASOPRA",
    version="0.1",
    url="",
    license='GNU GPLv3',

    author="Alejandro Pena-Bello",
    author_email="contact.basopra@gmail.com",

    description="BASOPRA - BAttery Schedule OPtimizer for Residential Applications",
    #long_description=read("README.txt"),
    packages=find_packages(exclude=['docs','tests*']),
    install_requires=['pandas>=2.2',
                       'numpy>=2.0',
                       'pyomo>=6.8',
                       'matplotlib>=3.9',
                       'pytz>=2024.1'],

    classifiers=[
        'Development Status :: Alpha',
        'License :: OSI Approved :: GNU GPLv3',
        'Programming Language :: Python'])
