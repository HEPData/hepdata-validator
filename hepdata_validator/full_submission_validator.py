import os.path
import shutil
import sys
import tempfile

import yaml

from .submission_file_validator import SubmissionFileValidator
from .data_file_validator import DataFileValidator

# We try to load using the CSafeLoader for speed improvements.
try:
    from yaml import CSafeLoader as Loader
    from yaml import CSafeDumper as Dumper
except ImportError:  # pragma: no cover
    from yaml import SafeLoader as Loader
    from yaml import SafeDumper as Dumper


def validate(directory=None, file=None, zipfile=None):
    """
    Offline validation of submission.yaml and YAML data files.
    Can check either a single file or a directory.

    :param type directory: Directory to check (defaults to current working directory).
    :param type file: Single submission yaml file to check (overrides directory if both are given)
    :param type zipfile: Zipped file (e.g. .zip, .tar.gz, .gzip) to check (overrides directory and file if both are given)
    :return: Bool showing whether the submission is valid
    :rtype: type
    """
    single_yaml_file = False
    temp_directory = None
    is_valid = True
    try:
        if zipfile:
            print(f"Checking zipfile {zipfile}")
            if not os.path.isfile(zipfile):
                raise ValueError(f"File {zipfile} does not exist.")

            # Try extracting file to a temp dir
            temp_directory = tempfile.mkdtemp()
            print(f"Extracting to {temp_directory}")
            try:
                shutil.unpack_archive(zipfile, temp_directory)
            except Exception as e:
                raise ValueError(f"Unable to extract file {zipfile}. Error was: {e}")

            # Find submission.yaml in extracted directory
            for dir_name, _, files in os.walk(temp_directory):
                for filename in files:
                    if filename == 'submission.yaml':
                        directory = dir_name

            if not directory:
                raise ValueError(f"submission.yaml not found in {zipfile}.")

        elif file:
            print(f"Checking file {file}")
            if not os.path.isfile(file):
                raise ValueError(f"File {file} does not exist.")
            single_yaml_file = True
        else:
            if not directory:
                directory = '.'
            print(f"Checking directory {directory}")
            if not os.path.isdir(directory):
                raise ValueError(f"Directory {directory} does not exist.")

        # Get location of the submission.yaml file or the single YAML file.
        if single_yaml_file:
            submission_file_path = file
        else:
            submission_file_path = os.path.join(directory, 'submission.yaml')
            if not os.path.isfile(submission_file_path):
                raise ValueError(f"No such file {submission_file_path}")

        # Open the submission.yaml file and load all YAML documents.
        with open(submission_file_path, 'r') as stream:
            docs = list(yaml.load_all(stream, Loader=Loader))

            # Need to remove independent_variables and dependent_variables from single YAML file.
            if single_yaml_file:
                for doc in docs:
                    if 'name' in doc:
                        file_name = doc['name'].replace(' ', '_').replace('/', '-') + '.yaml'
                        doc['data_file'] = file_name
                        with open(file_name, 'w') as data_file:
                            yaml.dump({'independent_variables': doc.pop('independent_variables', None),
                                       'dependent_variables': doc.pop('dependent_variables', None)}, data_file, Dumper=Dumper)

            # Validate the submission.yaml file
            submission_file_validator = SubmissionFileValidator()
            is_valid_submission_file = submission_file_validator.validate(file_path=submission_file_path, data=docs)
            if not is_valid_submission_file:
                print('%s is invalid HEPData YAML.' % submission_file_path)
                submission_file_validator.print_errors(submission_file_path)
                raise ValueError('Invalid YAML')
            else:
                print('%s is valid HEPData YAML.' % submission_file_path)

            # Loop over all YAML documents in the submission.yaml file.
            for doc in docs:

                # Skip empty YAML documents.
                if not doc:
                    continue

                # Check for presence of local files given as additional_resources.
                if 'additional_resources' in doc:
                    for resource in doc['additional_resources']:
                        if not resource['location'].startswith('http'):
                            location = os.path.join(directory, resource['location'])
                            if not os.path.isfile(location):
                                print('%s is missing.' % location)
                                is_valid = False
                            elif '/' in resource['location']:
                                print('%s should not contain "/".' % resource['location'])
                                is_valid = False

                # Check for non-empty YAML documents with a 'data_file' key.
                if 'data_file' in doc:

                    # Check for presence of '/' in data_file value.
                    if '/' in doc['data_file']:
                        print('%s should not contain "/".' % doc['data_file'])
                        continue

                    # Extract data file from YAML document.
                    data_file_path = directory + '/' + doc['data_file'] if directory else doc['data_file']
                    if not os.path.isfile(data_file_path):
                        print('%s is missing.' % data_file_path)
                        is_valid = False
                        continue

                    # Just try to load YAML data file without validating schema.
                    # Script will terminate with an exception if there is a problem.
                    contents = yaml.load(open(data_file_path, 'r'), Loader=Loader)

                    # Validate the YAML data file if validator imported.
                    data_file_validator = DataFileValidator()
                    is_valid_data_file = data_file_validator.validate(file_path=data_file_path, data=contents)
                    if not is_valid_data_file:
                        print('%s is invalid HEPData YAML.' % data_file_path)
                        data_file_validator.print_errors(data_file_path)
                        is_valid = False
                    else:
                        print('%s is valid HEPData YAML.' % data_file_path)

                    # For single YAML file, clean up by removing temporary data_file created above.
                    if single_yaml_file:
                        print('Removing %s.' % doc['data_file'])
                        os.remove(doc['data_file'])
        return is_valid
    finally:
        if temp_directory:
            # Delete temporary Directory
            shutil.rmtree(temp_directory)
