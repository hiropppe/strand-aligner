from distutils.core import setup
from Cython.Build import cythonize

setup(
  name = 'AlignerTest',
  ext_modules = cythonize(["*.pyx"]),
)
