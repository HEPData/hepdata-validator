import os

import pytest

from hepdata_validator import full_submission_validator


@pytest.fixture(scope="module")
def data_path():
    base_dir = os.path.dirname(os.path.realpath(__file__))
    return os.path.join(base_dir, 'test_data')


def test_valid_submission_dir(data_path, capsys):
    submission_dir = os.path.join(data_path, 'TestHEPSubmission')
    is_valid = full_submission_validator.validate(directory=submission_dir)
    assert is_valid

    out, err = capsys.readouterr()
    assert out == """Checking directory {0}
{0}/submission.yaml is valid HEPData YAML.
{0}/data1.yaml is valid HEPData YAML.
{0}/data2.yaml is valid HEPData YAML.
{0}/data3.yaml is valid HEPData YAML.
{0}/data4.yaml is valid HEPData YAML.
{0}/data5.yaml is valid HEPData YAML.
{0}/data6.yaml is valid HEPData YAML.
{0}/data7.yaml is valid HEPData YAML.
{0}/data8.yaml is valid HEPData YAML.
""".format(submission_dir)


def test_valid_submission_zip(data_path, capsys):
    submission_zip = os.path.join(data_path, 'TestHEPSubmission.zip')
    is_valid = full_submission_validator.validate(zipfile=submission_zip)
    assert is_valid

    out, err = capsys.readouterr()
    lines = out.splitlines()
    assert lines[0] == f"Checking zipfile {submission_zip}"
    assert lines[1].startswith('Extracting to ')
    assert lines[2].endswith("/submission.yaml is valid HEPData YAML.")
    for i in list(range(1, 8)):
        assert lines[i+2].endswith(f'data{i}.yaml is valid HEPData YAML.')


def test_valid_single_yaml(data_path, capsys):
    submission_file = os.path.join(data_path, '1512299.yaml')
    is_valid = full_submission_validator.validate(file=submission_file)
    assert is_valid

    out, err = capsys.readouterr()
    assert out == """Checking file {0}
{0} is valid HEPData YAML.
Table_1.yaml is valid HEPData YAML.
Removing Table_1.yaml.
Table_2.yaml is valid HEPData YAML.
Removing Table_2.yaml.
Table_3.yaml is valid HEPData YAML.
Removing Table_3.yaml.
Table_4.yaml is valid HEPData YAML.
Removing Table_4.yaml.
Table_5.yaml is valid HEPData YAML.
Removing Table_5.yaml.
""".format(submission_file)


def test_invalid_input(data_path):
    # Invalid file
    with pytest.raises(ValueError) as e:
        full_submission_validator.validate(file='notafile')

    assert str(e.value) == "File notafile does not exist."

    # Invalid directory
    with pytest.raises(ValueError) as e:
        full_submission_validator.validate(directory='notadirectory')

    str(e.value) == "Directory notadirectory does not exist."

    # Invalid zip (does not exist)
    with pytest.raises(ValueError) as e:
        full_submission_validator.validate(zipfile='notazipfile')

    assert str(e.value) == "File notazipfile does not exist."

    # Invalid zip (not a zip)
    file = os.path.join(data_path, 'valid_submission.yaml')
    with pytest.raises(ValueError) as e:
        full_submission_validator.validate(zipfile=file)

    assert str(e.value) == f"Unable to extract file {file}. Error was: Unknown archive format '{file}'"


def test_missing_submission(data_path):
    # Use current directory (no submission.yaml)
    with pytest.raises(ValueError) as e:
        full_submission_validator.validate()

    assert str(e.value) == f"No such file ./submission.yaml"

    # Zip without submission.yaml
    file = os.path.join(data_path, 'valid_submission.zip')
    with pytest.raises(ValueError) as e:
        full_submission_validator.validate(zipfile=file)

    assert str(e.value) == f"submission.yaml not found in {file}."


def test_invalid_submission(data_path, capsys):
    file = os.path.join(data_path, 'invalid_submission.yaml')
    with pytest.raises(ValueError) as e:
        full_submission_validator.validate(file=file)

    out, err = capsys.readouterr()
    lines = out.splitlines()
    assert lines[0] == f"Checking file {file}"
    assert lines[1] == f"{file} is invalid HEPData YAML."
    assert lines[2].strip().startswith("error - 'values' is a required property in 'keywords[0]'")
    assert str(e.value) == 'Invalid YAML'


def test_invalid_data_single_file(data_path, capsys):
    file = os.path.join(data_path, '1512299_invalid.yaml')
    is_valid = full_submission_validator.validate(file=file)
    assert not is_valid

    out, err = capsys.readouterr()
    lines = out.splitlines()
    assert lines[0] == f"Checking file {file}"
    assert lines[1] == f"{file} is valid HEPData YAML."
    assert lines[2] == f"Table_1.yaml is invalid HEPData YAML."
    assert lines[3].strip().startswith("error - Additional properties are not allowed ('errorss' was unexpected) in 'dependent_variables[0].values[0]'")


def test_invalid_data_directory(data_path, capsys):
    dir = os.path.join(data_path, 'TestHEPSubmission_invalid')
    is_valid = full_submission_validator.validate(directory=dir)
    assert not is_valid

    out, err = capsys.readouterr()
    assert 'mydirectory/data2.yaml should not contain "/".' in out
    assert "testsuite/test_data/TestHEPSubmission_invalid/data3.yaml is missing" in out
    assert '../TestHEPSubmission/figFigure8B.png should not contain "/".' in out
    assert "testsuite/test_data/TestHEPSubmission_invalid/figFigure9A.png is missing." in out
