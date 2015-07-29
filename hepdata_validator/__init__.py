import json
from jsonschema import validate, ValidationError
import yaml
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

    def validate(self, file_path):
        schema = json.load(open(self.schema_file, 'r'))

        try:
            data = yaml.load(open(file_path, 'r'))
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
        return file_name in self.messages

    def get_messages(self, file_name=None):
        if file_name is None:
            return self.messages

        elif file_name in self.messages:
            return self.messages[file_name]

        else:
            return []

    def clear_messages(self):
        self.messages = {}

    def add_validation_message(self, message):
        if message.file not in self.messages:
            self.messages[message.file] = []

        self.messages[message.file].append(message)


class ValidationMessage(object):
    file = ''
    level = ''
    message = ''

    def __init__(self, file='', level='error', message=''):
        self.file = file
        self.level = level
        self.message = message

    def __unicode__(self):
        return self.level + ' - ' + self.message
