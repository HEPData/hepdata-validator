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
    return DataFileValidator()


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

    assert is_valid is True
    assert not validator_v1.has_errors(file)


def test_invalid_yaml_file_v1(validator_v1, data_path, capsys):
    """
    Tests the DataFileValidator V1 against an invalid YAML
    """

    file = os.path.join(data_path, 'invalid_file.yaml')
    is_valid = validator_v1.validate(file_path=file)
    validator_v1.print_errors(file)

    assert is_valid is False
    out, err = capsys.readouterr()
    lines = out.splitlines()
    assert lines[0].strip() == "error - 0.443 is not of type 'string' in 'dependent_variables[0].values[1].errors[0].label' (expected: {'type': 'string'})"
    assert lines[1].strip() == "error - Invalid error value 2.300e-003f: value must be a number (possibly ending in %) in 'dependent_variables.values[1].errors[2].symerror'"
    assert lines[2].strip() == "error - asymerror plus and minus cannot both be empty in 'dependent_variables.values[1].errors[3].asymerror'"
    assert lines[3].strip() == "error - symerror cannot be empty in 'dependent_variables.values[1].errors[4].symerror'"
    assert lines[4].strip() == "error - Inconsistent length of 'values' list: independent_variables [1], dependent_variables [2]"


def test_empty_yaml_file_v1(validator_v1, data_path, capsys):
    """
    Tests the DataFileValidator V1 against an empty file
    """

    file = os.path.join(data_path, 'empty_file.yaml')
    is_valid = validator_v1.validate(file_path=file)
    validator_v1.print_errors(file)

    assert is_valid is False
    out, err = capsys.readouterr()
    assert out.strip() == "error - No data found in file."


def test_valid_yaml_file_with_percent_uncertainty_v1(validator_v1, data_path):
    """
    Tests the DataFileValidator V1 against a valid YAML with percentage uncertainties
    """

    file = os.path.join(data_path, 'valid_data_with_percent.yaml')
    is_valid = validator_v1.validate(file_path=file)
    validator_v1.print_errors(file)

    assert is_valid is True
    assert not validator_v1.has_errors(file)


def test_valid_json_file_v1(validator_v1, data_path):
    """
    Tests the DataFileValidator V1 against a valid JSON
    """

    file = os.path.join(data_path, 'valid_file.json')
    is_valid = validator_v1.validate(file_path=file)

    assert is_valid is True
    assert not validator_v1.has_errors(file)


def test_invalid_json_file_v1(validator_v1, data_path, capsys):
    """
    Tests the DataFileValidator V1 against an invalid JSON
    """

    file = os.path.join(data_path, 'invalid_file.json')
    is_valid = validator_v1.validate(file_path=file)
    validator_v1.print_errors(file)

    assert is_valid is False
    out, err = capsys.readouterr()
    lines = out.splitlines()
    assert len(lines) == 3
    assert lines[0].strip() == "error - 'independent_variables' is a required property"
    assert lines[1].strip() == "error - 'dependent_variables' is a required property"
    assert lines[2].strip().startswith("error - Additional properties are not allowed")


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

    assert is_valid is True
    assert not validator_v1.has_errors(file)


def test_load_valid_custom_data_and_path_v1(validator_v1, data_path):
    """
    Tests the DataFileValidator V1 against a valid custom YAML
    """

    custom_schema_path = os.path.join(data_path, 'custom_data_schema.json')
    validator_v1.load_custom_schema('different', custom_schema_path)

    assert 'different' in validator_v1.custom_data_schemas

    file = os.path.join(data_path, 'valid_file_custom.yaml')
    is_valid = validator_v1.validate(file_path=file)

    assert is_valid is True
    assert not validator_v1.has_errors(file)


def test_load_valid_custom_remote_data_and_path_v1(validator_v1, data_path):
    """
    Tests the DataFileValidator V1 against a valid remotely-defined schema
    """

    remote_schema_path = os.path.join(data_path, 'custom_remote_data_schema.json')
    remote_schema_type = 'my_remote_schema'

    validator_v1.load_custom_schema(remote_schema_type, remote_schema_path)

    file = os.path.join(data_path, 'valid_file_custom_remote.json')
    is_valid = validator_v1.validate(file_path=file, file_type=remote_schema_type)

    assert is_valid is True
    assert not validator_v1.has_errors(file)


def test_validate_valid_custom_data_type(validator_v1, data_path):
    """
    Tests the validation of a custom file type, defined at validation time
    """

    file = os.path.join(data_path, 'valid_file_custom.yaml')
    is_valid = validator_v1.validate(file_path=file, file_type='different')

    assert is_valid is True
    assert not validator_v1.has_errors(file)


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

    for msg in validator_v1.get_messages(file_name=file):
        assert msg.message.index("There was a problem parsing the file.") == 0


def test_invalid_parser_yaml_file_v1(validator_v1, data_path, capsys):
    """
    Tests the DataFileValidator V1 against an invalid parser file
    """

    file = os.path.join(data_path, 'invalid_parser_file.yaml')
    is_valid = validator_v1.validate(file_path=file)
    validator_v1.print_errors(file)

    assert is_valid is False
    out, err = capsys.readouterr()
    assert out.strip().startswith(f"""error - There was a problem parsing the file.
while parsing a flow mapping
  in "{file}", line 9, column 9""")
    # message is different in libyaml and non-libyaml versions but this is in both
    assert "expected ',' or '}'" in out
    assert out.strip().endswith(f'in "{file}", line 10, column 5')


def test_io_error_yaml_file_v1(validator_v1, data_path, capsys):
    """
    Tests the DataFileValidator V1 against a non-found file
    """

    file = os.path.join(data_path, 'valid_file.yaml')
    file = file[:-1]

    is_valid = validator_v1.validate(file_path=file)
    validator_v1.print_errors(file)

    assert is_valid is False
    out, err = capsys.readouterr()
    assert out.strip() == f"error - There was a problem parsing the file.\n[Errno 2] No such file or directory: '{file}'"


def test_file_with_zero_uncertainty_v1(validator_v1, data_path, capsys):
    """
    Tests the DataFileValidator V1 against a file with zero uncertainties
    """
    file = os.path.join(data_path, 'file_with_zero_uncertainty.yaml')
    is_valid = validator_v1.validate(file_path=file)
    validator_v1.print_errors(file)

    assert is_valid is False
    out, err = capsys.readouterr()
    assert out.strip() == "error - Uncertainties should not all be zero in 'dependent_variables.values[1].errors'"


def test_file_with_zero_percent_v1(validator_v1, data_path, capsys):
    """
    Tests the DataFileValidator V1 against a file with zero percentage uncertainties
    """
    file = os.path.join(data_path, 'valid_data_with_zero_percent.yaml')
    is_valid = validator_v1.validate(file_path=file)
    validator_v1.print_errors(file)

    assert is_valid is False
    out, err = capsys.readouterr()
    assert out.strip() == "error - Uncertainties should not all be zero in 'dependent_variables.values[0].errors'"


def test_file_with_inconsistent_values_v1(validator_v1, data_path, capsys):
    """
    Tests the DataFileValidator V1 against a file with an inconsistent values list
    """
    file = os.path.join(data_path, 'file_with_inconsistent_values.yaml')
    is_valid = validator_v1.validate(file_path=file)
    validator_v1.print_errors(file)

    assert is_valid is False
    out, err = capsys.readouterr()
    assert out.strip() == "error - Inconsistent length of 'values' list: independent_variables [1], dependent_variables [2]"


def test_file_with_only_independent_variables_v1(validator_v1, data_path, capsys):
    """
    Tests the DataFileValidator V1 against a file with only independent variables
    Data file from https://www.hepdata.net/record/ins2624324?version=1&table=Binning%20Average
    """
    file = os.path.join(data_path, 'binning_average.yaml')
    is_valid = validator_v1.validate(file_path=file)
    validator_v1.print_errors(file)

    assert is_valid is False
    out, err = capsys.readouterr()
    assert out.strip() == "error - Case of only independent_variables but no dependent_variables is not supported: independent_variables [40, 40], dependent_variables []"


def test_file_with_invalid_independent_variables_v1(validator_v1, data_path, capsys):
    """
    Tests the DataFileValidator V1 against a file with invalid independent variables
    """
    file = os.path.join(data_path, 'invalid_independent_variables_file.yaml')
    is_valid = validator_v1.validate(file_path=file)
    validator_v1.print_errors(file)

    assert is_valid is False
    out, err = capsys.readouterr()
    lines = out.splitlines()
    assert len(lines) == 10
    assert lines[0].strip() == "error - {'low': 6000} is not valid under any of the given schemas in 'independent_variables[0].values[0]' (expected: {'oneOf': [{'type': 'object', 'properties': {'value': {'type': ['string', 'number']}}, 'required': ['value'], 'additionalProperties': False}, {'type': 'object', 'properties': {'value': {'type': 'number'}, 'low': {'type': 'number'}, 'high': {'type': 'number'}}, 'required': ['low', 'high'], 'additionalProperties': False}]})"
    assert lines[1].strip() == "error - {'high': 7000} is not valid under any of the given schemas in 'independent_variables[0].values[1]' (expected: {'oneOf': [{'type': 'object', 'properties': {'value': {'type': ['string', 'number']}}, 'required': ['value'], 'additionalProperties': False}, {'type': 'object', 'properties': {'value': {'type': 'number'}, 'low': {'type': 'number'}, 'high': {'type': 'number'}}, 'required': ['low', 'high'], 'additionalProperties': False}]})"
    assert lines[2].strip() == "error - {'high': '7.0.0', 'low': '2.0.0'} is not valid under any of the given schemas in 'independent_variables[0].values[2]' (expected: {'oneOf': [{'type': 'object', 'properties': {'value': {'type': ['string', 'number']}}, 'required': ['value'], 'additionalProperties': False}, {'type': 'object', 'properties': {'value': {'type': 'number'}, 'low': {'type': 'number'}, 'high': {'type': 'number'}}, 'required': ['low', 'high'], 'additionalProperties': False}]})"
    assert lines[3].strip() == "error - independent_variable 'value' must not be a string range (use 'low' and 'high' to represent a range): '800 - 1000' in 'independent_variables[0].values[3].value' (expected: {'type': 'number or string (not a range)'})"
    assert lines[4].strip() == "error - independent_variable 'value' must not be a string range (use 'low' and 'high' to represent a range): '-5.3--2' in 'independent_variables[0].values[4].value' (expected: {'type': 'number or string (not a range)'})"
    assert lines[5].strip() == "error - independent_variable 'value' must not be a string range (use 'low' and 'high' to represent a range): '+2.3E5 -  +5E12' in 'independent_variables[0].values[5].value' (expected: {'type': 'number or string (not a range)'})"
    assert lines[6].strip() == "error - independent_variable 'value' must not be a string range (use 'low' and 'high' to represent a range): '-1e-09 - -3.5e-08' in 'independent_variables[0].values[6].value' (expected: {'type': 'number or string (not a range)'})"
    assert lines[7].strip() == "error - independent_variable 'low' and 'high' must not both have infinite values: '-inf' and 'inf' in 'independent_variables[0].values[9]'"
    assert lines[8].strip() == "error - independent_variable must not have more than one underflow bin: (-inf, 0.0000e+00), (-inf, 1.0000e+00) in 'independent_variables[0].values[13]'"
    assert lines[9].strip() == "error - independent_variable must not have more than one overflow bin: (0.0000e+00, inf), (1.0000e+00, inf) in 'independent_variables[0].values[13]'"


def test_file_with_missing_dependent_values_v1(validator_v1, data_path, capsys):
    """
    Tests the DataFileValidator V1 against a file with missing dependent values
    """
    file = os.path.join(data_path, 'invalid_missing_values.yaml')
    is_valid = validator_v1.validate(file_path=file)
    validator_v1.print_errors(file)

    assert is_valid is False
    out, err = capsys.readouterr()
    assert out.strip() == "error - 'values' is a required property in 'dependent_variables[0]' (expected: {'type': 'object', 'properties': {'header': {'type': 'object', 'properties': {'name': {'type': 'string'}, 'units': {'type': 'string'}}, 'required': ['name'], 'additionalProperties': False}, 'qualifiers': {'type': 'array', 'items': {'type': 'object', 'properties': {'name': {'type': 'string'}, 'value': {'type': ['string', 'number']}, 'units': {'type': 'string'}}, 'required': ['name', 'value'], 'additionalProperties': False}}, 'values': {'type': 'array', 'items': {'type': 'object', 'properties': {'value': {'type': ['string', 'number']}, 'errors': {'type': 'array', 'items': {'type': 'object', 'properties': {'symerror': {'type': ['number', 'string']}, 'asymerror': {'type': 'object', 'properties': {'minus': {'type': ['number', 'string']}, 'plus': {'type': ['number', 'string']}}, 'required': ['minus', 'plus'], 'additionalProperties': False}, 'label': {'type': 'string'}}, 'oneOf': [{'required': ['symerror']}, {'required': ['asymerror']}], 'additionalProperties': False}}}, 'required': ['value'], 'additionalProperties': False}}}, 'required': ['header', 'values'], 'additionalProperties': False})"


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
