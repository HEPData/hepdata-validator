# -*- coding: utf-8 -*-
#
# This file is part of HEPData.
# Copyright (C) 2020 CERN.
#
# HEPData is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# HEPData is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with HEPData; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, CERN does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

import abc
import os

from jsonschema import validate as json_validate, ValidationError
from jsonschema.validators import validator_for
from jsonschema.exceptions import by_relevance
from packaging import version as packaging_version

from .version import __version__

# We try to load using the CSafeLoader for speed improvements
YamlLoader = None
YamlDumper = None
use_libyaml = os.environ.get('USE_LIBYAML', True)
if use_libyaml and use_libyaml not in ('False', 'false', 'f', 'F'):
    try:
        from yaml import CSafeLoader as YamlLoader
        from yaml import CSafeDumper as YamlDumper
    except ImportError:  # pragma: no cover
        pass

if YamlLoader is None or YamlDumper is None:
    from yaml import SafeLoader as YamlLoader
    from yaml import SafeDumper as YamlDumper

__all__ = ('__version__', )

VALID_SCHEMA_VERSIONS = ['1.1.0', '1.0.1', '1.0.0', '0.1.0']
LATEST_SCHEMA_VERSION = VALID_SCHEMA_VERSIONS[0]

RAW_SCHEMAS_URL = 'https://raw.githubusercontent.com/HEPData/hepdata-validator/' \
    + __version__ + '/hepdata_validator/schemas'

class Validator(object):
    """
    Provides a general 'interface' for Validator in HEPData
    which validates schema files created with the
    JSON Schema syntax http://json-schema.org/
    """
    __metaclass__ = abc.ABCMeta

    def __init__(self, *args, **kwargs):
        self.messages = {}
        self.default_schema_file = ''
        self.schemas = kwargs.get('schemas', {})
        self.schema_folder = kwargs.get('schema_folder', 'schemas')
        self.schema_version_string = kwargs.get('schema_version', LATEST_SCHEMA_VERSION)
        if self.schema_version_string not in VALID_SCHEMA_VERSIONS:
            raise ValueError('Invalid schema version ' + self.schema_version_string)
        self.schema_version = packaging_version.parse(self.schema_version_string)


    def _get_schema_filepath(self, schema_filename):
        full_filepath = os.path.join(self.base_path,
                                     self.schema_folder,
                                     self.schema_version_string,
                                     schema_filename)

        if not os.path.isfile(full_filepath):
            raise ValueError('Invalid schema file ' + full_filepath)

        return full_filepath

    @abc.abstractmethod
    def validate(self, **kwargs):
        """
        Validates a file.

        :param file_path: path to file to be loaded.
        :param data: pre loaded YAML object (optional).
        :return: true if valid, false otherwise
        """

    def _validate_json_against_schema(self, file_path, data, schema, sort_fn=None, **kwargs):
        """
        Validates json_data against the given schema.
        Roughly follows the pattern of jsonschema.validate but adds errors to
        self.messages, and will add multiple errors if they exist.

        :param type file_path: path to file being checked
        :param type data: JSON/YAML data to validate
        :param type schema: schema to validate data against
        :param type sort_fn: Function to sort error messages to get most
            relevant (see docs for `jsonschema.exceptions.by_relevance`).
        :param type **kwargs: Other kwargs to use when creating the
            `jsonschema.IValidator` instance.
        """
        # Create validator ourselves so we can tweak the errors
        cls = validator_for(schema)
        cls.check_schema(schema)
        v = cls(schema, **kwargs)

        if not sort_fn:
            sort_fn = by_relevance()

        # Show all errors found, using best error in context for each
        for error in v.iter_errors(data):
            best = sorted([error] + error.context, key=sort_fn)[0]
            self.add_validation_error(file_path, best)

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
        Removes all error messages.

        :return:
        """
        self.messages = {}

    def add_validation_error(self, file_path, ve):
        """
        Formats a validation error into a readable error message and adds it to
        the messages dict
        """
        location = ''
        if ve.path:
            for part in ve.path:
                if type(part) == int:
                    location += '[{0}]'.format(part)
                elif not location:
                    location = part
                else:
                    location += '.' + part

        message = ve.message
        if location:
            message += f" in '{location}'"
        # Add expected schema section if it it's present and isn't the full schema
        if isinstance(ve.schema, dict) and '$schema' not in ve.schema.keys():
            message += f" (expected: {ve.schema})"

        self.add_validation_message(ValidationMessage(file=file_path,
                                                      message=message))

    def add_validation_message(self, message):
        """
        Adds a message to the messages dict.

        :param message:
        """
        if message.file not in self.messages:
            self.messages[message.file] = []

        self.messages[message.file].append(message)

    def print_errors(self, file_name):
        """
        Prints the errors observed for a file.
        """
        for error in self.get_messages(file_name):
            print('\t', error.__unicode__())


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
