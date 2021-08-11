from enum import Enum
import os.path
import shutil
import tempfile
from urllib.parse import urlparse, urlunsplit

import yaml

from hepdata_validator import Validator, ValidationMessage
from .schema_resolver import JsonSchemaResolver
from .schema_downloader import HTTPSchemaDownloader
from .submission_file_validator import SubmissionFileValidator
from .data_file_validator import DataFileValidator

# We try to load using the CSafeLoader for speed improvements.
try:
    from yaml import CSafeLoader as Loader
    from yaml import CSafeDumper as Dumper
except ImportError:  # pragma: no cover
    from yaml import SafeLoader as Loader
    from yaml import SafeDumper as Dumper


class SchemaType(Enum):
    SUBMISSION = 'submission'
    SINGLE_YAML = 'single file'
    DATA = 'data'
    REMOTE = 'remote'


class FullSubmissionValidator(Validator):

    def __init__(self, *args, **kwargs):
        super(FullSubmissionValidator, self).__init__(*args, **kwargs)
        self.submission_file_validator = SubmissionFileValidator(args, kwargs)
        self.data_file_validator = DataFileValidator(args, kwargs)
        self.valid_files = {}

    def print_valid_files(self):
        for type in SchemaType:
            if type in self.valid_files:
                if type == SchemaType.REMOTE:
                    for schema, file in self.valid_files[type]:
                        print(f'\t {file} is valid against schema {schema}.')
                else:
                    for file in self.valid_files[type]:
                        print(f'\t {file} is valid HEPData {type.value} YAML.')


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
                        file=zipfile, message="No submission.yaml file found in submission."
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
                        file=self.submission_file_path, message="No submission.yaml file found in submission."
                    ))
                    return False

            self.included_files = [self.submission_file_path]

            # Open the submission.yaml file and load all YAML documents.
            with open(self.submission_file_path, 'r') as stream:
                try:
                    docs = list(yaml.load_all(stream, Loader=Loader))
                except yaml.YAMLError as e:
                    self.add_validation_message(ValidationMessage(
                        file=self.submission_file_path,
                        message="There was a problem parsing the file:\n\t\t" + str(e).replace('\n', '\n\t\t')
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
                    type = SchemaType.SINGLE_YAML if self.single_yaml_file else SchemaType.SUBMISSION
                    self.valid_files[type] = [self.submission_file_path]

            # Check all files in directory are in included_files
            if not self.single_yaml_file:
                for f in os.listdir(self.directory):
                    file_path = os.path.join(self.directory, f)
                    if file_path not in self.included_files:
                        self.add_validation_message(ValidationMessage(
                            file=file_path, message='%s is not referenced in the submission.' % f
                        ))

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
                    self.included_files.append(location)
                    if not os.path.isfile(location):
                        self.add_validation_message(ValidationMessage(
                            file=self.submission_file_path, message=f"Missing 'additional_resources' file '{resource['location']}'."
                        ))
                        is_valid_submission_doc = False
                    elif '/' in resource['location']:
                        self.add_validation_message(ValidationMessage(
                            file=self.submission_file_path, message=f"Location of 'additional_resources' file '{resource['location']}' should not contain '/'."
                        ))
                        is_valid_submission_doc = False

        # Check for non-empty YAML documents with a 'data_file' key.
        if 'data_file' in doc:

            # Check for presence of '/' in data_file value.
            if '/' in doc['data_file']:
                self.add_validation_message(ValidationMessage(
                    file=self.submission_file_path, message=f"Name of data_file '{doc['data_file']}' should not contain '/'."
                ))
                return False

            # Extract data file from YAML document.
            if self.directory:
                data_file_path = os.path.join(self.directory, doc['data_file'])
            else:
                data_file_path = doc['data_file']

            if not self.single_yaml_file:
                self.included_files.append(data_file_path)

            if not os.path.isfile(data_file_path):
                self.add_validation_message(ValidationMessage(
                    file=data_file_path, message="Missing data_file '%s'." % doc['data_file']
                ))
                return is_valid_submission_doc

            user_data_file_path = self.submission_file_path if self.single_yaml_file else data_file_path

            # Check the remote schema (if defined)
            file_type = None
            if 'data_schema' in doc:
                try:
                    file_type = doc['data_schema']
                    self._load_remote_schema(file_type)
                except FileNotFoundError:
                    self.add_validation_message(ValidationMessage(
                        file=self.submission_file_path, message=f"Remote schema {doc['data_schema']} not found."
                    ))
                    return False

            # Just try to load YAML data file without validating schema.
            try:
                contents = yaml.load(open(data_file_path, 'r'), Loader=Loader)
            except (OSError, yaml.YAMLError) as e:
                problem_type = 'reading' if isinstance(e, OSError) else 'parsing'
                self.add_validation_message(ValidationMessage(
                    file=user_data_file_path,
                    message=f"There was a problem {problem_type} the file:\n\t\t" + str(e).replace('\n', '\n\t\t')
                ))
                return is_valid_submission_doc

            # Validate the YAML data file
            is_valid_data_file = self.data_file_validator.validate(
                file_path=data_file_path, file_type=file_type, data=contents
            )
            if not is_valid_data_file:
                table_msg = f" ({doc['name']})" if self.single_yaml_file else ''
                invalid_msg = f"against schema {doc['data_schema']}" if 'data_schema' in doc else "HEPData YAML"
                self.add_validation_message(ValidationMessage(
                    file=user_data_file_path, message=f'{user_data_file_path}{table_msg} is invalid {invalid_msg}.'
                ))
                if self.single_yaml_file:
                    is_valid_submission_doc = False

                is_valid_data_file = False
                for message in self.data_file_validator.get_messages(data_file_path):
                    self.add_validation_message(ValidationMessage(
                        file=user_data_file_path, message=message.message
                    ))
            elif not self.single_yaml_file:
                type = SchemaType.REMOTE if 'data_schema' in doc else SchemaType.DATA

                if type not in self.valid_files:
                    self.valid_files[type] = []

                if 'data_schema' in doc:
                    self.valid_files[type].append((doc['data_schema'], user_data_file_path))
                else:
                    self.valid_files[type].append(user_data_file_path)

            # For single YAML file, clean up by removing temporary data_file created above.
            if self.single_yaml_file:
                os.remove(doc['data_file'])

        return is_valid_submission_doc

    def _load_remote_schema(self, schema_url):
        # Load the schema with the given URL into self.data_file_validator
        url = urlparse(schema_url)
        schema_path, schema_name = os.path.split(url.path)

        base_url = urlunsplit((url.scheme, url.netloc, schema_path, '', ''))

        resolver = JsonSchemaResolver(base_url)
        downloader = HTTPSchemaDownloader(resolver, base_url)

        # Retrieve and save the remote schema in the local path
        schema_spec = downloader.get_schema_spec(schema_name)
        downloader.save_locally(schema_name, schema_spec)

        # Load the custom schema as a custom type
        local_path = os.path.join(downloader.schemas_path, schema_name)
        self.data_file_validator.load_custom_schema(schema_url, local_path)
