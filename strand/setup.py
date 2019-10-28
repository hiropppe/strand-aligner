from setuptools import find_packages

from distutils import core
from distutils.core import setup

from Cython.Build import cythonize

core.setup(
  ext_modules=cythonize(["cython/*.pyx"]),
)

setup(
  name='strand',
  version='0.0.1',
  packages=find_packages(),
  scripts=[
    'strand-align'
  ]
)
