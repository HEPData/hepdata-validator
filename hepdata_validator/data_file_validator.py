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

import json

import os
import yaml
from yaml.scanner import ScannerError

from hepdata_validator import Validator, ValidationMessage
from jsonschema import validate as json_validate, ValidationError

__author__ = 'eamonnmaguire'


class DataFileValidator(Validator):
    """
    Validates the Data file YAML/JSON file
    """
    base_path = os.path.dirname(__file__)
    default_schema_file = base_path + '/schemas/data_schema.json'

    custom_data_schemas = {}

    def load_custom_schema(self, type, schema_file_path=None):
        """
        Loads a custom schema, or will used a stored version for the given type if available
        :param type: e.g. histfactory
        :return:
        """
        try:
            if type in self.custom_data_schemas:
                return self.custom_data_schemas[type]

            if schema_file_path:
                _schema_file = schema_file_path
            else:
                _schema_file = os.path.join(self.base_path, 'schemas', "{0}_schema.json".format(type))

            custom_data_schema = json.load(open(_schema_file, 'r'))
            self.custom_data_schemas[type] = custom_data_schema

            return custom_data_schema
        except Exception as e:
            raise UnsupportedDataSchemaException(
                message="There is no schema defined for the '{0}' data type.".format(type))

    def validate(self, **kwargs):
        """
        Validates a data file

        :param file_path: path to file to be loaded.
        :param data: pre loaded YAML object (optional).
        :return: Bool to indicate the validity of the file.
        """

        default_data_schema = json.load(open(self.default_schema_file, 'r'))

        # even though we are using the yaml package to load,
        # it supports JSON and YAML
        data = kwargs.pop("data", None)
        file_path = kwargs.pop("file_path", None)

        if file_path is None:
            raise LookupError("file_path argument must be supplied")

        if data is None:

            try:
                # We try to load using the CLoader for speed improvements.
                try:
                    data = yaml.load(open(file_path, 'r'), Loader=yaml.CLoader)
                except ScannerError as se:
                    self.add_validation_message(ValidationMessage(file=file_path, message=
                    'There was a problem parsing the file.\n' + str(se)))
                    return False
            except: #pragma: no cover
                try:  # pragma: no cover
                    data = yaml.load(open(file_path, 'r'))  # pragma: no cover
                except ScannerError as se:  # pragma: no cover
                    self.add_validation_message(
                        ValidationMessage(file=file_path, message=
                    'There was a problem parsing the file.\n' + str(se))) # pragma: no cover
                    return False

        try:

            if 'type' in data:
                custom_schema = self.load_custom_schema(data['type'])
                json_validate(data, custom_schema)
            else:
                json_validate(data, default_data_schema)

        except ValidationError as ve:

            self.add_validation_message(
                ValidationMessage(file=file_path,
                                    message=ve.message + ' in ' + str(ve.instance)))

        if self.has_errors(file_path):
            return False
        else:
            return True


class UnsupportedDataSchemaException(Exception):
    """
    Represents an error on the request of a custom data schema which does not exist.
    """
    def __init__(self, message=''):
        self.message = message

    def __unicode__(self):
        return self.message
