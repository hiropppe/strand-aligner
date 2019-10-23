from distutils.core import setup
from Cython.Build import cythonize

setup(
  name = 'PyMaxent',
  ext_modules = cythonize(["cython/*.pyx"]),
)
