#!/usr/bin/env python
from setuptools import setup

with open('README.rst') as f:
    readme = f.read()

setup(name="gamejolt",
      version="1",
      author="Benjamin Moran",
      author_email="benmoran@protonmail.com",
      description="A module for interfacing with the GameJolt API",
      license="MIT",
      keywords="game gamedev gamejolt",
      url="https://github.com/benmoran56/gamejolt",
      long_description=readme,
      py_modules=['gamejolt'],
      classifiers=["Development Status :: 5 - Production/Stable",
                   "Intended Audience :: Developers",
                   "License :: OSI Approved :: MIT License",
                   "Operating System :: OS Independent",
                   "Programming Language :: Python :: 3 :: Only",
                   "Topic :: Games/Entertainment",
                   "Topic :: Software Development :: Libraries"])
