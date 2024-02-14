from setuptools import setup

setup(cffi_modules="src/libdatachannel/libdatachannel_build.py:ffibuilder",
       setup_requires=["cffi>=1.0.0"],
      install_requires=["cffi>=1.0.0"],
      test_suite="tests",)
