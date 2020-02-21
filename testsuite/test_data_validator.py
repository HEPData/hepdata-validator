import os
import pytest
from hepdata_validator.data_file_validator import DataFileValidator
from hepdata_validator.data_file_validator import UnsupportedDataSchemaException


####################################################
#                 Tests fixtures                   #
####################################################


@pytest.fixture(scope="module")
def data_path():
    base_dir = os.path.dirname(os.path.realpath(__file__))
    return os.path.join(base_dir, 'test_data')


@pytest.fixture(scope="module")
def validator_v0():
    return DataFileValidator(schema_version='0.1.0')


@pytest.fixture(scope="module")
def validator_v1():
    return DataFileValidator(schema_version='1.0.0')


####################################################
#            DataFileValidator V0 tests            #
####################################################


def test_valid_yaml_file_v0(validator_v0, data_path):
    """
    Tests the DataFileValidator V0 against a valid YAML
    """

    assert 'schemas/0.1.0/data_schema.json' in validator_v0.default_schema_file

    file = os.path.join(data_path, 'valid_file.yaml')
    is_valid = validator_v0.validate(file_path=file)
    validator_v0.print_errors(file)

    assert is_valid is True


def test_valid_json_file_v0(validator_v0, data_path):
    """
    Tests the DataFileValidator V0 against a valid JSON
    """

    assert 'schemas/0.1.0/data_schema.json' in validator_v0.default_schema_file

    file = os.path.join(data_path, 'valid_file.json')
    is_valid = validator_v0.validate(file_path=file)
    validator_v0.print_errors(file)

    assert is_valid is True


####################################################
#            DataFileValidator V1 tests            #
####################################################


def test_no_file_path_v1(validator_v1):
    """
    Tests the DataFileValidator V1 against a non-existing file path
    """

    with pytest.raises(LookupError):
        validator_v1.validate(file_path=None)


def test_valid_yaml_file_v1(validator_v1, data_path):
    """
    Tests the DataFileValidator V1 against a valid YAML
    """

    file = os.path.join(data_path, 'valid_file.yaml')
    is_valid = validator_v1.validate(file_path=file)
    validator_v1.print_errors(file)

    assert is_valid is True


def test_invalid_yaml_file_v1(validator_v1, data_path):
    """
    Tests the DataFileValidator V1 against an invalid JSON
    """

    file = os.path.join(data_path, 'invalid_file.yaml')
    is_valid = validator_v1.validate(file_path=file)
    validator_v1.print_errors(file)

    assert is_valid is False


def test_valid_yaml_file_with_percent_errors_v1(validator_v1, data_path):
    """
    Tests the DataFileValidator V1 against a valid YAML with some errors
    """

    file = os.path.join(data_path, 'valid_data_with_error.yaml')
    is_valid = validator_v1.validate(file_path=file)
    validator_v1.print_errors(file)

    assert is_valid is False


def test_valid_json_file_v1(validator_v1, data_path):
    """
    Tests the DataFileValidator V1 against a valid JSON
    """

    file = os.path.join(data_path, 'valid_file.json')
    is_valid = validator_v1.validate(file_path=file)
    validator_v1.print_errors(file)

    assert is_valid is True


def test_invalid_json_file_v1(validator_v1, data_path):
    """
    Tests the DataFileValidator V1 against an invalid JSON
    """

    file = os.path.join(data_path, 'invalid_file.json')
    is_valid = validator_v1.validate(file_path=file)
    validator_v1.print_errors(file)

    assert is_valid is False


def test_load_valid_custom_data_v1(validator_v1, data_path):
    """
    Tests the DataFileValidator V1 against a valid custom JSON
    """

    # This is actually one of the default schemas
    # but it allows testing of custom files in the default path
    validator_v1.load_custom_schema('data')

    assert 'data' in validator_v1.custom_data_schemas

    file = os.path.join(data_path, 'valid_file.json')
    is_valid = validator_v1.validate(file_path=file)
    validator_v1.print_errors(file)

    assert is_valid is True


def test_load_valid_custom_data_and_path_v1(validator_v1, data_path):
    """
    Tests the DataFileValidator V1 against a valid custom YAML
    """

    custom_schema_path = os.path.join(data_path, 'custom_data_schema.json')
    validator_v1.load_custom_schema('different', custom_schema_path)

    assert 'different' in validator_v1.custom_data_schemas

    file = os.path.join(data_path, 'valid_file_custom.yaml')
    is_valid = validator_v1.validate(file_path=file)
    validator_v1.print_errors(file)

    assert is_valid is True


def test_load_invalid_custom_schema_v1(validator_v1, data_path):
    """
    Tests the DataFileValidator V1 against an unsupported schema
    """

    validator_v1.custom_data_schemas = {}

    try:
        validator_v1.load_custom_schema('different')
    except UnsupportedDataSchemaException as udse:
        assert udse.message == "There is no schema defined for the 'different' data type."
        assert udse.message == udse.__unicode__()


def test_invalid_syntax_data_file_v1(validator_v1, data_path):
    """
    Tests the DataFileValidator V1 against an invalid syntax YAML
    """

    file = os.path.join(data_path, 'invalid_data_file.yaml')

    assert validator_v1.validate(file_path=file) is False
    assert validator_v1.has_errors(file_name=file) is True
    assert len(validator_v1.get_messages(file_name=file)) == 1

    validator_v1.print_errors(file)

    for msg in validator_v1.get_messages(file_name=file):
        assert msg.message.index("There was a problem parsing the file.") == 0


def test_invalid_parser_yaml_file_v1(validator_v1, data_path):
    """
    Tests the DataFileValidator V1 against an in invalid parser file
    """

    file = os.path.join(data_path, 'invalid_parser_file.yaml')
    is_valid = validator_v1.validate(file_path=file)
    validator_v1.print_errors(file)

    assert is_valid is False


def test_io_error_yaml_file_v1(validator_v1, data_path):
    """
    Tests the DataFileValidator V1 against a non-found file
    """

    file = os.path.join(data_path, 'valid_file.yaml')
    file = file[:-1]

    is_valid = validator_v1.validate(file_path=file)
    validator_v1.print_errors(file)

    assert is_valid is False
