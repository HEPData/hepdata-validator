"""JSON schema and validation code for HEPData submissions"""

import sys

import os
from setuptools import setup
from setuptools.command.test import test as TestCommand


test_requirements = [
    'pytest>=2.7.0',
    "pytest-cache>=1.0",
    'pytest-cov>=1.8.0',
    'pytest-pep8>=1.0.6',
    'coverage>=3.7.1,<6.0',
    'mock>=2.0.0',
]

extras_require = {
    'all': [],
    'docs': ['Sphinx>=1.4.2'],
    'tests': test_requirements,
}


class PyTest(TestCommand):
    """PyTest Test."""

    user_options = [('pytest-args=', 'a', "Arguments to pass to pytest")]

    def initialize_options(self):
        """Init pytest."""
        TestCommand.initialize_options(self)
        self.pytest_args = []

        from ConfigParser import ConfigParser

        config = ConfigParser()
        config.read('pytest.ini')
        self.pytest_args = config.get('pytest', 'addopts').split(' ')

    def finalize_options(self):
        """Finalize pytest."""
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        """Run tests."""
        # import here, cause outside the eggs aren't loaded
        import pytest
        import _pytest.config

        pm = _pytest.config.get_plugin_manager()
        pm.consider_setuptools_entrypoints()
        errno = pytest.main(self.pytest_args)
        sys.exit(errno)


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
    test_suite='hepdata_validator.testsuite',
    tests_require=test_requirements,
    cmdclass={'test': PyTest},
    python_requires='>=3.6',
    entry_points={
        'console_scripts': ['hepdata-validate=hepdata_validator.cli:validate'],
    }
)
