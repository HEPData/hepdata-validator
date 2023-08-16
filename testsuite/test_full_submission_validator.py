import os

import pytest

from hepdata_validator.full_submission_validator import FullSubmissionValidator, SchemaType


@pytest.fixture(scope="module")
def data_path():
    base_dir = os.path.dirname(os.path.realpath(__file__))
    return os.path.join(base_dir, 'test_data')


@pytest.fixture()
def validator_v0():
    return FullSubmissionValidator(schema_version='0.1.0')


@pytest.fixture()
def validator_v1():
    return FullSubmissionValidator()


def test_valid_submission_dir(validator_v1, data_path, capsys):
    submission_dir = os.path.join(data_path, 'TestHEPSubmission')
    is_valid = validator_v1.validate(directory=submission_dir)
    assert is_valid

    validator_v1.print_valid_files()
    out, err = capsys.readouterr()
    assert out == """	 {0}/submission.yaml is valid HEPData submission YAML.
	 {0}/data1.yaml is valid HEPData data YAML.
	 {0}/data2.yaml is valid HEPData data YAML.
	 {0}/data3.yaml is valid HEPData data YAML.
	 {0}/data4.yaml is valid HEPData data YAML.
	 {0}/data5.yaml is valid HEPData data YAML.
	 {0}/data6.yaml is valid HEPData data YAML.
	 {0}/data7.yaml is valid HEPData data YAML.
	 {0}/data8.yaml is valid HEPData data YAML.
""".format(submission_dir)


def test_valid_submission_zip(validator_v1, data_path, capsys):
    submission_zip = os.path.join(data_path, 'TestHEPSubmission.zip')
    is_valid = validator_v1.validate(archive=submission_zip)
    assert is_valid

    validator_v1.print_valid_files()
    out, err = capsys.readouterr()
    lines = out.splitlines()
    assert lines[0].strip() == "TestHEPSubmission/submission.yaml is valid HEPData submission YAML."
    for i in list(range(1, 8)):
        assert lines[i].strip() == f'TestHEPSubmission/data{i}.yaml is valid HEPData data YAML.'


def test_valid_single_yaml(validator_v1, data_path, capsys):
    submission_file = os.path.join(data_path, '1512299.yaml')
    is_valid = validator_v1.validate(file=submission_file)
    assert is_valid
    assert validator_v1.valid_files == {SchemaType.SINGLE_YAML: [submission_file]}
    validator_v1.print_valid_files()
    out, err = capsys.readouterr()
    assert out.strip() == f"{submission_file} is valid HEPData single file YAML."


def test_valid_single_yaml_gzip(validator_v1, data_path, capsys):
    submission_file = os.path.join(data_path, '1512299.yaml.gz')
    is_valid = validator_v1.validate(file=submission_file)
    assert is_valid
    assert SchemaType.SINGLE_YAML in validator_v1.valid_files
    assert validator_v1.valid_files[SchemaType.SINGLE_YAML][0] == '1512299.yaml'
    validator_v1.print_valid_files()
    out, err = capsys.readouterr()
    assert out.strip() == "1512299.yaml is valid HEPData single file YAML."


def test_valid_submission_dir_remote_schema(validator_v1, data_path, capsys):
    submission_dir = os.path.join(data_path, 'TestRemoteSubmission')
    is_valid = validator_v1.validate(directory=submission_dir)
    assert is_valid

    validator_v1.print_valid_files()
    out, err = capsys.readouterr()
    assert out == """	 {0}/submission.yaml is valid HEPData submission YAML.
	 {0}/valid_file_custom_remote.json is valid against schema https://scikit-hep.org/pyhf/schemas/1.0.0/workspace.json.
""".format(submission_dir)


def test_valid_submission_dir_remote_schema_no_autoloading(data_path):
    validator = FullSubmissionValidator(autoload_remote_schemas=False)
    submission_dir = os.path.join(data_path, 'TestRemoteSubmission')

    # Validate without pre-loading schemas - should get an error
    is_valid = validator.validate(directory=submission_dir)
    assert not is_valid
    messages = validator.get_messages(os.path.join(submission_dir, 'submission.yaml'))
    assert len(messages) == 1
    assert messages[0].message == \
        "Autoloading of remote schema https://scikit-hep.org/pyhf/schemas/1.0.0/workspace.json is not allowed."

    # Load remote schema and try again
    validator.clear_all()
    validator.load_remote_schema(schema_url='https://scikit-hep.org/pyhf/schemas/1.0.0/workspace.json')
    is_valid = validator.validate(directory=submission_dir)
    assert is_valid


def test_valid_submission_dir_remote_schema_multiple_loads():
    validator = FullSubmissionValidator(autoload_remote_schemas=False)

    # Load schema once - should be fine
    validator.load_remote_schema(base_url="https://scikit-hep.org/pyhf/schemas/1.0.0", schema_name="workspace.json")
    assert len(validator._data_file_validator.custom_data_schemas) == 1
    assert "https://scikit-hep.org/pyhf/schemas/1.0.0/workspace.json" in validator._data_file_validator.custom_data_schemas

    # Load same schema again (via URL this time) - should not add anything to custom_data_schemas
    validator.load_remote_schema(schema_url='https://scikit-hep.org/pyhf/schemas/1.0.0/workspace.json')
    assert len(validator._data_file_validator.custom_data_schemas) == 1
    assert "https://scikit-hep.org/pyhf/schemas/1.0.0/workspace.json" in validator._data_file_validator.custom_data_schemas


def test_invalid_input(validator_v1, data_path, capsys):
    # Invalid file
    is_valid = validator_v1.validate(file='notafile')
    assert not is_valid
    assert validator_v1.valid_files == {}
    validator_v1.print_errors('notafile')
    out, err = capsys.readouterr()
    lines = out.splitlines()
    assert lines[0].strip() == "error - File notafile does not exist."

    # Invalid directory
    is_valid = validator_v1.validate(directory='notadirectory')
    assert not is_valid
    assert validator_v1.valid_files == {}
    validator_v1.print_errors('notadirectory')
    out, err = capsys.readouterr()
    lines = out.splitlines()
    assert lines[0].strip() == "error - Directory notadirectory does not exist."

    # Invalid zip (does not exist)
    is_valid = validator_v1.validate(archive='notanarchive')
    assert not is_valid
    assert validator_v1.valid_files == {}
    validator_v1.print_errors('notanarchive')
    out, err = capsys.readouterr()
    lines = out.splitlines()
    assert lines[0].strip() == "error - File notanarchive does not exist."

    # Invalid zip (not a zip)
    file = os.path.join(data_path, 'valid_submission.yaml')
    is_valid = validator_v1.validate(archive=file)
    assert not is_valid
    assert validator_v1.valid_files == {}
    validator_v1.print_errors(file)
    out, err = capsys.readouterr()
    lines = out.splitlines()
    assert lines[0].strip() == f"error - Unable to extract file {file}. Error was: Unknown archive format '{file}'"


def test_missing_submission(validator_v1, data_path, capsys):
    # Use current directory (no submission.yaml)
    is_valid = validator_v1.validate()
    assert not is_valid
    assert validator_v1.valid_files == {}
    validator_v1.print_errors('./submission.yaml')
    out, err = capsys.readouterr()
    lines = out.splitlines()
    assert lines[0].strip() == "error - No submission.yaml file found in submission."

    # Zip without submission.yaml
    file = os.path.join(data_path, 'valid_submission.zip')
    validator_v1.validate(archive=file)
    assert not is_valid
    assert validator_v1.valid_files == {}
    validator_v1.print_errors(file)
    out, err = capsys.readouterr()
    lines = out.splitlines()
    assert lines[0].strip() == "error - No submission.yaml file found in submission."


def test_invalid_submission(validator_v1, data_path, capsys):
    file = os.path.join(data_path, 'invalid_submission.yaml')
    is_valid = validator_v1.validate(file=file)
    assert not is_valid
    assert validator_v1.valid_files == {}
    validator_v1.print_errors(file)
    out, err = capsys.readouterr()
    lines = out.splitlines()
    assert lines[0].strip() == f"error - {file} is invalid HEPData YAML."
    assert lines[1].strip().startswith("error - 'values' is a required property in 'keywords[0]'")


def test_invalid_data_single_file(validator_v1, data_path, capsys):
    file = os.path.join(data_path, '1512299_invalid.yaml')
    is_valid = validator_v1.validate(file=file)
    assert not is_valid
    assert validator_v1.valid_files == {}
    validator_v1.print_errors(file)
    out, err = capsys.readouterr()
    lines = out.splitlines()
    assert lines[0].strip() == f"error - {file} (Table 1) is invalid HEPData YAML."
    assert lines[1].strip().startswith("error - Additional properties are not allowed ('errorss' was unexpected) in 'dependent_variables[0].values[0]'")


def test_invalid_data_single_file_gzip(validator_v1, data_path, capsys):
    file = os.path.join(data_path, '1512299_invalid.yaml.gz')
    is_valid = validator_v1.validate(file=file)
    assert not is_valid
    assert validator_v1.valid_files == {}
    validator_v1.print_errors(file)
    out, err = capsys.readouterr()
    lines = out.splitlines()
    assert lines[0].strip().startswith(f"error - Unable to extract file {file}. Error was: Not a gzipped file")


def test_invalid_yaml_single_file_gzip(validator_v1, data_path, capsys):
    # Check error messages don't contain temp dir
    file = os.path.join(data_path, '1512299_invalid_yaml.yaml.gz')
    is_valid = validator_v1.validate(file=file)
    assert not is_valid
    assert validator_v1.valid_files == {}
    validator_v1.print_errors('1512299_invalid_yaml.yaml')
    out, err = capsys.readouterr()
    assert out.strip().startswith("""error - There was a problem parsing the file:
		while parsing a flow mapping
		  in "1512299_invalid_yaml.yaml", line 7, column 11""")
    # message is different in libyaml and non-libyaml versions but this is in both
    assert "expected ',' or '}'" in out
    assert out.strip().endswith('in "1512299_invalid_yaml.yaml", line 8, column 3')


def test_invalid_single_file_data_file(validator_v1, data_path, capsys):
    # Check that passing a data file as a single file does not validate
    file = os.path.join(data_path, 'valid_file.yaml')
    is_valid = validator_v1.validate(file=file)
    assert not is_valid
    assert validator_v1.valid_files == {}
    validator_v1.print_errors(file)
    out, err = capsys.readouterr()
    lines = out.splitlines()
    assert lines[0].strip() == f"error - {file} is invalid HEPData YAML."
    assert lines[1].strip().startswith("error - There should be at least one document matching the submission schema.")


def test_invalid_data_directory(validator_v1, data_path, capsys):
    dir = os.path.join(data_path, 'TestHEPSubmission_invalid')
    is_valid = validator_v1.validate(directory=dir)
    assert not is_valid
    expected_valid_files = [os.path.join(dir, f) for f in [
        'data1.yaml', 'data4.yaml', 'data5.yaml', 'data6.yaml', 'data7.yaml', '._data9.yaml', 'data10.yaml'
    ]]
    assert validator_v1.valid_files == {SchemaType.DATA: expected_valid_files}
    assert validator_v1.has_errors
    # Check errors directly rather than with print so we can check they're allocated to the right file
    errors = validator_v1.get_messages()
    expected_file_names = [
        os.path.join(dir, 'submission.yaml'),
        os.path.join(dir, 'data3.yaml'),
        os.path.join(dir, 'data8.yaml'),
        os.path.join(dir, 'figFigure8B.png'),
        os.path.join(dir, '._data10.yaml'),
        os.path.join(dir, '._data11.yaml'),
        os.path.join(dir, 'data11.yaml'),
    ]
    assert set(errors.keys()) == set(expected_file_names)
    assert errors[expected_file_names[0]][0].message == "Name of data_file 'mydirectory/data2.yaml' should not contain '/'."
    assert errors[expected_file_names[0]][1].message == "Location of 'additional_resources' file '../TestHEPSubmission/figFigure8B.png' should not contain '/'."
    assert errors[expected_file_names[0]][2].message == "Missing 'additional_resources' file 'figFigure9A.png'."
    assert errors[expected_file_names[1]][0].message == "Missing data_file 'data3.yaml'."
    assert errors[expected_file_names[2]][0].message.startswith(f"""There was a problem parsing the file:
		while parsing a block mapping
		  in "{dir}/data8.yaml", line 1, column 1""")
    # message differs depending on whether libyaml is used
    assert "did not find expected key" in errors[expected_file_names[2]][0].message or \
           "expected <block end>, but found '<block mapping start>'" in errors[expected_file_names[2]][0].message
    assert errors[expected_file_names[2]][0].message.endswith(f'in "{dir}/data8.yaml", line 9, column 3')
    assert errors[expected_file_names[3]][0].message == "figFigure8B.png is not referenced in the submission."
    assert len(errors[expected_file_names[4]]) == 2
    assert errors[expected_file_names[4]][0].message == "._data10.yaml is not referenced in the submission."
    assert errors[expected_file_names[4]][1].message == "._data10.yaml might be a file created by tar on MacOS. Set COPYFILE_DISABLE=1 before creating the archive."
    assert errors[expected_file_names[4]][1].level == 'hint'
    assert errors[expected_file_names[5]][0].message == "._data11.yaml is not referenced in the submission."
    assert errors[expected_file_names[6]][0].message == "Size of data_file 'data11.yaml' (12180000 bytes) is bigger than the limit of 10485760 bytes. Try adding the file as an additional_resource instead."


def test_invalid_archive(validator_v1, data_path):#, capsys):
    archive = os.path.join(data_path, 'TestHEPSubmission_invalid.zip')
    dir = 'TestHEPSubmission_invalid'
    is_valid = validator_v1.validate(archive=archive)
    assert not is_valid
    expected_valid_files = [os.path.join(dir, f) for f in [
        'data1.yaml', 'data4.yaml', 'data5.yaml', 'data6.yaml', 'data7.yaml', '._data9.yaml', 'data10.yaml'
    ]]
    assert validator_v1.valid_files == {SchemaType.DATA: expected_valid_files}
    assert validator_v1.has_errors
    # Check errors directly rather than with print so we can check they're allocated to the right file
    errors = validator_v1.get_messages()
    expected_file_names = [
        os.path.join(dir, 'submission.yaml'),
        os.path.join(dir, 'data3.yaml'),
        os.path.join(dir, 'data8.yaml'),
        os.path.join(dir, 'figFigure8B.png'),
        os.path.join(dir, '._data10.yaml'),
        os.path.join(dir, '._data11.yaml')
    ]
    assert set(errors.keys()) == set(expected_file_names)
    assert errors[expected_file_names[0]][0].message == "Name of data_file 'mydirectory/data2.yaml' should not contain '/'."
    assert errors[expected_file_names[0]][1].message == "Location of 'additional_resources' file '../TestHEPSubmission/figFigure8B.png' should not contain '/'."
    assert errors[expected_file_names[0]][2].message == f"Missing 'additional_resources' file 'figFigure9A.png'."
    assert errors[expected_file_names[1]][0].message == f"Missing data_file 'data3.yaml'."
    assert errors[expected_file_names[2]][0].message.startswith(f"""There was a problem parsing the file:
		while parsing a block mapping
		  in "{dir}/data8.yaml", line 1, column 1""")
    # message differs depending on whether libyaml is used
    assert "did not find expected key" in errors[expected_file_names[2]][0].message or \
           "expected <block end>, but found '<block mapping start>'" in errors[expected_file_names[2]][0].message
    assert errors[expected_file_names[2]][0].message.endswith(f'in "{dir}/data8.yaml", line 9, column 3')
    assert errors[expected_file_names[3]][0].message == f"figFigure8B.png is not referenced in the submission."
    assert len(errors[expected_file_names[4]]) == 2
    assert errors[expected_file_names[4]][0].message == f"._data10.yaml is not referenced in the submission."
    assert errors[expected_file_names[4]][1].message == f"._data10.yaml might be a file created by tar on MacOS. Set COPYFILE_DISABLE=1 before creating the archive."
    assert errors[expected_file_names[4]][1].level == 'hint'
    assert errors[expected_file_names[5]][0].message == f"._data11.yaml is not referenced in the submission."


def test_invalid_syntax_submission(validator_v1, data_path, capsys):
    file = os.path.join(data_path, 'invalid_syntax_submission.yaml')
    is_valid = validator_v1.validate(file=file)
    assert not is_valid
    assert validator_v1.valid_files == {}
    validator_v1.print_errors(file)
    out, err = capsys.readouterr()
    assert out.strip() == f"""error - There was a problem parsing the file:
		while scanning a simple key
		  in "{file}", line 9, column 1
		could not find expected ':'
		  in "{file}", line 10, column 1"""


def test_invalid_remote_schema_load(validator_v1):
    with pytest.raises(ValueError) as excinfo:
        validator_v1.load_remote_schema()

    assert str(excinfo.value) == "Must provide EITHER schema_url OR both base_url and schema_name"

    with pytest.raises(ValueError) as excinfo:
        validator_v1.load_remote_schema(schema_name="my_schema_name")

    assert str(excinfo.value) == "Must provide EITHER schema_url OR both base_url and schema_name"


def test_invalid_remote_schema(validator_v1, data_path, capsys):
    submission_dir = os.path.join(data_path, 'TestRemoteSubmission_invalid')
    file = os.path.join(submission_dir, 'submission.yaml')
    is_valid = validator_v1.validate(directory=submission_dir)
    assert not is_valid

    # Check errors directly rather than with print so we can check they're allocated to the right file
    errors = validator_v1.get_messages()
    expected_file_names = [
        os.path.join(submission_dir, 'submission.yaml'),
        os.path.join(submission_dir, 'invalid_file_custom_remote.json')
    ]
    assert set(errors.keys()) == set(expected_file_names)
    assert errors[expected_file_names[0]][0].message == 'Remote schema https://hepdata.net/notarealproject/schemas/v0.0.0/thisisnotarealfile.json not found.'
    assert errors[expected_file_names[1]][0].message == f"{submission_dir}/invalid_file_custom_remote.json is invalid against schema https://scikit-hep.org/pyhf/schemas/1.0.0/workspace.json."

    validator_v1.print_errors(file)
    out, err = capsys.readouterr()
    assert out == """	 error - Remote schema https://hepdata.net/notarealproject/schemas/v0.0.0/thisisnotarealfile.json not found.
"""


def test_clear_all(validator_v1):
    """
    Tests the SubmissionFileValidator V1 clear messages function
    """

    validator_v1.messages = {'full': 'non-empty'}
    validator_v1.submission_docs = ['doc1', 'doc2']
    validator_v1.valid_files = {'a': ['valid_file']}
    validator_v1._submission_file_validator.messages = {'submission': 'non-empty'}
    validator_v1._data_file_validator.messages = {'data': 'non-empty'}
    validator_v1.clear_all()

    assert len(validator_v1.get_messages()) == 0
    assert len(validator_v1._submission_file_validator.get_messages()) == 0
    assert len(validator_v1._data_file_validator.get_messages()) == 0
    assert len(validator_v1.valid_files) == 0
    assert validator_v1.submission_docs is None


def test_v0_schema(validator_v1, validator_v0, data_path, capsys):
    submission_dir = os.path.join(data_path, 'TestHEPSubmission_v0')

    # Should be invalid with v1 validator
    is_valid = validator_v1.validate(directory=submission_dir)
    assert not is_valid

    # Should be valid with v0 validator
    is_valid = validator_v0.validate(directory=submission_dir)
    assert is_valid
