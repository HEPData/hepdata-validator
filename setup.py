"""JSON schema and validation code for HEPData submissions"""

import sys

import os
from setuptools import setup


test_requirements = [
    'pytest>=2.7.0',
    "pytest-cache>=1.0",
    'pytest-cov>=1.8.0',
    'pytest-pep8>=1.0.6',
    'coverage>=3.7.1',
    'mock>=2.0.0',
]

extras_require = {
    'all': [],
    'docs': ['Sphinx>7'],
    'tests': test_requirements,
}

for name, reqs in extras_require.items():
    extras_require['all'].extend(reqs)

g = {}
with open(os.path.join('hepdata_validator', 'version.py'), 'rt') as fp:
    exec(fp.read(), g)
    version = g['__version__']

# Get the long description from the README file
with open('README.rst', 'rt') as fp:
    long_description = fp.read()

setup(
    name='hepdata_validator',
    version=version,
    url='https://github.com/hepdata/hepdata-validator',
    license='GPLv2',
    author='HEPData Team',
    author_email='info@hepdata.net',
    description=__doc__,
    keywords='hepdata validator',
    package_data={'hepdata_validator': ["schemas/**/*.json"]},
    long_description=long_description,
    long_description_content_type='text/x-rst',
    packages=["hepdata_validator"],
    zip_safe=False,
    platforms='any',
    extras_require=extras_require,
    install_requires=[
        "click",
        "jsonschema",
        "packaging",
        "pyyaml>=5.4.1",
        "requests",
    ],
    python_requires='>=3.6',
    entry_points={
        'console_scripts': ['hepdata-validate=hepdata_validator.cli:validate'],
    }
)
