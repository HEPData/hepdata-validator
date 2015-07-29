import json
from jsonschema import validate, ValidationError
import os
import yaml
from yaml.scanner import ScannerError
from hepdata_validator import Validator, ValidationMessage


__author__ = 'eamonnmaguire'


class SubmissionFileValidator(Validator):
    """
    Validates the Submission file YAML/JSON file
    """
    base_path = os.path.dirname(__file__)
    schema_file = base_path + '/schemas/submission_schema.json'
    additonal_info_schema = base_path + '/schemas/additional_info_schema.json'

    def validate(self, file_path):
        try:
            submission_file_schema = json.load(
                open(self.schema_file, 'r'))

            additional_file_section_schema = json.load(
                open(self.additonal_info_schema, 'r'))

            # even though we are using the yaml package to load,
            # it supports JSON and YAML

            data = yaml.load_all(open(file_path, 'r'))
            for data_item in data:
                try:
                    if 'comment' in data_item:
                        validate(data_item, additional_file_section_schema)
                    else:
                        validate(data_item, submission_file_schema)

                except ValidationError as ve:
                    self.add_validation_message(
                        ValidationMessage(file=file_path,
                                          message=ve.message + ' in ' + str(ve.instance)))
            if self.has_errors(file_path):
                return False
            else:
                return True
        except ScannerError as se:
            print(se)
            self.add_validation_message(
                ValidationMessage(file=file_path,
                                  message='There was a problem parsing the file. '
                                          'This can be because you forgot spaces '
                                          'after colons in your YAML file for instance.')
            )
