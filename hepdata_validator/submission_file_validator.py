import json
from jsonschema import validate, ValidationError
import os
import re
import yaml
from yaml.scanner import ScannerError

# We try to load using the CSafeLoader for speed improvements.
try:
    from yaml import CSafeLoader as Loader
except ImportError: #pragma: no cover
    from yaml import SafeLoader as Loader #pragma: no cover

from hepdata_validator import Validator, ValidationMessage

__author__ = 'eamonnmaguire'


class SubmissionFileValidator(Validator):
    """
    Validates the Submission file YAML/JSON file.
    """
    base_path = os.path.dirname(__file__)
    submission_filename = 'submission_schema.json'
    additional_info_filename = 'additional_info_schema.json'

    def __init__(self, *args, **kwargs):
        super(SubmissionFileValidator, self).__init__(*args, **kwargs)
        self.default_schema_file = self._get_schema_filepath(self.submission_filename)
        self.additional_info_schema = self._get_schema_filepath(self.additional_info_filename)

    def validate(self, **kwargs):
        """
        Validates a submission file.

        :param file_path: path to file to be loaded.
        :param data: pre loaded YAML object (optional).
        :return: Bool to indicate the validity of the file.
        """
        data_file_handle = None
        return_value = False

        try:
            submission_file_schema = None
            additional_file_section_schema = None
            
            with open(self.default_schema_file, 'r') as submission_schema:
                submission_file_schema = json.load(submission_schema)

            with open(self.additional_info_schema, 'r') as additional_schema:
                additional_file_section_schema = json.load(additional_schema)

            # even though we are using the yaml package to load,
            # it supports JSON and YAML
            data = kwargs.pop("data", None)
            file_path = kwargs.pop("file_path", None)

            if file_path is None:
                raise LookupError("file_path argument must be supplied")

            if data is None:
                data_file_handle = open(file_path, 'r')
                data = yaml.load_all(data_file_handle, Loader=Loader)

            for data_item_index, data_item in enumerate(data):
                if data_item is None:
                    continue
                try:
                    if not data_item_index and 'data_file' not in data_item:
                        validate(data_item, additional_file_section_schema)
                    else:
                        validate(data_item, submission_file_schema)
                        if self._get_major_version() > 0:
                            check_cmenergies(data_item)

                except ValidationError as ve:
                    self.add_validation_message(
                            ValidationMessage(file=file_path,
                                                message=ve.message + ' in ' + str(ve.instance)))

            if not self.has_errors(file_path):
                return_value = True

        except LookupError as le:
            raise le

        except ScannerError as se:  # pragma: no cover
            self.add_validation_message(  # pragma: no cover
                ValidationMessage(file=file_path, message=
                    'There was a problem parsing the file.  '
                    'This can be because you forgot spaces '
                    'after colons in your YAML file for instance.  '
                    'Diagnostic information follows.\n' + str(se)))
            return_value = False

        except Exception as e:
            self.add_validation_message(ValidationMessage(file=file_path, message=e.__str__()))
            return_value = False

        finally:
            if data_file_handle:
                data_file_handle.close()

        return return_value


def check_cmenergies(data_item):
    """
    Check that 'cmenergies' values are numeric unless a range like 1.7-4.7.

    :param data_item: YAML document from submission.yaml
    :return: raise ValidationError if not numeric
    """
    for keyword in data_item['keywords']:
        if keyword['name'] == 'cmenergies':
            cmenergies = keyword['values']
            for cmenergy in cmenergies:
                try:
                    cmenergy = float(cmenergy)
                except ValueError:
                    m = re.match(r'^\d+\.?\d?-\d+\.?\d?$', cmenergy)
                    if not m or len(cmenergies) > 1:
                        raise ValidationError("Invalid value (in GeV) for cmenergies: %s" % cmenergy,
                                              instance=data_item)