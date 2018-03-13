from setuptools import setup

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
              # 'parse = pcfg_parser.scripts.parse:main',
          ]
      }
)
