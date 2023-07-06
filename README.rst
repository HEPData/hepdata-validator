==================
 HEPData Validator
==================

.. image:: https://github.com/HEPData/hepdata-validator/workflows/Continuous%20Integration/badge.svg?branch=main
   :target: https://github.com/HEPData/hepdata-validator/actions?query=branch%3Amain
   :alt: GitHub Actions Build Status

.. image:: https://coveralls.io/repos/github/HEPData/hepdata-validator/badge.svg?branch=main
   :target: https://coveralls.io/github/HEPData/hepdata-validator?branch=main
   :alt: Coveralls Status

.. image:: https://img.shields.io/github/license/HEPData/hepdata-validator.svg
   :target: https://github.com/HEPData/hepdata-validator/blob/main/LICENSE.txt
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
   :target: https://hepdata-validator.readthedocs.io/en/latest/?badge=latest
   :alt: Documentation Status

JSON schema and validation code (in Python 3) for HEPData submissions

* Documentation: https://hepdata-validator.readthedocs.io


Installation
------------

If you can, install `LibYAML <https://pyyaml.org/wiki/LibYAML>`_ (a C library for parsing and emitting YAML) on your machine.
This will allow for the use of ``CSafeLoader`` (instead of Python ``SafeLoader``) for faster loading of YAML files.
Not a big deal for small files, but performs markedly better on larger documents.

Install from `PyPI <https://pypi.org/project/hepdata-validator/>`_ using ``pip``:

.. code:: bash

   $ pip install --user hepdata-validator
   $ hepdata-validate --help

If you would like to use LibYAML, you may need an additional step if running on an M1 Mac, to ensure pyyaml is built
with the LibYAML bindings. Run the following after installing LibYAML via Homebrew:

.. code:: bash

  $ LDFLAGS="-L$(brew --prefix)/lib" CFLAGS="-I$(brew --prefix)/include" pip install --global-option="--with-libyaml" --force pyyaml


Developers
==========
Developers should install from GitHub in a `virtual environment <https://docs.python.org/3/tutorial/venv.html>`_:

.. code:: bash

   $ git clone https://github.com/HEPData/hepdata-validator
   $ cd hepdata-validator
   $ python3.9 -m venv venv
   $ source venv/bin/activate
   (venv)$ pip install --upgrade pip
   (venv)$ pip install --upgrade -e ".[all]"

Tests should be run both with and without LibYAML, as error messages from the different YAML parsers vary:

.. code:: bash

   (venv) $ USE_LIBYAML=True pytest testsuite
   (venv) $ USE_LIBYAML=False pytest testsuite

Usage
-----

The ``hepdata-validator`` package allows you to validate (via the command line or Python):

* A full directory of submission and data files
* An archive file (.zip, .tar, .tar.gz, .tgz) containing all of the files (`full details <https://hepdata-submission.readthedocs.io/en/latest/introduction.html>`_)
* A `single .yaml or .yaml.gz file <https://hepdata-submission.readthedocs.io/en/latest/single_yaml.html>`_ (but *not* ``submission.yaml`` or a YAML data file)
* A ``submission.yaml`` file or individual YAML data file (via Python only, not via the command line)

The same package is used for validating uploads made to `hepdata.net <https://www.hepdata.net>`_, therefore
first validating offline can be more efficient in checking your submission is valid before uploading.


Command line
============

Installing the ``hepdata-validator`` package adds the command ``hepdata-validate`` to your path, which allows you to validate a
`HEPData submission <https://hepdata-submission.readthedocs.io/en/latest/introduction.html>`_ offline.

Examples
^^^^^^^^

To validate a submission comprising of multiple files in the current directory:

.. code:: bash

    $ hepdata-validate

To validate a submission comprising of multiple files in another directory:

.. code:: bash

    $ hepdata-validate -d ../TestHEPSubmission

To validate an archive file (.zip, .tar, .tar.gz, .tgz) in the current directory:

.. code:: bash

    $ hepdata-validate -a TestHEPSubmission.zip

To validate a single YAML file in the current directory:

.. code:: bash

    $ hepdata-validate -f single_yaml_file.yaml

Usage options
^^^^^^^^^^^^^

.. code:: bash

    $ hepdata-validate --help
    Usage: hepdata-validate [OPTIONS]

      Offline validation of submission.yaml and YAML data files. Can check either
      a directory, an archive file, or the single YAML file format.

    Options:
      -d, --directory TEXT  Directory to check (defaults to current working
                            directory)
      -f, --file TEXT       Single .yaml or .yaml.gz file (but not submission.yaml
                            or a YAML data file) to check - see https://hepdata-
                            submission.readthedocs.io/en/latest/single_yaml.html.
                            (Overrides directory)
      -a, --archive TEXT    Archive file (.zip, .tar, .tar.gz, .tgz) to check.
                            (Overrides directory and file)
      --help                Show this message and exit.


Python
======

Validating a full submission
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To validate a full submission, instantiate a ``FullSubmissionValidator`` object:

.. code:: python

    from hepdata_validator.full_submission_validator import FullSubmissionValidator, SchemaType
    full_submission_validator = FullSubmissionValidator()

    # validate a directory
    is_dir_valid = full_submission_validator.validate(directory='TestHEPSubmission')

    # or uncomment to validate an archive file
    # is_archive_valid = full_submission_validator.validate(archive='TestHEPSubmission.zip')

    # or uncomment to validate a single file
    # is_file_valid = full_submission_validator.validate(file='single_yaml_file.yaml')

    # if there are any error messages, they are retrievable through this call
    full_submission_validator.get_messages()

    # the error messages can be printed for each file
    full_submission_validator.print_errors('submission.yaml')

    # the list of valid files can be retrieved via the valid_files property, which is a
    # dict mapping SchemaType (e.g. SUBMISSION, DATA, SINGLE_YAML, REMOTE) to lists of
    # valid files
    full_submission_validator.valid_files[SchemaType.SUBMISSION]
    full_submission_validator.valid_files[SchemaType.DATA]
    # full_submission_validator.valid_files[SchemaType.SINGLE_YAML]

    # if a remote schema is used, valid_files is a list of tuples (schema, file)
    # full_submission_validator.valid_files[SchemaType.REMOTE]

    # the list of valid files can be printed
    full_submission_validator.print_valid_files()


Validating individual files
^^^^^^^^^^^^^^^^^^^^^^^^^^^

To validate submission files, instantiate a ``SubmissionFileValidator`` object:

.. code:: python

    from hepdata_validator.submission_file_validator import SubmissionFileValidator

    submission_file_validator = SubmissionFileValidator()
    submission_file_path = 'submission.yaml'

    # the validate method takes a string representing the file path
    is_valid_submission_file = submission_file_validator.validate(file_path=submission_file_path)

    # if there are any error messages, they are retrievable through this call
    submission_file_validator.get_messages()

    # the error messages can be printed
    submission_file_validator.print_errors(submission_file_path)


To validate data files, instantiate a ``DataFileValidator`` object:

.. code:: python

    from hepdata_validator.data_file_validator import DataFileValidator

    data_file_validator = DataFileValidator()

    # the validate method takes a string representing the file path
    data_file_validator.validate(file_path='data.yaml')

    # if there are any error messages, they are retrievable through this call
    data_file_validator.get_messages()

    # the error messages can be printed
    data_file_validator.print_errors('data.yaml')


Optionally, if you have already loaded the YAML object, then you can pass it through
as a ``data`` object. You must also pass through the ``file_path`` since this is used as a key
for the error message lookup map.

.. code:: python

    from hepdata_validator.data_file_validator import DataFileValidator
    import yaml

    file_contents = yaml.safe_load(open('data.yaml', 'r'))
    data_file_validator = DataFileValidator()

    data_file_validator.validate(file_path='data.yaml', data=file_contents)

    data_file_validator.get_messages('data.yaml')

    data_file_validator.print_errors('data.yaml')

For the analogous case of the ``SubmissionFileValidator``:

.. code:: python

    from hepdata_validator.submission_file_validator import SubmissionFileValidator
    import yaml
    submission_file_path = 'submission.yaml'

    # convert a generator returned by yaml.safe_load_all into a list
    docs = list(yaml.safe_load_all(open(submission_file_path, 'r')))

    submission_file_validator = SubmissionFileValidator()
    is_valid_submission_file = submission_file_validator.validate(file_path=submission_file_path, data=docs)
    submission_file_validator.print_errors(submission_file_path)


Schema Versions
---------------

When considering **native HEPData JSON schemas**, there are multiple `versions
<https://github.com/HEPData/hepdata-validator/tree/main/hepdata_validator/schemas>`_.
In most cases you should use the **latest** version (the default). If you need to use a different version,
you can pass a keyword argument ``schema_version`` when initialising the validator:

.. code:: python

    submission_file_validator = SubmissionFileValidator(schema_version='0.1.0')
    data_file_validator = DataFileValidator(schema_version='0.1.0')


Remote Schemas
--------------

When using **remotely defined schemas**, versions depend on the organization providing those schemas,
and it is their responsibility to offer a way of keeping track of different schema versions.

The ``JsonSchemaResolver`` object resolves ``$ref`` in the JSON schema. The ``HTTPSchemaDownloader`` object retrieves
schemas from a remote location, and optionally saves them in the local file system, following the structure:
``schemas_remote/<org>/<project>/<version>/<schema_name>``. An example may be:

.. code:: python

    from hepdata_validator.data_file_validator import DataFileValidator
    data_validator = DataFileValidator()

    # Split remote schema path and schema name
    schema_path = 'https://scikit-hep.org/pyhf/schemas/1.0.0/'
    schema_name = 'workspace.json'

    # Create JsonSchemaResolver object to resolve $ref in JSON schema
    from hepdata_validator.schema_resolver import JsonSchemaResolver
    pyhf_resolver = JsonSchemaResolver(schema_path)

    # Create HTTPSchemaDownloader object to validate against remote schema
    from hepdata_validator.schema_downloader import HTTPSchemaDownloader
    pyhf_downloader = HTTPSchemaDownloader(pyhf_resolver, schema_path)

    # Retrieve and save the remote schema in the local path
    pyhf_type = pyhf_downloader.get_schema_type(schema_name)
    pyhf_spec = pyhf_downloader.get_schema_spec(schema_name)
    pyhf_downloader.save_locally(schema_name, pyhf_spec)

    # Load the custom schema as a custom type
    import os
    pyhf_path = os.path.join(pyhf_downloader.schemas_path, schema_name)
    data_validator.load_custom_schema(pyhf_type, pyhf_path)

    # Validate a specific schema instance
    data_validator.validate(file_path='pyhf_workspace.json', file_type=pyhf_type)


The native HEPData JSON schema are provided as part of the ``hepdata-validator`` package and it is not necessary to
download them. However, in principle, for testing purposes, note that the same mechanism above could be used with:

.. code:: python

    schema_path = 'https://hepdata.net/submission/schemas/1.1.1/'
    schema_name = 'data_schema.json'

and passing a HEPData YAML data file as the ``file_path`` argument of the ``validate`` method.
