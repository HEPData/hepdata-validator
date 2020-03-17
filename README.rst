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

.. image:: https://img.shields.io/pypi/v/hepdata-validator
   :target: https://pypi.org/project/hepdata-validator/
   :alt: PyPI Version

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
   pip install --upgrade -e .[tests]
   pytest testsuite


Usage
-----

To validate against remote schemas, instantiate a ``HTTPSchemaDownloader`` object.

This object retrieves schemas from a remote location, and optionally save them in the local file system,
following the structure: ``schemas_remote/<host>/<version>/<schema_name>``

.. code:: python

    from hepdata_validator.schema_downloader import HTTPSchemaDownloader

    downloader = HTTPSchemaDownloader(
        endpoint="https://scikit-hep.org/pyhf/schemas/1.0.0",
        company="scikit-hep.org",
        version="1.0.0",
    )

    schema_name = "defs.json"
    schema_spec = downloader.get_schema(schema_name)

    # The downloader stores the remote schema in the local path
    downloader.save_locally(schema_name, schema_spec)


To validate submissions, instantiate a ``SubmissionFileValidator`` object:

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


To validate data files, you need to instantiate a ``DataFileValidator`` object.

In this case, the ``DataFileValidator`` can take a ``schema_folder`` argument to specify
the location of the schemas it is going to validate (by default ``schemas``).
This is useful when validating against schemas stored inside ``schemas_remote/<organization_name>``.

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

When considering **native HEP JSON schemas**, there are currently 2 versions: `0.1.0
<https://github.com/HEPData/hepdata-validator/tree/master/hepdata_validator/schemas/0.1.0>`_ and `1.0.0
<https://github.com/HEPData/hepdata-validator/tree/master/hepdata_validator/schemas/1.0.0>`_.
In most cases you should use **1.0.0** (the default). If you need to use a different version,
you can pass a keyword argument ``schema_version`` when initialising the validator:

.. code:: python

    sub_validator = SubmissionFileValidator(schema_version='0.1.0')
    data_validator = DataFileValidator(schema_version='0.1.0')

When using **remotely defined schemas**, versions depend on the organization providing those schemas,
and it is their responsibility to offer a way of keeping track of different schemas versions.
An example may be:

.. code:: python

    sub_validator = SubmissionFileValidator(schema_folder='schemas_remote/scikit-hep.org', schema_version='1.0.0')
    data_validator = DataFileValidator(schema_folder='schemas_remote/scikit-hep.org', schema_version='1.0.0')