from enum import Enum
import gzip
import os.path
from packaging import version as packaging_version
import shutil
import tempfile
from urllib.parse import urlparse, urlunsplit

import yaml

from hepdata_validator import Validator, ValidationMessage, YamlLoader, YamlDumper
from .schema_resolver import JsonSchemaResolver
from .schema_downloader import HTTPSchemaDownloader
from .submission_file_validator import SubmissionFileValidator
from .data_file_validator import DataFileValidator


INDIVIDUAL_FILE_SIZE_LIMIT = 10485760

class SchemaType(Enum):
    SUBMISSION = 'submission'
    SINGLE_YAML = 'single file'
    DATA = 'data'
    REMOTE = 'remote'


class FullSubmissionValidator(Validator):
    """Class to validate a full submission.

    :attr dict valid_files: map of SchemaType (e.g. submission, data, single
                            file, remote) to lists of valid files
    :attr list submission_docs: List of parsed YAML (represented as `dicts`)
                                from the submission file
    """

    def __init__(self, *args, **kwargs):
        super(FullSubmissionValidator, self).__init__(*args, **kwargs)
        self._submission_file_validator = SubmissionFileValidator(*args, **kwargs)
        self._data_file_validator = DataFileValidator(*args, **kwargs)
        self.valid_files = {}
        self.submission_docs = None
        if 'autoload_remote_schemas' in kwargs:
            self.autoload_remote_schemas = kwargs['autoload_remote_schemas']
        else:
            self.autoload_remote_schemas = True

    def print_valid_files(self):
        for type in SchemaType:
            if type in self.valid_files:
                if type == SchemaType.REMOTE:
                    for schema, file in self.valid_files[type]:
                        print(f'\t {file} is valid against schema {schema}.')
                else:
                    for file in self.valid_files[type]:
                        print(f'\t {file} is valid HEPData {type.value} YAML.')

    def clear_messages(self):
        super().clear_messages()
        self._submission_file_validator.clear_messages()
        self._data_file_validator.clear_messages()

    def clear_all(self):
        """
        Removes all `messages`, `valid_files` and `submission_docs`
        """
        self.clear_messages()
        self.valid_files = {}
        self.submission_docs = None

    def validate(self, directory=None, file=None, archive=None):
        """
        Offline validation of submission.yaml and YAML data files.
        Can check either a single file or a directory.

        :param type directory: Directory to check (defaults to current working directory).
        :param type file: Single submission yaml file to check (overrides directory if both are given)
        :param type archive: Archive file (e.g. .zip, .tar.gz, .gzip) to check (overrides directory and file if both are given)
        :return: Bool showing whether the submission is valid
        :rtype: type
        """
        self.single_yaml_file = False
        self.temp_directory = None
        self.directory = directory

        try:
            # Check input file/directory exists and is valid
            if archive:
                if not os.path.isfile(archive):
                    self._add_validation_message(
                        file=archive, message=f"File {archive} does not exist."
                    )
                    return False

                # Try extracting file to a temp dir
                self.temp_directory = tempfile.mkdtemp()
                try:
                    shutil.unpack_archive(archive, self.temp_directory)
                except Exception as e:
                    self._add_validation_message(
                        file=archive, message=f"Unable to extract file {archive}. Error was: {e}"
                    )
                    return False

                # Find submission.yaml in extracted directory
                for dir_name, _, files in os.walk(self.temp_directory):
                    for filename in files:
                        if filename == 'submission.yaml':
                            self.directory = dir_name

                if not self.directory:
                    self._add_validation_message(
                        file=archive, message="No submission.yaml file found in submission."
                    )
                    return False

            elif file:
                if not os.path.isfile(file):
                    self._add_validation_message(
                        file=file, message=f"File {file} does not exist."
                    )
                    return False
                self.single_yaml_file = True
                self.directory = None

                if file.endswith('.yaml.gz'):
                    # Try extracting file to a temp dir
                    self.temp_directory = tempfile.mkdtemp()
                    unzipped_path = os.path.join(self.temp_directory, os.path.basename(file[:-3]))
                    try:
                        with gzip.GzipFile(file, 'rb') as gzip_file:
                            with open(unzipped_path, 'wb') as unzipped_file:
                                unzipped_file.write(gzip_file.read())
                    except Exception as e:
                        self._add_validation_message(
                            file=file, message=f"Unable to extract file {file}. Error was: {e}"
                        )
                        return False

                    self.submission_file_path = unzipped_path
                    self.directory = self.temp_directory
                else:
                    self.submission_file_path = file

            else:
                self.directory = directory if directory else '.'
                if not os.path.isdir(self.directory):
                    self._add_validation_message(
                        file=self.directory, message=f"Directory {self.directory} does not exist."
                    )
                    return False

            # Get location of the submission.yaml file
            if not self.single_yaml_file:
                self.submission_file_path = os.path.join(self.directory, 'submission.yaml')
                if not os.path.isfile(self.submission_file_path):
                    self._add_validation_message(
                        file=self.submission_file_path, message="No submission.yaml file found in submission."
                    )
                    return False

            self.included_files = [self.submission_file_path]

            # Open the submission.yaml file and load all YAML documents.
            with open(self.submission_file_path, 'r') as submission_file:
                try:
                    self.submission_docs = list(yaml.load_all(submission_file, Loader=YamlLoader))
                except yaml.YAMLError as e:
                    self._add_validation_message(
                        file=self.submission_file_path,
                        message="There was a problem parsing the file:\n\t\t" + str(e).replace('\n', '\n\t\t')
                    )
                    return False

                # Need to remove independent_variables and dependent_variables from single YAML file.
                if self.single_yaml_file:
                    self._create_data_files(self.submission_docs)

                # Validate the submission.yaml file
                is_valid_submission_file = self._submission_file_validator.validate(file_path=self.submission_file_path, data=self.submission_docs)
                if not is_valid_submission_file:
                    self._add_validation_message(
                        file=self.submission_file_path, message=f'{self.submission_file_path} is invalid HEPData YAML.'
                    )
                    for message in self._submission_file_validator.get_messages(self.submission_file_path):
                        self._add_validation_message(
                            file=self.submission_file_path, message=message.message
                        )
                    return False

                # Loop over all YAML documents in the submission.yaml file.
                for doc in self.submission_docs:
                    is_valid_doc_in_submission_file = self._check_doc(doc)
                    if not is_valid_doc_in_submission_file:
                        is_valid_submission_file = False

                if is_valid_submission_file:
                    type = SchemaType.SINGLE_YAML if self.single_yaml_file else SchemaType.SUBMISSION
                    self.valid_files[type] = [self._remove_temp_directory(self.submission_file_path)]

            # Check all files in directory are in included_files
            if not self.single_yaml_file and self.schema_version >= packaging_version.parse("1.1.0"):
                # helper to check if a provided file is not meant to describe HEP data, but rather
                # represents "extended attributes" (e.g.) as a result of BSD tar (default on MacOS)
                # which creates these extra files when archiving files with extended attributes on
                # HSF+ volumes (denoted by "@" in permission bits)
                def is_ext_attr_file(f):
                    # three conditions must be fulfilled
                    # 1. the file must not be referenced in the submission (already checked below)
                    # 2. the file name must have the format "._<actual_file>"
                    prefix = "._"
                    if not f.startswith(prefix):
                        return False
                    # 3. a file named "<actual_file>" must exist in the same directory
                    if not os.path.isfile(os.path.join(self.directory, f[len(prefix):])):
                        return False
                    return True

                for f in os.listdir(self.directory):
                    file_path = os.path.join(self.directory, f)
                    if file_path not in self.included_files:
                        self._add_validation_message(
                            file=file_path, message=f'{f} is not referenced in the submission.'
                        )
                        if is_ext_attr_file(f):
                            self._add_validation_message(
                               file=file_path, message=f'{f} might be a file created by tar on MacOS. Set COPYFILE_DISABLE=1 before creating the archive.',
                               level='hint'
                            )

            return len(self.messages) == 0
        finally:
            if self.temp_directory:
                # Delete temporary Directory
                shutil.rmtree(self.temp_directory)

    def _add_validation_message(self, file, message, **kwargs):
        if self.temp_directory:
            # Remove temp directory from filename and message
            file = self._remove_temp_directory(file)
            message = self._remove_temp_directory(message)

        self.add_validation_message(ValidationMessage(
            file=file, message=message, **kwargs
        ))

    def _remove_temp_directory(self, s):
        if self.temp_directory:
            return s.replace(self.temp_directory + '/', '')
        else:
            return s

    def _create_data_files(self, docs):
        for doc in docs:
            if 'name' in doc:
                file_name = doc['name'].replace(' ', '_').replace('/', '-') + '.yaml'
                doc['data_file'] = file_name
                if self.directory:
                    file_name = os.path.join(self.directory, file_name)
                with open(file_name, 'w') as data_file:
                    yaml.dump({'independent_variables': doc.pop('independent_variables', None),
                               'dependent_variables': doc.pop('dependent_variables', None)}, data_file, Dumper=YamlDumper)

    def _check_doc(self, doc):
        # Skip empty YAML documents.
        if not doc:
            return True

        is_valid_submission_doc = True

        # Check for presence of local files given as additional_resources.
        if 'additional_resources' in doc:
            for resource in doc['additional_resources']:
                # For v0 schemas, allow resource locations that start with '/resource/'
                if self.schema_version.major == 0:
                    unchecked_prefixes = ('http', '/resource/')
                else:
                    unchecked_prefixes = 'http'

                if not resource['location'].startswith(unchecked_prefixes):
                    location = os.path.join(self.directory, resource['location'])
                    self.included_files.append(location)
                    if '/' in resource['location']:
                        self._add_validation_message(
                            file=self.submission_file_path, message=f"Location of 'additional_resources' file '{resource['location']}' should not contain '/'."
                        )
                        is_valid_submission_doc = False
                    elif not os.path.isfile(location):
                        self._add_validation_message(
                            file=self.submission_file_path, message=f"Missing 'additional_resources' file '{resource['location']}'."
                        )
                        is_valid_submission_doc = False

        # Check for non-empty YAML documents with a 'data_file' key.
        if 'data_file' in doc:

            # Check for presence of '/' in data_file value.
            if '/' in doc['data_file']:
                self._add_validation_message(
                    file=self.submission_file_path, message=f"Name of data_file '{doc['data_file']}' should not contain '/'."
                )
                return False

            # Extract data file from YAML document.
            if self.directory:
                data_file_path = os.path.join(self.directory, doc['data_file'])
            else:
                data_file_path = doc['data_file']

            if not self.single_yaml_file:
                self.included_files.append(data_file_path)

            if not os.path.isfile(data_file_path):
                self._add_validation_message(
                    file=data_file_path, message="Missing data_file '%s'." % doc['data_file']
                )
                return is_valid_submission_doc

            file_size = os.path.getsize(data_file_path)
            if file_size > INDIVIDUAL_FILE_SIZE_LIMIT: # 10MB limit for each file
                self._add_validation_message(
                    file=data_file_path,
                    message=f"Size of data_file '{doc['data_file']}' ({file_size} bytes) is bigger than the limit of " \
                            f"{INDIVIDUAL_FILE_SIZE_LIMIT} bytes. Try adding the file as an additional_resource instead."
                )
                return is_valid_submission_doc

            user_data_file_path = self.submission_file_path if self.single_yaml_file else data_file_path
            user_data_file_path = self._remove_temp_directory(user_data_file_path)

            # Check the remote schema (if defined)
            file_type = None
            if 'data_schema' in doc:
                try:
                    file_type = doc['data_schema']
                    if self.autoload_remote_schemas:
                        self.load_remote_schema(file_type)
                    elif doc['data_schema'] not in self._data_file_validator.custom_data_schemas:
                        self._add_validation_message(
                            file=self.submission_file_path,
                            message=f"Autoloading of remote schema {doc['data_schema']} is not allowed."
                        )
                        return False
                except FileNotFoundError:
                    self._add_validation_message(
                        file=self.submission_file_path, message=f"Remote schema {doc['data_schema']} not found."
                    )
                    return False

            # Just try to load YAML data file without validating schema.
            try:
                contents = yaml.load(open(data_file_path, 'r'), Loader=YamlLoader)
            except (OSError, yaml.YAMLError) as e:
                problem_type = 'reading' if isinstance(e, OSError) else 'parsing'
                self._add_validation_message(
                    file=user_data_file_path,
                    message=f"There was a problem {problem_type} the file:\n\t\t" + str(e).replace('\n', '\n\t\t')
                )
                return is_valid_submission_doc

            # Validate the YAML data file
            is_valid_data_file = self._data_file_validator.validate(
                file_path=data_file_path, file_type=file_type, data=contents
            )
            if not is_valid_data_file:
                table_msg = f" ({doc['name']})" if self.single_yaml_file else ''
                invalid_msg = f"against schema {doc['data_schema']}" if 'data_schema' in doc else "HEPData YAML"
                self._add_validation_message(
                    file=user_data_file_path, message=f'{user_data_file_path}{table_msg} is invalid {invalid_msg}.'
                )
                if self.single_yaml_file:
                    is_valid_submission_doc = False

                is_valid_data_file = False
                for message in self._data_file_validator.get_messages(data_file_path):
                    self._add_validation_message(
                        file=user_data_file_path, message=message.message
                    )
            elif not self.single_yaml_file:
                type = SchemaType.REMOTE if 'data_schema' in doc else SchemaType.DATA

                if type not in self.valid_files:
                    self.valid_files[type] = []

                if 'data_schema' in doc:
                    self.valid_files[type].append((doc['data_schema'], user_data_file_path))
                else:
                    self.valid_files[type].append(user_data_file_path)

            # For single YAML file, clean up by removing temporary data_file created above.
            if self.single_yaml_file and not self.temp_directory:
                os.remove(doc['data_file'])

        return is_valid_submission_doc

    def load_remote_schema(self, schema_url=None, base_url=None, schema_name=None):
        """
        Loads the given schema into the validator's DataSubmissionValidator.
        """
        if schema_url:
            url = urlparse(schema_url)
            schema_path, schema_name = os.path.split(url.path)
            base_url = urlunsplit((url.scheme, url.netloc, schema_path, '', ''))
        elif not base_url or not schema_name:
            raise ValueError("Must provide EITHER schema_url OR both base_url and schema_name")

        resolver = JsonSchemaResolver(base_url)
        downloader = HTTPSchemaDownloader(resolver, base_url)
        if not schema_url:
            schema_url = downloader.get_schema_type(schema_name)

        # Don't download again if already loaded
        if schema_url in self._data_file_validator.custom_data_schemas:
            return

        # Retrieve and save the remote schema in the local path
        schema_spec = downloader.get_schema_spec(schema_name)
        downloader.save_locally(schema_name, schema_spec)

        # Load the custom schema as a custom type
        local_path = os.path.join(downloader.schemas_path, schema_name)
        self._data_file_validator.load_custom_schema(schema_url, local_path)
