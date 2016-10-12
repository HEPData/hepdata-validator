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
    default_schema_file = base_path + '/schemas/submission_schema.json'
    additonal_info_schema = base_path + '/schemas/additional_info_schema.json'

    def validate(self, **kwargs):
        """
        Validates a submission file
        :param file_path: path to file to be loaded.
        :param data: pre loaded YAML object (optional).
        :return: Bool to indicate the validity of the file.
        """
        try:
            submission_file_schema = json.load(
                    open(self.default_schema_file, 'r'))

            additional_file_section_schema = json.load(
                    open(self.additonal_info_schema, 'r'))

            # even though we are using the yaml package to load,
            # it supports JSON and YAML
            data = kwargs.pop("data", None)
            file_path = kwargs.pop("file_path", None)

            if file_path is None:
                raise LookupError("file_path argument must be supplied")

            if data is None:
                try:
                    # We try to load using the CLoader for speed improvements.
                    data = yaml.load_all(open(file_path, 'r'), Loader=yaml.CLoader)
                except Exception as e: #pragma: no cover
                    data = yaml.load_all(open(file_path, 'r')) #pragma: no cover

            for data_item in data:
                if data_item is None:
                    continue
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
            self.add_validation_message(
                    ValidationMessage(file=file_path,
                                      message='There was a problem parsing the file.  '
                                              'This can be because you forgot spaces '
                                              'after colons in your YAML file for instance.  '
                                              'Diagnostic information follows.\n' + str(se))
            )
            return False
