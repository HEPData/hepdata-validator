import os.path
import shutil
import sys
import tempfile

import yaml

from hepdata_validator import Validator, ValidationMessage
from .submission_file_validator import SubmissionFileValidator
from .data_file_validator import DataFileValidator

# We try to load using the CSafeLoader for speed improvements.
try:
    from yaml import CSafeLoader as Loader
    from yaml import CSafeDumper as Dumper
except ImportError:  # pragma: no cover
    from yaml import SafeLoader as Loader
    from yaml import SafeDumper as Dumper


class FullSubmissionValidator(Validator):

    def __init__(self, *args, **kwargs):
        super(FullSubmissionValidator, self).__init__(*args, **kwargs)
        self.submission_file_validator = SubmissionFileValidator(args, kwargs)
        self.data_file_validator = DataFileValidator(args, kwargs)
        self.valid_files = []

    def print_valid_files(self):
        for file in self.valid_files:
            print(f'\t {file} is valid HEPData YAML.')

    def validate(self, directory=None, file=None, zipfile=None):
        """
        Offline validation of submission.yaml and YAML data files.
        Can check either a single file or a directory.

        :param type directory: Directory to check (defaults to current working directory).
        :param type file: Single submission yaml file to check (overrides directory if both are given)
        :param type zipfile: Zipped file (e.g. .zip, .tar.gz, .gzip) to check (overrides directory and file if both are given)
        :return: Bool showing whether the submission is valid
        :rtype: type
        """
        self.single_yaml_file = False
        temp_directory = None
        self.directory = directory

        try:
            # Check input file/directory exists and is valid
            if zipfile:
                if not os.path.isfile(zipfile):
                    self.add_validation_message(ValidationMessage(
                        file=zipfile, message=f"File {zipfile} does not exist."
                    ))
                    return False

                # Try extracting file to a temp dir
                temp_directory = tempfile.mkdtemp()
                try:
                    shutil.unpack_archive(zipfile, temp_directory)
                except Exception as e:
                    self.add_validation_message(ValidationMessage(
                        file=zipfile, message=f"Unable to extract file {zipfile}. Error was: {e}"
                    ))
                    return False

                # Find submission.yaml in extracted directory
                for dir_name, _, files in os.walk(temp_directory):
                    for filename in files:
                        if filename == 'submission.yaml':
                            self.directory = dir_name

                if not self.directory:
                    self.add_validation_message(ValidationMessage(
                        file=zipfile, message=f"submission.yaml not found in {zipfile}."
                    ))
                    return False

            elif file:
                if not os.path.isfile(file):
                    self.add_validation_message(ValidationMessage(
                        file=file, message=f"File {file} does not exist."
                    ))
                    return False
                self.single_yaml_file = True
                self.directory = None
            else:
                self.directory = directory if directory else '.'
                if not os.path.isdir(self.directory):
                    self.add_validation_message(ValidationMessage(
                        file=self.directory, message=f"Directory {self.directory} does not exist."
                    ))
                    return False

            # Get location of the submission.yaml file or the single YAML file.
            if self.single_yaml_file:
                self.submission_file_path = file
            else:
                self.submission_file_path = os.path.join(self.directory, 'submission.yaml')
                if not os.path.isfile(self.submission_file_path):
                    self.add_validation_message(ValidationMessage(
                        file=self.submission_file_path, message=f"No such file {self.submission_file_path}"
                    ))
                    return False

            # Open the submission.yaml file and load all YAML documents.
            with open(self.submission_file_path, 'r') as stream:
                try:
                    docs = list(yaml.load_all(stream, Loader=Loader))
                except yaml.YAMLError as e:
                    self.add_validation_message(ValidationMessage(
                        file=self.submission_file_path, message=f'{self.submission_file_path} is invalid YAML: {str(e)}'
                    ))
                    return False

                # Need to remove independent_variables and dependent_variables from single YAML file.
                if self.single_yaml_file:
                    self._create_data_files(docs)

                # Validate the submission.yaml file
                is_valid_submission_file = self.submission_file_validator.validate(file_path=self.submission_file_path, data=docs)
                if not is_valid_submission_file:
                    self.add_validation_message(ValidationMessage(
                        file=self.submission_file_path, message=f'{self.submission_file_path} is invalid HEPData YAML.'
                    ))
                    for message in self.submission_file_validator.get_messages(self.submission_file_path):
                        self.add_validation_message(ValidationMessage(
                            file=self.submission_file_path, message=message.message
                        ))
                    return False

                # Loop over all YAML documents in the submission.yaml file.
                for doc in docs:
                    is_valid_doc_in_submission_file = self._check_doc(doc)
                    if not is_valid_doc_in_submission_file:
                        is_valid_submission_file = False

                if is_valid_submission_file:
                    self.valid_files.insert(0, self.submission_file_path)

            return len(self.messages) == 0
        finally:
            if temp_directory:
                # Delete temporary Directory
                shutil.rmtree(temp_directory)

    def _create_data_files(self, docs):
        for doc in docs:
            if 'name' in doc:
                file_name = doc['name'].replace(' ', '_').replace('/', '-') + '.yaml'
                doc['data_file'] = file_name
                with open(file_name, 'w') as data_file:
                    yaml.dump({'independent_variables': doc.pop('independent_variables', None),
                               'dependent_variables': doc.pop('dependent_variables', None)}, data_file, Dumper=Dumper)

    def _check_doc(self, doc):
        # Skip empty YAML documents.
        if not doc:
            return True

        is_valid_submission_doc = True

        # Check for presence of local files given as additional_resources.
        if 'additional_resources' in doc:
            for resource in doc['additional_resources']:
                if not resource['location'].startswith('http'):
                    location = os.path.join(self.directory, resource['location'])
                    if not os.path.isfile(location):
                        self.add_validation_message(ValidationMessage(
                            file=self.submission_file_path, message='%s is missing.' % location
                        ))
                        is_valid_submission_doc = False
                    elif '/' in resource['location']:
                        self.add_validation_message(ValidationMessage(
                            file=self.submission_file_path, message='%s should not contain "/".' % resource['location']
                        ))
                        is_valid_submission_doc = False

        # Check for non-empty YAML documents with a 'data_file' key.
        if 'data_file' in doc:

            # Check for presence of '/' in data_file value.
            if '/' in doc['data_file']:
                self.add_validation_message(ValidationMessage(
                    file=self.submission_file_path, message='%s should not contain "/".' % doc['data_file']
                ))
                return False

            # Extract data file from YAML document.
            data_file_path = self.directory + '/' + doc['data_file'] if self.directory else doc['data_file']
            if not os.path.isfile(data_file_path):
                self.add_validation_message(ValidationMessage(
                    file=data_file_path, message='%s is missing.' % data_file_path
                ))
                return is_valid_submission_doc

            user_data_file_path = self.submission_file_path if self.single_yaml_file else data_file_path

            # Just try to load YAML data file without validating schema.
            try:
                contents = yaml.load(open(data_file_path, 'r'), Loader=Loader)
            except yaml.YAMLError as e:
                self.add_validation_message(ValidationMessage(
                    file=user_data_file_path, message=f'{user_data_file_path} is invalid YAML: {str(e)}'
                ))
                return is_valid_submission_doc

            # Validate the YAML data file
            is_valid_data_file = self.data_file_validator.validate(file_path=data_file_path, data=contents)
            if not is_valid_data_file:
                table_msg = f" ({doc['name']})" if self.single_yaml_file else ''
                self.add_validation_message(ValidationMessage(
                    file=user_data_file_path, message=f'{user_data_file_path}{table_msg} is invalid HEPData YAML.'
                ))
                if self.single_yaml_file:
                    is_valid_submission_doc = False

                is_valid_data_file = False
                for message in self.data_file_validator.get_messages(data_file_path):
                    self.add_validation_message(ValidationMessage(
                        file=user_data_file_path, message=message.message
                    ))
            elif not self.single_yaml_file:
                self.valid_files.append(user_data_file_path)

            # For single YAML file, clean up by removing temporary data_file created above.
            if self.single_yaml_file:
                os.remove(doc['data_file'])

        return is_valid_submission_doc
