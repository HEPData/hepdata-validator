import os
import unittest

import yaml

# We try to load using the CSafeLoader for speed improvements.
try:
    from yaml import CSafeLoader as Loader
except ImportError: #pragma: no cover
    from yaml import SafeLoader as Loader #pragma: no cover

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

    def test_valid_v0_submission_yaml_against_v1(self):
        print('___SUBMISSION_FILE_VALIDATION: Testing valid v0 yaml submission against v1 schema___')

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


if __name__ == '__main__':
    unittest.main()
