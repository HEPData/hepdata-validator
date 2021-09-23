import os

from click.testing import CliRunner
import pytest

from hepdata_validator.cli import validate

@pytest.fixture(scope="module")
def data_path():
    base_dir = os.path.dirname(os.path.realpath(__file__))
    return os.path.join(base_dir, 'test_data')


@pytest.fixture(scope="module")
def cli_runner():
    return CliRunner()


def test_valid_submission_dir(data_path, cli_runner):
    submission_dir = os.path.join(data_path, 'TestHEPSubmission')
    result = cli_runner.invoke(validate, ['-d', submission_dir])
    assert result.exit_code == 0
    assert result.output == """{0} is valid.
	 {0}/submission.yaml is valid HEPData submission YAML.
	 {0}/data1.yaml is valid HEPData data YAML.
	 {0}/data2.yaml is valid HEPData data YAML.
	 {0}/data3.yaml is valid HEPData data YAML.
	 {0}/data4.yaml is valid HEPData data YAML.
	 {0}/data5.yaml is valid HEPData data YAML.
	 {0}/data6.yaml is valid HEPData data YAML.
	 {0}/data7.yaml is valid HEPData data YAML.
	 {0}/data8.yaml is valid HEPData data YAML.
""".format(submission_dir)


def test_valid_submission_zip(data_path, cli_runner):
    submission_zip = os.path.join(data_path, 'TestHEPSubmission.zip')
    result = cli_runner.invoke(validate, ['-a', submission_zip])
    assert result.exit_code == 0
    lines = result.output.splitlines()
    assert lines[0] == f"{submission_zip} is valid."
    assert lines[1].endswith("/submission.yaml is valid HEPData submission YAML.")
    for i in list(range(1, 8)):
        assert lines[i+1].endswith(f'data{i}.yaml is valid HEPData data YAML.')


def test_valid_single_yaml(data_path, cli_runner):
    submission_file = os.path.join(data_path, '1512299.yaml')
    result = cli_runner.invoke(validate, ['-f', submission_file])
    assert result.exit_code == 0
    assert result.output == f"""{submission_file} is valid.
	 {submission_file} is valid HEPData single file YAML.
"""


def test_invalid_filename(cli_runner):
    result = cli_runner.invoke(validate, ['-f', 'notarealfile'])
    assert result.exit_code == 1
    assert result.output == """ERROR: notarealfile is invalid.
	 error - File notarealfile does not exist.
"""


def test_invalid_yaml(data_path, cli_runner):
    file = os.path.join(data_path, '1512299_invalid.yaml')
    result = cli_runner.invoke(validate, ['-f', file])
    assert result.exit_code == 1
    lines = result.output.splitlines()
    assert lines[0] == f"ERROR: {file} is invalid."
    assert lines[1].strip().startswith(f"error - {file} (Table 1) is invalid HEPData YAML.")
