==================
 HEPData Validator
==================

.. image:: https://img.shields.io/travis/HEPData/hepdata-validator.svg
   :target: https://travis-ci.org/HEPData/hepdata-validator
   :alt: Travis Status

.. image:: https://coveralls.io/repos/github/HEPData/hepdata-validator/badge.svg?branch=master
   :target: https://coveralls.io/github/HEPData/hepdata-validator?branch=master
   :alt: Coveralls Status

.. image:: https://img.shields.io/github/license/HEPData/hepdata-validator.svg
   :target: https://github.com/HEPData/hepdata-validator/blob/master/LICENSE.txt
   :alt: License

.. image:: https://img.shields.io/github/release/hepdata/hepdata-validator.svg?maxAge=2592000
   :target: https://github.com/HEPData/hepdata-validator/releases
   :alt: GitHub Releases

.. image:: https://img.shields.io/github/issues/hepdata/hepdata-validator.svg?maxAge=2592000
   :target: https://github.com/HEPData/hepdata-validator/issues
   :alt: GitHub Issues

.. image:: https://readthedocs.org/projects/hepdata-validator/badge/?version=latest
   :target: http://hepdata-validator.readthedocs.io/en/latest/?badge=latest
   :alt: Documentation Status

JSON schema and validation code for HEPData submissions

* Documentation: http://hepdata-validator.readthedocs.io


Installation
------------

If you can, install `LibYAML <https://pyyaml.org/wiki/LibYAML>`_ (a C library for parsing and emitting YAML) on your machine.
This will allow for the use of CLoader for faster loading of YAML files.
Not a big deal for small files, but performs markedly better on larger documents.

Via pip:

.. code:: bash

   pip install hepdata-validator

Via GitHub (for developers):

.. code:: bash

   git clone https://github.com/HEPData/hepdata-validator
   cd hepdata-validator
   pip install --upgrade -e . -r requirements.txt
   pytest testsuite


Usage
-----

To validate files, you need to instantiate a validator (I love OO).

.. code:: python

    from hepdata_validator.submission_file_validator import SubmissionFileValidator
    
    submission_file_validator = SubmissionFileValidator()
    submission_file_path = 'submission.yaml'
    
    # the validate method takes a string representing the file path. 
    is_valid_submission_file = submission_file_validator.validate(file_path=submission_file_path)
    
    # if there are any error messages, they are retrievable through this call
    submission_file_validator.get_messages()

    # the error messages can be printed
    submission_file_validator.print_errors(submission_file_path)


Data file validation is exactly the same.

.. code:: python
    
    from hepdata_validator.data_file_validator import DataFileValidator
    
    data_file_validator = DataFileValidator()
    
    # the validate method takes a string representing the file path.
    data_file_validator.validate(file_path='data.yaml')
    
    # if there are any error messages, they are retrievable through this call
    data_file_validator.get_messages()

    # the error messages can be printed
    data_file_validator.print_errors('data.yaml')


Optionally, if you have already loaded the YAML object, then you can pass it through
as a data object. You must also pass through the ``file_path`` since this is used as a key
for the error message lookup map.

.. code:: python

    from hepdata_validator.data_file_validator import DataFileValidator
    import yaml
    
    file_contents = yaml.load(open('data.yaml', 'r'))
    data_file_validator = DataFileValidator()
    
    data_file_validator.validate(file_path='data.yaml', data=file_contents)
    
    data_file_validator.get_messages('data.yaml')

    data_file_validator.print_errors('data.yaml')


An example `offline validation script <https://github.com/HEPData/hepdata-submission/blob/master/scripts/check.py>`_
uses the ``hepdata_validator`` package to validate the ``submission.yaml`` file and all YAML data files of a
HEPData submission.


Schemas
-------

There are currently 2 versions of the JSON schemas, `0.1.0
<https://github.com/HEPData/hepdata-validator/tree/master/hepdata_validator/schemas/0.1.0>`_ and `1.0.0
<https://github.com/HEPData/hepdata-validator/tree/master/hepdata_validator/schemas/1.0.0>`_. In most cases you should use
**1.0.0** (the default). If you need to use a different version, you can pass a keyword argument ``schema_version``
when initialising the validator:

.. code:: python

    submission_file_validator = SubmissionFileValidator(schema_version='0.1.0')
    data_file_validator = DataFileValidator(schema_version='0.1.0')
