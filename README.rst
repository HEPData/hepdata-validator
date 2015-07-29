HEPData Validator

.. image:: https://api.travis-ci.org/HEPData/hepdata-validator.svg
        :target: https://travis-ci.org/HEPData/hepdata-validator


.. image:: https://coveralls.io/repos/HEPData/hepdata-validator/badge.svg?branch=master&service=github
  :target: https://coveralls.io/github/HEPData/hepdata-validator?branch=master


Includes the JSON Schema for submission files and code to run validations.

Usage.

To validate files, you need to instantiate a validator (I love OO).

``` python
from hepdata_validator.submission_file_validator import SubmissionFileValidator

submission_file_validator = SubmissionFileValidator()
submission_file_path = 'submission.yaml'

# the validate method takes a string representing the file path. 
is_valid_submission_file = submission_file_validator.validate(submission_file_path)

# if there are any error messages, they are retrievable through this call
submission_file_validator.get_messages()
```

Data file validation is exactly the same.

``` python
from hepdata_validator.submission_file_validator import DataFileValidator

data_file_validator = DataFileValidator()

# the validate method takes a string representing the file path.
data_file_validator.validate('data.yaml')

# if there are any error messages, they are retrievable through this call
data_file_validator.get_messages()
```