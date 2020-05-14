import os
import pytest
from hepdata_validator import VALID_SCHEMA_VERSIONS
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
    return DataFileValidator(schema_version='1.0.1')


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
    Tests the DataFileValidator V1 against an invalid YAML
    """

    file = os.path.join(data_path, 'invalid_file.yaml')
    is_valid = validator_v1.validate(file_path=file)
    validator_v1.print_errors(file)

    assert is_valid is False


def test_valid_yaml_file_with_percent_uncertainty_v1(validator_v1, data_path):
    """
    Tests the DataFileValidator V1 against a valid YAML with percentage uncertainties
    """

    file = os.path.join(data_path, 'valid_data_with_percent.yaml')
    is_valid = validator_v1.validate(file_path=file)
    validator_v1.print_errors(file)

    assert is_valid is True


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


def test_load_valid_custom_remote_data_and_path_v1(validator_v1, data_path):
    """
    Tests the DataFileValidator V1 against a valid remotely-defined schema
    """

    remote_schema_path = os.path.join(data_path, 'custom_remote_data_schema.json')
    remote_schema_type = 'my_remote_schema'

    validator_v1.load_custom_schema(remote_schema_type, remote_schema_path)

    file = os.path.join(data_path, 'valid_file_custom_remote.json')
    is_valid = validator_v1.validate(file_path=file, file_type=remote_schema_type)
    validator_v1.print_errors(file)

    assert is_valid is True


def test_validate_valid_custom_data_type(validator_v1, data_path):
    """
    Tests the validation of a custom file type, defined at validation time
    """

    file = os.path.join(data_path, 'valid_file_custom.yaml')
    is_valid = validator_v1.validate(file_path=file, file_type='different')
    validator_v1.print_errors(file)

    assert is_valid is True


def test_validate_undefined_data_type(validator_v1, data_path):
    """
    Tests the DataFileValidator V1 validation of an unsupported schema
    """

    file_path = os.path.join(data_path, 'valid_file_custom.yaml')
    file_type = 'undefined'

    is_valid = validator_v1.validate(file_path=file_path, file_type=file_type)
    errors = validator_v1.get_messages(file_name=file_path)

    assert is_valid is False
    assert len(errors) == 1


def test_load_undefined_custom_schema_v1(validator_v1):
    """
    Tests the DataFileValidator V1 loading of an unsupported schema
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
    assert validator_v1.has_errors(file) is True
    assert len(validator_v1.get_messages(file_name=file)) == 1

    validator_v1.print_errors(file)

    for msg in validator_v1.get_messages(file_name=file):
        assert msg.message.index("There was a problem parsing the file.") == 0


def test_invalid_parser_yaml_file_v1(validator_v1, data_path):
    """
    Tests the DataFileValidator V1 against an invalid parser file
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


def test_file_with_zero_uncertainty_v1(validator_v1, data_path):
    """
    Tests the DataFileValidator V1 against a file with zero uncertainties
    """
    file = os.path.join(data_path, 'file_with_zero_uncertainty.yaml')
    is_valid = validator_v1.validate(file_path=file)
    validator_v1.print_errors(file)

    assert is_valid is False


def test_file_with_zero_percent_v1(validator_v1, data_path):
    """
    Tests the DataFileValidator V1 against a file with zero percentage uncertainties
    """
    file = os.path.join(data_path, 'valid_data_with_zero_percent.yaml')
    is_valid = validator_v1.validate(file_path=file)
    validator_v1.print_errors(file)

    assert is_valid is False


def test_file_with_inconsistent_values_v1(validator_v1, data_path):
    """
    Tests the DataFileValidator V1 against a file with an inconsistent values list
    """
    file = os.path.join(data_path, 'file_with_inconsistent_values.yaml')
    is_valid = validator_v1.validate(file_path=file)
    validator_v1.print_errors(file)

    assert is_valid is False


def test_invalid_schema_version():
    """
    Tests the DataFileValidator creation with an invalid schema version
    """
    with pytest.raises(ValueError) as excinfo:
        validator = DataFileValidator(schema_version='0.9999.99')

    assert "Invalid schema version 0.9999.99" == str(excinfo.value)


def test_invalid_schema_file():
    """
    Tests the DataFileValidator creation with an invalid schema version
    Fudge the schema versions constant so we can check the file check works
    """
    VALID_SCHEMA_VERSIONS.append('0.9999.9999')
    try:
        with pytest.raises(ValueError) as excinfo:
            validator = DataFileValidator(schema_version='0.9999.9999')

        assert "Invalid schema file" in str(excinfo.value)
    finally:
        VALID_SCHEMA_VERSIONS.pop()
