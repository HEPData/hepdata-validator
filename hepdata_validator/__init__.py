import json
from jsonschema import validate, ValidationError
import yaml
from yaml.scanner import ScannerError
from yaml.parser import ParserError

__author__ = 'eamonnmaguire'


class Validator(object):
    """
    Provides a general 'interface' for Validator in HEPdata
    which validates schema files created with the
    JSONschema syntax http://json-schema.org/
    """
    messages = {}
    schema_file = ''

    def __init__(self):
        self.messages = {}

    def validate(self, **kwargs):
        """
        Validates a file.
        :param file_path: path to file to be loaded.
        :param data: pre loaded YAML object (optional).
        :return: true if valid, false otherwise
        """
        schema = json.load(open(self.schema_file, 'r'))

        data = kwargs.pop("data", None)
        file_path = kwargs.pop("file_path", None)

        if data is None:

            try:
                try:
                    data = yaml.load(open(file_path, 'r'), Loader=yaml.CLoader)
                except ScannerError as se:
                    self.add_validation_message(ValidationMessage(file=file_path, message=str(se)))
                    return False
            except: #pragma: no cover
                try: #pragma: no cover
                    data = yaml.load(open(file_path, 'r')) #pragma: no cover
                except ScannerError as se: #pragma: no cover
                    self.add_validation_message(ValidationMessage(file=file_path, message=str(se))) #pragma: no cover
                    return False #pragma: no cover

        try:
            validate(data, schema)

        except ValidationError as ve:
            self.add_validation_message(
                ValidationMessage(file=file_path,
                                  message="{} in {}".format(ve.message, ve.instance)))
            return False
        except ParserError as pe:
            self.add_validation_message(
                ValidationMessage(file=file_path,
                                  message=pe.__str__()))
            return False

        return True

    def has_errors(self, file_name):
        """
        Returns true if the provided file name has error messages
        associated with it, false otherwise.
        :param file_name:
        :return: boolean
        """
        return file_name in self.messages

    def get_messages(self, file_name=None):
        """
        Return messages for a file (if file_name provided).
        If file_name is none, returns all messages as a dict.
        :param file_name:
        :return: array if file_name is provided, dict otherwise.
        """
        if file_name is None:
            return self.messages

        elif file_name in self.messages:
            return self.messages[file_name]

        else:
            return []

    def clear_messages(self):
        """
        Removes all error messages
        :return:
        """
        self.messages = {}

    def add_validation_message(self, message):
        """
        Adds a message to the messages dict
        :param message:
        """
        if message.file not in self.messages:
            self.messages[message.file] = []

        self.messages[message.file].append(message)

    def print_errors(self, file_name):
        """
        Prints the errors observed for a file
        """
        for error in self.get_messages(file_name):
            print '\t', error.__unicode__()


class ValidationMessage(object):
    """
    An object to encapsulate information about an error including
    the file the error originated in, the error level, and the
    message itself.
    """
    file = ''
    level = ''
    message = ''

    def __init__(self, file='', level='error', message=''):
        self.file = file
        self.level = level
        self.message = message

    def __unicode__(self):
        return self.level + ' - ' + self.message
