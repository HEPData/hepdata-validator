import os
import pytest
import yaml
from hepdata_validator import VALID_SCHEMA_VERSIONS
from hepdata_validator.submission_file_validator import SubmissionFileValidator

# We try to load using the CSafeLoader for speed improvements.
try:
    from yaml import CSafeLoader as Loader
except ImportError:
    from yaml import SafeLoader as Loader


####################################################
#                 Tests fixtures                   #
####################################################


@pytest.fixture(scope="module")
def data_path():
    base_dir = os.path.dirname(os.path.realpath(__file__))
    return os.path.join(base_dir, 'test_data')


@pytest.fixture(scope="module")
def validator_v0():
    return SubmissionFileValidator(schema_version='0.1.0')


@pytest.fixture(scope="module")
def validator_v1():
    return SubmissionFileValidator(schema_version='1.0.1')


####################################################
#         SubmissionFileValidator V0 tests         #
####################################################


def test_valid_submission_yaml_v0(validator_v0, data_path):
    """
    Tests the SubmissionFileValidator V0 against a valid YAML
    """

    file = os.path.join(data_path, 'valid_submission_v0.yaml')

    with open(file, 'r') as submission:
        yaml_obj = yaml.load_all(submission, Loader=Loader)
        is_valid = validator_v0.validate(file_path=file, data=yaml_obj)
        validator_v0.print_errors(file)

        assert is_valid is True


####################################################
#         SubmissionFileValidator V1 tests         #
####################################################


def test_valid_submission_yaml_v1(validator_v1, data_path):
    """
    Tests the SubmissionFileValidator V1 against a valid YAML
    """

    file = os.path.join(data_path, 'valid_submission.yaml')

    with open(file, 'r') as submission:
        yaml_obj = yaml.load_all(submission, Loader=Loader)
        is_valid = validator_v1.validate(file_path=file, data=yaml_obj)
        validator_v1.print_errors(file)

        assert is_valid is True


def test_v0_valid_submission_yaml_v1(validator_v1, data_path):
    """
    Tests the SubmissionFileValidator V1 against a valid V0-schema YAML
    """

    file = os.path.join(data_path, 'valid_submission_v0.yaml')

    with open(file, 'r') as submission:
        yaml_obj = yaml.load_all(submission, Loader=Loader)
        is_valid = validator_v1.validate(file_path=file, data=yaml_obj)
        validator_v1.print_errors(file)

        assert is_valid is False


def test_no_file_path_v1(validator_v1):
    """
    Tests the SubmissionFileValidator V1 against a non-existing file path
    """

    with pytest.raises(LookupError):
        validator_v1.validate(file_path=None)


def test_invalid_syntax_v1(validator_v1, data_path):
    """
    Tests the SubmissionFileValidator V1 against an invalid syntax YAML
    """

    file = os.path.join(data_path, 'invalid_syntax_submission.yaml')

    assert validator_v1.validate(file_path=file) is False
    assert validator_v1.has_errors(file) is True
    assert len(validator_v1.get_messages(file_name=file)) == 1

    validator_v1.print_errors(file)

    for msg in validator_v1.get_messages(file_name=file):
        assert msg.message.index("There was a problem parsing the file.") == 0


def test_clear_messages_v1(validator_v1):
    """
    Tests the SubmissionFileValidator V1 clear messages function
    """

    validator_v1.messages = {'non-empty'}
    validator_v1.clear_messages()

    assert len(validator_v1.get_messages()) == 0


def test_valid_submission_yaml_with_records_v1(validator_v1, data_path):
    """
    Tests the SubmissionFileValidator V1 against a valid YAML with records
    """

    file = os.path.join(data_path, 'valid_submission_with_associated_record.yaml')
    is_valid = validator_v1.validate(file_path=file)
    validator_v1.print_errors(file)

    assert is_valid is True
    assert validator_v1.has_errors(file) is False


def test_valid_submission_yaml_with_empty_section_v1(validator_v1, data_path):
    """
    Tests the SubmissionFileValidator V1 against a valid YAML with empty section
    """

    file = os.path.join(data_path, 'valid_submission_empty.yaml')
    is_valid = validator_v1.validate(file_path=file)
    validator_v1.print_errors(file)

    assert is_valid is True


def test_valid_submission_yaml_with_license_v1(validator_v1, data_path):
    """
    Tests the SubmissionFileValidator V1 against a valid YAML with license
    """

    file = os.path.join(data_path, 'valid_submission_license.yaml')
    is_valid = validator_v1.validate(file_path=file)
    validator_v1.print_errors(file)

    assert is_valid is True


def test_invalid_submission_yaml_v1(validator_v1, data_path):
    """
    Tests the SubmissionFileValidator V1 against an invalid YAML
    """

    file = os.path.join(data_path, 'invalid_submission.yaml')
    is_valid = validator_v1.validate(file_path=file)
    validator_v1.print_errors(file)

    assert is_valid is False


def test_invalid_parser_submission_yaml_v1(validator_v1, data_path):
    """
    Tests the SubmissionFileValidator V1 against an invalid parser YAML
    """

    file = os.path.join(data_path, 'invalid_parser_submission.yaml')
    is_valid = validator_v1.validate(file_path=file)
    validator_v1.print_errors(file)

    assert is_valid is False


def test_io_error_submission_yaml_v1(validator_v1, data_path):
    """
    Tests the SubmissionFileValidator V1 against a non-found file
    """

    file = os.path.join(data_path, 'valid_submission.yaml')
    file = file[:-1]

    is_valid = validator_v1.validate(file_path=file)
    validator_v1.print_errors(file)

    assert is_valid is False


def test_invalid_schema_version():
    with pytest.raises(ValueError) as excinfo:
        validator = SubmissionFileValidator(schema_version='0.9999.99')

    assert "Invalid schema version 0.9999.99" == str(excinfo.value)


def test_invalid_schema_file():
    # Fudge the schema versions constant so we can check the file check works
    VALID_SCHEMA_VERSIONS.append('0.9999.9999')
    try:
        with pytest.raises(ValueError) as excinfo:
            validator = SubmissionFileValidator(schema_version='0.9999.9999')

        assert "Invalid schema file" in str(excinfo.value)
    finally:
        VALID_SCHEMA_VERSIONS.pop()


def test_data_schema_submission_yaml_v1(validator_v1, data_path):
    """
    Tests the SubmissionFileValidator V1 against a valid YAML with a data_schema key
    """

    file = os.path.join(data_path, 'valid_submission_custom_remote.yaml')

    with open(file, 'r') as submission:
        yaml_obj = yaml.load_all(submission, Loader=Loader)
        is_valid = validator_v1.validate(file_path=file, data=yaml_obj)
        validator_v1.print_errors(file)

        assert is_valid is True


def test_invalid_cmenergies_submission_yaml_v1(validator_v1, data_path):
    """
    Tests the SubmissionFileValidator V1 against an invalid cmenergies value
    """

    file = os.path.join(data_path, 'invalid_cmenergies.yaml')

    with open(file, 'r') as submission:
        yaml_obj = yaml.load_all(submission, Loader=Loader)
        is_valid = validator_v1.validate(file_path=file, data=yaml_obj)
        validator_v1.print_errors(file)

        assert is_valid is False