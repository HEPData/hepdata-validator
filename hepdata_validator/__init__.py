# -*- coding: utf-8 -*-
#
# This file is part of HEPData.
# Copyright (C) 2016 CERN.
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

from .version import __version__

__all__ = ('__version__', )


class Validator(object):
    """
    Provides a general 'interface' for Validator in HEPdata
    which validates schema files created with the
    JSONschema syntax http://json-schema.org/
    """
    __metaclass__ = abc.ABCMeta

    messages = {}
    default_schema_file = ''

    def __init__(self, *args, **kwargs):
        self.messages = {}

        self.schemas = kwargs.get('schemas', {})

    @abc.abstractmethod
    def validate(self, **kwargs):
        """
        Validates a file.
        :param file_path: path to file to be loaded.
        :param data: pre loaded YAML object (optional).
        :return: true if valid, false otherwise
        """

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