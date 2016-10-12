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

    def validate(self, file_path):
        try:
            default_data_schema = json.load(
                open(self.default_schema_file, 'r'))

            try:
                data = yaml.load_all(open(file_path, 'r'), Loader=yaml.CLoader)
            except: #pragma: no cover
                data = yaml.load_all(open(file_path, 'r')) #pragma: no cover

            for data_item in data:
                if data_item is None:
                    continue
                try:
                    if 'type' in data_item:
                        custom_schema = self.load_custom_schema(data_item['type'])
                        json_validate(data_item, custom_schema)
                    else:
                        json_validate(data_item, default_data_schema)

                except ValidationError as ve:
                    self.add_validation_message(
                        ValidationMessage(file=file_path,
                                          message=ve.message + ' in ' + str(ve.instance)))
            if self.has_errors(file_path):
                return False
            else:
                return True
        except ScannerError as se:
            self.add_validation_message(
                ValidationMessage(file=file_path,
                                  message='There was a problem parsing the file. '
                                          'This can be because you forgot spaces '
                                          'after colons in your YAML file for instance.\n{0}'.format(se.__repr__()))
            )


class UnsupportedDataSchemaException(Exception):
    """
    Represents an error on the request of a custom data schema which does not exist.
    """
    def __init__(self, message=''):
        self.message = message

    def __unicode__(self):
        return self.message
