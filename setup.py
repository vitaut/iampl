from distutils.core import setup

setup(
    name = 'ampl',
    version = '0.1',
    author = 'Victor Zverovich',
    url = 'https://github.com/vitaut/iampl',
    packages = ['ampl'],
    license = 'BSD license',
    description = 'An IPython extension for working with AMPL.',
    long_description = open('README.rst').read())