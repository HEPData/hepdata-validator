import os

import pytest

from hepdata_validator.full_submission_validator import FullSubmissionValidator


@pytest.fixture(scope="module")
def data_path():
    base_dir = os.path.dirname(os.path.realpath(__file__))
    return os.path.join(base_dir, 'test_data')


@pytest.fixture(scope="module")
def validator_v0():
    return FullSubmissionValidator(schema_version='0.1.0')


@pytest.fixture()
def validator_v1():
    return FullSubmissionValidator(schema_version='1.0.2')


def test_valid_submission_dir(validator_v1, data_path, capsys):
    submission_dir = os.path.join(data_path, 'TestHEPSubmission')
    is_valid = validator_v1.validate(directory=submission_dir)
    assert is_valid

    validator_v1.print_valid_files()
    out, err = capsys.readouterr()
    assert out == """	 {0}/submission.yaml is valid HEPData YAML.
	 {0}/data1.yaml is valid HEPData YAML.
	 {0}/data2.yaml is valid HEPData YAML.
	 {0}/data3.yaml is valid HEPData YAML.
	 {0}/data4.yaml is valid HEPData YAML.
	 {0}/data5.yaml is valid HEPData YAML.
	 {0}/data6.yaml is valid HEPData YAML.
	 {0}/data7.yaml is valid HEPData YAML.
	 {0}/data8.yaml is valid HEPData YAML.
""".format(submission_dir)


def test_valid_submission_zip(validator_v1, data_path, capsys):
    submission_zip = os.path.join(data_path, 'TestHEPSubmission.zip')
    is_valid = validator_v1.validate(zipfile=submission_zip)
    assert is_valid

    validator_v1.print_valid_files()
    out, err = capsys.readouterr()
    lines = out.splitlines()
    assert lines[0].endswith("/submission.yaml is valid HEPData YAML.")
    for i in list(range(1, 8)):
        assert lines[i].endswith(f'data{i}.yaml is valid HEPData YAML.')


def test_valid_single_yaml(validator_v1, data_path, capsys):
    submission_file = os.path.join(data_path, '1512299.yaml')
    is_valid = validator_v1.validate(file=submission_file)
    assert is_valid
    assert validator_v1.valid_files == [submission_file]
    validator_v1.print_valid_files()
    out, err = capsys.readouterr()
    assert out.strip() == f"{submission_file} is valid HEPData YAML."


def test_invalid_input(validator_v1, data_path, capsys):
    # Invalid file
    is_valid = validator_v1.validate(file='notafile')
    assert not is_valid
    assert validator_v1.valid_files == []
    validator_v1.print_errors('notafile')
    out, err = capsys.readouterr()
    lines = out.splitlines()
    assert lines[0].strip() == "error - File notafile does not exist."

    # Invalid directory
    is_valid = validator_v1.validate(directory='notadirectory')
    assert not is_valid
    assert validator_v1.valid_files == []
    validator_v1.print_errors('notadirectory')
    out, err = capsys.readouterr()
    lines = out.splitlines()
    assert lines[0].strip() == "error - Directory notadirectory does not exist."

    # Invalid zip (does not exist)
    is_valid = validator_v1.validate(zipfile='notazipfile')
    assert not is_valid
    assert validator_v1.valid_files == []
    validator_v1.print_errors('notazipfile')
    out, err = capsys.readouterr()
    lines = out.splitlines()
    assert lines[0].strip() == "error - File notazipfile does not exist."

    # Invalid zip (not a zip)
    file = os.path.join(data_path, 'valid_submission.yaml')
    is_valid = validator_v1.validate(zipfile=file)
    assert not is_valid
    assert validator_v1.valid_files == []
    validator_v1.print_errors(file)
    out, err = capsys.readouterr()
    lines = out.splitlines()
    assert lines[0].strip() == f"error - Unable to extract file {file}. Error was: Unknown archive format '{file}'"


def test_missing_submission(validator_v1, data_path, capsys):
    # Use current directory (no submission.yaml)
    is_valid = validator_v1.validate()
    assert not is_valid
    assert validator_v1.valid_files == []
    validator_v1.print_errors('./submission.yaml')
    out, err = capsys.readouterr()
    lines = out.splitlines()
    assert lines[0].strip() == "error - No such file ./submission.yaml"

    # Zip without submission.yaml
    file = os.path.join(data_path, 'valid_submission.zip')
    validator_v1.validate(zipfile=file)
    assert not is_valid
    assert validator_v1.valid_files == []
    validator_v1.print_errors(file)
    out, err = capsys.readouterr()
    lines = out.splitlines()
    assert lines[0].strip() == f"error - submission.yaml not found in {file}."


def test_invalid_submission(validator_v1, data_path, capsys):
    file = os.path.join(data_path, 'invalid_submission.yaml')
    is_valid = validator_v1.validate(file=file)
    assert not is_valid
    assert validator_v1.valid_files == []
    validator_v1.print_errors(file)
    out, err = capsys.readouterr()
    lines = out.splitlines()
    assert lines[0].strip() == f"error - {file} is invalid HEPData YAML."
    assert lines[1].strip().startswith("error - 'values' is a required property in 'keywords[0]'")


def test_invalid_data_single_file(validator_v1, data_path, capsys):
    file = os.path.join(data_path, '1512299_invalid.yaml')
    is_valid = validator_v1.validate(file=file)
    assert not is_valid
    assert validator_v1.valid_files == []
    validator_v1.print_errors(file)
    out, err = capsys.readouterr()
    lines = out.splitlines()
    assert lines[0].strip() == f"error - {file} (Table 1) is invalid HEPData YAML."
    assert lines[1].strip().startswith("error - Additional properties are not allowed ('errorss' was unexpected) in 'dependent_variables[0].values[0]'")


def test_invalid_data_directory(validator_v1, data_path, capsys):
    dir = os.path.join(data_path, 'TestHEPSubmission_invalid')
    is_valid = validator_v1.validate(directory=dir)
    assert not is_valid
    expected_valid_files = [os.path.join(dir, f) for f in [
        'data1.yaml', 'data4.yaml', 'data5.yaml', 'data6.yaml', 'data7.yaml'
    ]]
    assert validator_v1.valid_files == expected_valid_files
    assert validator_v1.has_errors
    # Check errors directly rather than with print so we can check they're allocated to the right file
    errors = validator_v1.get_messages()
    expected_file_names = [
        os.path.join(dir, 'submission.yaml'),
        os.path.join(dir, 'data3.yaml'),
        os.path.join(dir, 'data8.yaml')
    ]
    assert set(errors.keys()) == set(expected_file_names)
    assert errors[expected_file_names[0]][0].message == 'mydirectory/data2.yaml should not contain "/".'
    assert errors[expected_file_names[0]][1].message == '../TestHEPSubmission/figFigure8B.png should not contain "/".'
    assert errors[expected_file_names[0]][2].message == f"{dir}/figFigure9A.png is missing."
    assert errors[expected_file_names[1]][0].message == f"{dir}/data3.yaml is missing."
    assert errors[expected_file_names[2]][0].message == f"""{dir}/data8.yaml is invalid YAML: while parsing a block mapping
  in "{dir}/data8.yaml", line 1, column 1
did not find expected key
  in "{dir}/data8.yaml", line 9, column 3"""


def test_invalid_syntax_submission(validator_v1, data_path, capsys):
    file = os.path.join(data_path, 'invalid_syntax_submission.yaml')
    is_valid = validator_v1.validate(file=file)
    assert not is_valid
    assert validator_v1.valid_files == []
    validator_v1.print_errors(file)
    out, err = capsys.readouterr()
    assert out.strip() == f"""error - {file} is invalid YAML: while scanning a simple key
  in "{file}", line 9, column 1
could not find expected ':'
  in "{file}", line 10, column 1"""
