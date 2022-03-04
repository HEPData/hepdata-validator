import json
from jsonschema import ValidationError, RefResolver
import os
from packaging import version as packaging_version
import re
import yaml
from yaml.scanner import ScannerError

from hepdata_validator import Validator, ValidationMessage, YamlLoader

__author__ = 'eamonnmaguire'


class SubmissionFileValidator(Validator):
    """
    Validates the Submission file YAML/JSON file.
    """
    base_path = os.path.dirname(__file__)
    submission_filename = 'submission_schema.json'
    additional_info_filename = 'additional_info_schema.json'
    additional_resources_filename = 'additional_resources_schema.json'

    def __init__(self, *args, **kwargs):
        super(SubmissionFileValidator, self).__init__(*args, **kwargs)
        self.default_schema_file = self._get_schema_filepath(self.submission_filename)
        self.additional_info_schema = self._get_schema_filepath(self.additional_info_filename)
        if self.schema_version >= packaging_version.parse("1.1.0"):
            self.additional_resources_schema = self._get_schema_filepath(self.additional_resources_filename)

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

            resolver = None
            if self.schema_version >= packaging_version.parse("1.1.0"):
                with open(self.additional_resources_schema, 'r') as additional_schema:
                    additional_resources_schema = json.load(additional_schema)

                resolver = RefResolver.from_schema(additional_resources_schema)

            # even though we are using the yaml package to load,
            # it supports JSON and YAML
            data = kwargs.pop("data", None)
            file_path = kwargs.pop("file_path", None)

            if file_path is None:
                raise LookupError("file_path argument must be supplied")

            if data is None:
                data_file_handle = open(file_path, 'r')
                data = yaml.load_all(data_file_handle, Loader=YamlLoader)

            table_names = []
            table_data_files = []
            has_submission_doc = False
            for data_item_index, data_item in enumerate(data):
                if data_item is None:
                    continue
                try:
                    if not data_item_index and 'data_file' not in data_item:
                        self._validate_json_against_schema(
                            file_path,
                            data_item,
                            additional_file_section_schema,
                            resolver=resolver
                        )
                    else:
                        self._validate_json_against_schema(
                            file_path,
                            data_item,
                            submission_file_schema,
                            resolver=resolver
                        )
                        has_submission_doc = True
                        if not self.has_errors(file_path) and self.schema_version.major > 0:
                            check_cmenergies(data_item)
                            table_names.append(data_item['name'])
                            table_data_files.append(data_item['data_file'])

                except ValidationError as ve:
                    self.add_validation_error(file_path, ve)

            if not has_submission_doc and self.schema_version >= packaging_version.parse("1.1.0"):
                # It's possible that all data items match the additional_file_section_schema
                # just by having properties that don't match any items in there. So we need
                # to make sure that we have at least one valid submission doc.
                self.add_validation_message(
                    ValidationMessage(
                        file=file_path,
                        message='There should be at least one document matching the submission schema.'
                    )
                )


            if self.schema_version >= packaging_version.parse("1.1.0"):
                self.check_for_duplicates(file_path, table_names, table_data_files)

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

    def check_for_duplicates(self, file_path, table_names, table_data_files):
        for (key, items) in [('name', table_names), ('data_file', table_data_files)]:
            seen = set()
            duplicates = []

            for x in items:
                if x not in seen:
                    seen.add(x)
                elif x not in duplicates:
                    duplicates.append(x)

            if duplicates:
                for d in duplicates:
                    self.add_validation_message(ValidationMessage(
                        file=file_path,
                        message=f"Duplicate table {key}: {d}"
                    ))


def check_cmenergies(data_item):
    """
    Check that 'cmenergies' values are numeric unless a range like 1.7-4.7.

    :param data_item: YAML document from submission.yaml
    :return: raise ValidationError if not numeric
    """
    for i, keyword in enumerate(data_item['keywords']):
        if keyword['name'] == 'cmenergies':
            cmenergies = keyword['values']
            for cmenergy in cmenergies:
                try:
                    cmenergy = float(cmenergy)
                except ValueError:
                    m = re.match(r'^\d+\.?\d*-\d+\.?\d*$', cmenergy)
                    if not m or len(cmenergies) > 1:
                        raise ValidationError("Invalid value (in GeV) for cmenergies: '%s'" % cmenergy,
                                              path=['keywords', i, 'name', 'cmenergies'],
                                              instance=data_item['keywords'],
                                              schema={ "type": "number or hyphen-separated range of numbers e.g. 1.7-4.7"})
