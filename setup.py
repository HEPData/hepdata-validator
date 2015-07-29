__author__ = 'eamonnmaguire'
from distutils.core import setup

setup(
    name='hepdata_validator',
    version='0.1',
    url='https://github.com/hepdata/hepdata-validator',
    license='GPLv2',
    author='Eamonn Maguire',
    author_email='eamonn.maguire@cern.ch',
    description=__doc__,
    package_data={'hepdata_validator': ["schemas/*.json"]},
    long_description=open('README.md', 'rt').read(),
    packages=["hepdata_validator"],
    namespace_packages=["hepdata", "hepdata.ext", ],
    include_package_data=True,
    zip_safe=False,
    platforms='any',
    install_requires=[
        "pyyaml",
        "jsonschema"
    ],
    test_suite='hepdata_validator.testsuite',
    tests_requires=[]
)
