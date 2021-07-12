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


def test_valid_submission_zip(data_path, cli_runner):
    submission_zip = os.path.join(data_path, 'TestHEPSubmission.zip')
    result = cli_runner.invoke(validate, ['-z', submission_zip])
    assert result.exit_code == 0


def test_valid_single_yaml(data_path, cli_runner):
    submission_file = os.path.join(data_path, '1512299.yaml')
    result = cli_runner.invoke(validate, ['-f', submission_file])
    assert result.exit_code == 0


def test_invalid_filename(cli_runner):
    result = cli_runner.invoke(validate, ['-f', 'notarealfile'])
    assert result.exit_code == 2
    assert 'ERROR: File notarealfile does not exist' in result.output


def test_invalid_yaml(data_path, cli_runner):
    file = os.path.join(data_path, '1512299_invalid.yaml')
    result = cli_runner.invoke(validate, ['-f', file])
    assert result.exit_code == 1
    assert "Table_1.yaml is invalid HEPData YAML." in result.output
