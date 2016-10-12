==================
 HEPData Validator
==================

.. image:: https://img.shields.io/travis/HEPData/hepdata-validator.svg
    :target: https://travis-ci.org/HEPData/hepdata-validator

.. image:: https://coveralls.io/repos/github/HEPData/hepdata-validator/badge.svg?branch=master
    :target: https://coveralls.io/github/HEPData/hepdata-validator?branch=master

.. image:: https://img.shields.io/github/license/HEPData/hepdata-validator.svg
    :target: https://github.com/HEPData/hepdata-validator/blob/master/LICENSE

.. image:: https://readthedocs.org/projects/hepdata-validator/badge/?version=latest
    :target: http://hepdata-validator.readthedocs.io/


The Durham High Energy Physics Database (HEPData) has been built up over the past four decades as a unique open-access
repository for scattering data from experimental particle physics. It currently comprises the data points from plots and
tables related to several thousand publications including those from the Large Hadron Collider (LHC). HEPData is funded
by a grant from the UK STFC and is based at the IPPP at Durham University.

HEPData is built upon Invenio 3 and is open source and free to use!

* Free software: GPLv2 license

* Documentation: http://hepdata-validator.readthedocs.io/


Installation
------------

If you can, install libyaml on your machine. This will allow for the use of CLoader for faster loading
of YAML files. Not a big deal for small files, but performs markedly better on larger documents.

Via pip:

.. code:: bash

  pip install hepdata_validator


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

    
Data file validation is exactly the same.

.. code:: python
    
    from hepdata_validator.data_file_validator import DataFileValidator
    
    data_file_validator = DataFileValidator()
    
    # the validate method takes a string representing the file path.
    data_file_validator.validate(file_path='data.yaml')
    
    # if there are any error messages, they are retrievable through this call
    data_file_validator.get_messages()


Optionally, if you have already loaded the YAML object, then you can pass it through
as a data object. You must also pass through the file_path since this is used as a key
for the error message lookup map.

.. code:: python

    from hepdata_validator.data_file_validator import DataFileValidator
    import yaml
    
    file = yaml.load(open('data.yaml', 'r'))
    data_file_validator = DataFileValidator()
    
    data_file_validator.validate(file_path='data.yaml', data=file_contents)
    
    data_file_validator.get_messages('data.yaml')