import os
import unittest

import yaml

# We try to load using the CSafeLoader for speed improvements.
try:
    from yaml import CSafeLoader as Loader
except ImportError: #pragma: no cover
    from yaml import SafeLoader as Loader #pragma: no cover

from hepdata_validator.data_file_validator import DataFileValidator, UnsupportedDataSchemaException
from hepdata_validator.submission_file_validator import SubmissionFileValidator


class SubmissionFileValidationTest(unittest.TestCase):
    validator = None

    def setUp(self):
        self.base_dir = os.path.dirname(os.path.realpath(__file__))

        self.valid_license_file = 'test_data/valid_submission_license.yaml'
        self.valid_file = 'test_data/valid_submission.yaml'
        self.valid_v0_file = 'test_data/valid_submission_v0.yaml'
        self.valid_file_with_associated_records = 'test_data/valid_submission_with_associated_record.yaml'
        self.valid_empty_file = 'test_data/valid_submission_empty.yaml'
        self.invalid_file = 'test_data/invalid_submission.yaml'
        self.invalid_syntax_file = 'test_data/invalid_syntax_submission.yaml'
        self.invalid_parser_file = 'test_data/invalid_parser_submission.yaml'

    def test_valid_submission_yaml(self):
        print('___SUBMISSION_FILE_VALIDATION: Testing valid yaml submission___')

        self.validator = None
        self.validator = SubmissionFileValidator()
        valid_sub_yaml = os.path.join(self.base_dir, self.valid_file)
        sub_yaml_obj = yaml.load_all(open(valid_sub_yaml, 'r'), Loader=Loader)
        self.assertEqual(
            self.validator.validate(file_path=valid_sub_yaml, data=sub_yaml_obj),
            True
        )
        self.validator.print_errors(valid_sub_yaml)

    def test_valid_v0_submission_yaml(self):
        print('___SUBMISSION_FILE_VALIDATION: Testing valid v0 yaml submission___')

        self.validator = None
        self.validator = SubmissionFileValidator(schema_version='0.1.0')
        valid_sub_yaml = os.path.join(self.base_dir, self.valid_v0_file)
        sub_yaml_obj = yaml.load_all(open(valid_sub_yaml, 'r'), Loader=Loader)
        self.assertEqual(
            self.validator.validate(file_path=valid_sub_yaml, data=sub_yaml_obj),
            True
        )
        self.validator.print_errors(valid_sub_yaml)

    def test_valid_v0_submission_yaml_against_v2(self):
        print('___SUBMISSION_FILE_VALIDATION: Testing valid v0 yaml submission against v2 schema___')

        self.validator = None
        self.validator = SubmissionFileValidator()
        valid_sub_yaml = os.path.join(self.base_dir, self.valid_v0_file)
        sub_yaml_obj = yaml.load_all(open(valid_sub_yaml, 'r'), Loader=Loader)
        self.assertEqual(
            self.validator.validate(file_path=valid_sub_yaml, data=sub_yaml_obj),
            False
        )
        self.validator.print_errors(valid_sub_yaml)

    def test_no_file_path_supplied(self):
        self.validator = SubmissionFileValidator()
        try:
            self.validator.validate(file_path=None)
        except LookupError as le:
            assert (le)

    def test_invalid_syntax(self):
        self.validator = SubmissionFileValidator()
        invalid_syntax_file = os.path.join(self.base_dir, self.invalid_syntax_file)

        self.assertFalse(self.validator.validate(file_path=invalid_syntax_file))

        self.assertTrue(self.validator.has_errors(invalid_syntax_file))
        self.assertTrue(len(self.validator.get_messages(invalid_syntax_file)) == 1)
        self.validator.print_errors(invalid_syntax_file)
        for message in self.validator.get_messages(invalid_syntax_file):
            print(message.message)
            self.assertTrue(message.message.index("There was a problem parsing the file.") == 0)

        self.assertTrue(len(self.validator.get_messages()) == 1)
        self.validator.clear_messages()
        self.assertTrue(len(self.validator.get_messages()) == 0)

    def test_valid_submission_yaml_with_associated_records(self):
        print('___SUBMISSION_FILE_VALIDATION: Testing valid yaml submission with associated records___')

        self.validator = None
        self.validator = SubmissionFileValidator()
        valid_sub_yaml = os.path.join(self.base_dir, self.valid_file_with_associated_records)
        is_valid = self.validator.validate(file_path=valid_sub_yaml)
        self.validator.print_errors(valid_sub_yaml)

        self.assertTrue(is_valid)
        self.assertTrue(not self.validator.has_errors(valid_sub_yaml))

    def test_valid_submission_yaml_with_empty_section(self):
        print('___SUBMISSION_FILE_VALIDATION: Testing valid yaml ' \
              'submission without main section___')

        self.validator = None
        self.validator = SubmissionFileValidator()
        valid_sub_yaml = os.path.join(self.base_dir, self.valid_empty_file)

        self.assertEqual(self.validator.validate(file_path=valid_sub_yaml), True)
        self.validator.print_errors(valid_sub_yaml)

    def test_valid_submission_yaml_with_license(self):
        print('___SUBMISSION_FILE_VALIDATION: ' \
              'Testing valid yaml submission with license___')

        self.validator = None
        self.validator = SubmissionFileValidator()
        valid_sub_yaml = os.path.join(self.base_dir,
                                      self.valid_license_file)

        is_valid = self.validator.validate(file_path=valid_sub_yaml)
        self.validator.print_errors(valid_sub_yaml)
        self.assertEqual(is_valid, True)

    def test_invalid_submission_yaml(self):
        print('___SUBMISSION_FILE_VALIDATION: ' \
              'Testing invalid yaml submission___')
        self.validator = None
        self.validator = SubmissionFileValidator()
        invalid_sub_yaml = os.path.join(self.base_dir, self.invalid_file)

        self.assertEqual(self.validator.validate(
            file_path=invalid_sub_yaml), False
        )

        self.validator.print_errors(invalid_sub_yaml)

    def test_invalid_parser_submission_yaml(self):
        print('___SUBMISSION_FILE_VALIDATION: ' \
              'Testing invalid parser yaml submission___')
        self.validator = None
        self.validator = SubmissionFileValidator()
        invalid_sub_yaml = os.path.join(self.base_dir, self.invalid_parser_file)

        self.assertEqual(self.validator.validate(
            file_path=invalid_sub_yaml), False
        )

        self.validator.print_errors(invalid_sub_yaml)

    def test_ioerror_submission_yaml(self):
        print('___SUBMISSION_FILE_VALIDATION: ' \
              'Testing ioerror yaml submission___')
        self.validator = None
        self.validator = SubmissionFileValidator()
        invalid_sub_yaml = os.path.join(self.base_dir, self.valid_file[:-1])

        self.assertEqual(self.validator.validate(
            file_path=invalid_sub_yaml), False
        )

        self.validator.print_errors(invalid_sub_yaml)


class DataValidationTest(unittest.TestCase):
    validator = None

    def setUp(self):
        self.validator = DataFileValidator()
        self.base_dir = os.path.dirname(os.path.realpath(__file__))

        self.invalid_file_yaml = os.path.join(
            self.base_dir,
            'test_data/invalid_file.yaml'
        )

        self.valid_file_yaml = os.path.join(
            self.base_dir,
            'test_data/valid_file.yaml'
        )

        self.valid_file_json = os.path.join(
            self.base_dir,
            'test_data/valid_file.json'
        )

        self.invalid_file_json = os.path.join(
            self.base_dir,
            'test_data/invalid_file.json')

        self.valid_file_error_percent_yaml = os.path.join(
            self.base_dir,
            'test_data/valid_data_with_error.yaml'
        )

        self.invalid_syntax_data_file = os.path.join(
            self.base_dir,
            'test_data/invalid_data_file.yaml'
        )

        self.invalid_parser_file = os.path.join(
            self.base_dir,
            'test_data/invalid_parser_file.yaml'
        )

        self.valid_custom_file = os.path.join(
            self.base_dir,
            'test_data/valid_file_custom.yaml')

    def test_no_file_path_supplied(self):
        try:
            self.validator.validate(file_path=None)
        except LookupError as le:
            assert (le)

    def test_valid_yaml_file(self):
        print('___DATA_VALIDATION: Testing valid yaml submission___')
        is_valid = self.validator.validate(file_path=self.valid_file_yaml)
        self.validator.print_errors(self.valid_file_yaml)
        self.assertEqual(is_valid, True)

    def test_invalid_yaml_file(self):
        print('___DATA_VALIDATION: Testing invalid yaml submission___')
        self.assertEqual(self.validator.validate(file_path=self.invalid_file_yaml),
                         False)

        self.validator.print_errors(self.invalid_file_yaml)

    def test_valid_file_with_percent_errors(self):
        print('___DATA_VALIDATION: Testing valid yaml percent error ___')
        self.assertEqual(self.validator.validate(file_path=self.valid_file_error_percent_yaml),
                         False)
        self.validator.print_errors(self.valid_file_error_percent_yaml)

    def test_valid_json_file(self):
        print('___DATA_VALIDATION: Testing valid json submission___')
        is_valid = self.validator.validate(file_path=self.valid_file_json)
        self.validator.print_errors(self.valid_file_json)
        self.assertEqual(is_valid, True)

        self.validator.print_errors(self.valid_file_json)

    def test_valid_yaml_file_against_v0(self):
        print('___DATA_VALIDATION: Testing valid yaml submission against v0___')
        validator = DataFileValidator(schema_version='0.1.0')
        self.assertTrue('schemas/0.1.0/data_schema.json' in validator.default_schema_file)
        is_valid = validator.validate(file_path=self.valid_file_yaml)
        validator.print_errors(self.valid_file_yaml)
        self.assertEqual(is_valid, True)

    def test_valid_json_file_against_v0(self):
        print('___DATA_VALIDATION: Testing valid json submission against v0___')
        validator = DataFileValidator(schema_version='0.1.0')
        self.assertTrue('schemas/0.1.0/data_schema.json' in validator.default_schema_file)
        is_valid = validator.validate(file_path=self.valid_file_json)
        self.assertEqual(is_valid, True)
        validator.print_errors(self.valid_file_json)

    def test_invalid_json_file(self):
        print('___DATA_VALIDATION: Testing invalid json submission___')
        self.assertEqual(self.validator.validate(file_path=self.invalid_file_json),
                         False)
        self.validator.print_errors(self.invalid_file_json)

    def test_load_data_with_custom_data_type(self):
        self.validator = DataFileValidator()
        custom_schema_path = os.path.join(self.base_dir, 'test_data/custom_data_schema.json')
        self.validator.load_custom_schema('different', custom_schema_path)

        self.assertTrue('different' in self.validator.custom_data_schemas)

        self.assertTrue(self.validator.validate(file_path=self.valid_custom_file))

    def test_load_invalid_custom_schema(self):
        self.validator.custom_data_schemas = {}
        print('Loading invalid schema')
        try:
            self.validator.load_custom_schema('different')
        except UnsupportedDataSchemaException as udse:
            self.assertTrue(udse.message == "There is no schema defined for the 'different' data type.")
            self.assertTrue(udse.message == udse.__unicode__())

    def test_load_invalid_data_file(self):

        print('Loading invalid data file')

        self.assertFalse(self.validator.validate(file_path=self.invalid_syntax_data_file))

        self.assertTrue(self.validator.has_errors(self.invalid_syntax_data_file))
        self.assertTrue(len(self.validator.get_messages(self.invalid_syntax_data_file)) == 1)
        self.validator.print_errors(self.invalid_syntax_data_file)
        for message in self.validator.get_messages(self.invalid_syntax_data_file):
            self.assertTrue(message.message.index("There was a problem parsing the file.") == 0)

    def test_invalid_parser_yaml_file(self):
        print('___DATA_VALIDATION: Testing invalid parser yaml submission___')
        self.assertEqual(self.validator.validate(file_path=self.invalid_parser_file),
                         False)

        self.validator.print_errors(self.invalid_parser_file)

    def test_ioerror_yaml_file(self):
        print('___DATA_VALIDATION: Testing ioerror yaml submission___')
        self.assertEqual(self.validator.validate(file_path=self.valid_file_yaml[:-1]),
                         False)

        self.validator.print_errors(self.valid_file_yaml[:-1])


if __name__ == '__main__':
    unittest.main()
