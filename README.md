## HEPData Validator

[![Build Status](https://api.travis-ci.org/HEPData/hepdata-validator.svg)](https://travis-ci.org/HEPData/hepdata-validator)

[![Coverage Status](https://coveralls.io/repos/HEPData/hepdata-validator/badge.svg?branch=master&service=github)](https://coveralls.io/github/HEPData/hepdata-validator?branch=master)

[![PyPi](https://img.shields.io/pypi/dm/hepdata-validator.svg)](https://pypi.python.org/pypi/hepdata-validator/)

[![License](https://img.shields.io/github/license/hepdata/hepdata-validator.svg)](https://github.com/HEPData/hepdata-validator/blob/master/LICENSE.txt)



Includes the JSON Schema for submission files and code to run validations.

### Installation
If you can, install libyaml on your machine. This will allow for the use of CLoader for faster loading
of YAML files. Not a big deal for small files, but performs markedly better on larger documents.

Via pip:
```
pip install hepdata_validator
```


### Usage

To validate files, you need to instantiate a validator (I love OO).

``` python
from hepdata_validator.submission_file_validator import SubmissionFileValidator

submission_file_validator = SubmissionFileValidator()
submission_file_path = 'submission.yaml'

# the validate method takes a string representing the file path. 
is_valid_submission_file = submission_file_validator.validate(file_path=submission_file_path)

# if there are any error messages, they are retrievable through this call
submission_file_validator.get_messages()
```

Data file validation is exactly the same.

``` python
from hepdata_validator.data_file_validator import DataFileValidator

data_file_validator = DataFileValidator()

# the validate method takes a string representing the file path.
data_file_validator.validate(file_path='data.yaml')

# if there are any error messages, they are retrievable through this call
data_file_validator.get_messages()
```

Optionally, if you have already loaded the YAML object, then you can pass it through
as a data object. You must also pass through the file_path since this is used as a key
for the error message lookup map.

```python

from hepdata_validator.data_file_validator import DataFileValidator
import yaml

file = yaml.load(open('data.yaml', 'r'))
data_file_validator = DataFileValidator()

data_file_validator.validate(file_path='data.yaml', data=file_contents)

data_file_validator.get_messages('data.yaml')
```