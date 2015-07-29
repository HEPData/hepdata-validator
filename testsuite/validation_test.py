import os
import unittest
from hepdata_validator.data_file_validator import DataFileValidator
from hepdata_validator.submission_file_validator import SubmissionFileValidator

__author__ = 'eamonnmaguire'


class SubmissionFileValidationTest(unittest.TestCase):
    validator = None

    def setUp(self):
        self.base_dir = os.path.dirname(os.path.realpath(__file__))

        self.valid_license_file = 'test_data/valid_submission_license.yaml'
        self.valid_file = 'test_data/valid_submission.yaml'
        self.invalid_file = 'test_data/invalid_submission.yaml'

    def test_valid_submission_yaml(self):
        print '___SUBMISSION_FILE_VALIDATION: Testing valid yaml submission___'

        self.validator = None
        self.validator = SubmissionFileValidator()
        valid_sub_yaml = os.path.join(self.base_dir, self.valid_file)

        self.assertEqual(self.validator.validate(valid_sub_yaml), True)

        for error in self.validator.get_messages(valid_sub_yaml):
            print '\t', error.__unicode__()

        print 'Valid\n'

    def test_valid_submission_yaml_with_license(self):
        print '___SUBMISSION_FILE_VALIDATION: ' \
              'Testing valid yaml submission with license___'

        self.validator = None
        self.validator = SubmissionFileValidator()
        valid_sub_yaml = os.path.join(self.base_dir,
                                      self.valid_license_file)

        self.assertEqual(self.validator.validate(valid_sub_yaml), True)

        for error in self.validator.get_messages(valid_sub_yaml):
            print '\t', error.__unicode__()

        print 'Valid\n'

    def test_invalid_submission_yaml(self):
        print '___SUBMISSION_FILE_VALIDATION: ' \
              'Testing invalid yaml submission___'
        self.validator = None
        self.validator = SubmissionFileValidator()
        invalid_sub_yaml = os.path.join(self.base_dir, self.invalid_file)

        self.assertEqual(self.validator.validate(
            invalid_sub_yaml), False
        )

        for error in self.validator.get_messages(invalid_sub_yaml):
            print '\t', error.__unicode__()

        print 'Invalid\n'


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

    def test_valid_yaml_file(self):
        print '___DATA_VALIDATION: Testing valid yaml submission___'
        self.assertEqual(self.validator.validate(self.valid_file_yaml),
                         True)
        for error in self.validator.get_messages(self.valid_file_yaml):
            print '\t', error.__unicode__()
        print 'Valid\n'

    def test_invalid_yaml_file(self):
        print '___DATA_VALIDATION: Testing invalid yaml submission___'
        self.assertEqual(self.validator.validate(self.invalid_file_yaml),
                         False)
        for error in self.validator.get_messages(self.invalid_file_yaml):
            print '\t', error.__unicode__()
        print 'Invalid\n'

    def test_valid_json_file(self):
        print '___DATA_VALIDATION: Testing valid json submission___'
        self.assertEqual(self.validator.validate(self.valid_file_json),
                         True)
        for error in self.validator.get_messages(self.valid_file_json):
            print '\t', error.__unicode__()
        print 'VALID\n'

    def test_invalid_json_file(self):
        print '___DATA_VALIDATION: Testing invalid json submission___'
        self.assertEqual(self.validator.validate(self.invalid_file_json),
                         False)
        for error in self.validator.get_messages(self.invalid_file_json):
            print '\t', error.__unicode__()

        print 'Invalid\n'


if __name__ == '__main__':
    unittest.main()
