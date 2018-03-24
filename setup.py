import os
from setuptools import setup

from Cython.Build import cythonize
os.environ['CFLAGS'] = '-O3 -Wall -stdlib=libc++'
os.environ["MACOSX_DEPLOYMENT_TARGET"]= "10.10"

setup(
    name='ctf_parser',
    version='0.1',
    description='Multilevel Coarse-to-Fine Parser',
    author='Johannes Gontrum',
    author_email='gontrum@me.com',
    include_package_data=True,
    license='MPL 2.0',
    entry_points={
        'console_scripts': [
            'ctfparser = ctf_parser.scripts.parser:ctf',
            'ckyparser = ctf_parser.scripts.parser:cky'
        ]
    },
    ext_modules=cythonize(
        "ctf_parser/parser/inside_outside_calculator.pyx",
        language='c++'
    )
)
