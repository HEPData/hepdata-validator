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

import json
import os
import yaml

# We try to load using the CSafeLoader for speed improvements.
try:
    from yaml import CSafeLoader as Loader
except ImportError: #pragma: no cover
    from yaml import SafeLoader as Loader #pragma: no cover

from hepdata_validator import Validator, ValidationMessage
from jsonschema import validate as json_validate, ValidationError

__author__ = 'eamonnmaguire'


class DataFileValidator(Validator):
    """
    Validates the YAML/JSON data file.
    """
    base_path = os.path.dirname(__file__)
    schema_name = 'data_schema.json'
    custom_data_schemas = {}

    def __init__(self, *args, **kwargs):
        super(DataFileValidator, self).__init__(*args, **kwargs)
        self.default_schema_file = self._get_schema_filepath(self.schema_name)

    def load_custom_schema(self, type, schema_file_path=None):
        """
        Loads a custom schema, or will use a stored version for the given type if available.

        :param type: e.g. histfactory
        :return:
        """
        try:
            if type in self.custom_data_schemas:
                return self.custom_data_schemas[type]

            if schema_file_path:
                _schema_file = schema_file_path
            else:
                _schema_file = os.path.join(self.base_path,
                                            self.schema_folder,
                                            self.schema_version,
                                            "{0}_schema.json".format(type))

            with open(_schema_file, 'r') as f:
                custom_data_schema = json.load(f)
                self.custom_data_schemas[type] = custom_data_schema

            return custom_data_schema
        except Exception as e:
            raise UnsupportedDataSchemaException(
                message="There is no schema defined for the '{0}' data type.".format(type))

    def validate(self, **kwargs):
        """
        Validates a data file.

        :param file_path: path to file to be loaded.
        :param file_type: file data type (optional).
        :param data: pre loaded YAML object (optional).
        :return: Bool to indicate the validity of the file.
        """

        file_path = kwargs.pop("file_path", None)
        file_type = kwargs.pop("file_type", None)
        data = kwargs.pop("data", None)

        if file_path is None:
            raise LookupError("file_path argument must be supplied")

        if data is None:

            try:
                # The yaml package support both JSON and YAML
                with open(file_path, 'r') as df:
                    data = yaml.load(df, Loader=Loader)
            except Exception as e:
                self.add_validation_message(ValidationMessage(
                    file=file_path,
                    message='There was a problem parsing the file.\n' + e.__str__(),
                ))
                return False

        try:
            if file_type:
                custom_schema = self.load_custom_schema(file_type)
                json_validate(data, custom_schema)
            elif 'type' in data:
                custom_schema = self.load_custom_schema(data['type'])
                json_validate(data, custom_schema)
            else:
                with open(self.default_schema_file, 'r') as f:
                    default_data_schema = json.load(f)
                    json_validate(data, default_data_schema)
                if self._get_major_version() > 0:
                    check_for_zero_uncertainty(data)
                    check_length_values(data)

        except ValidationError as ve:
            self.add_validation_message(ValidationMessage(
                file=file_path,
                message=ve.message + ' in ' + str(ve.instance),
            ))

        except UnsupportedDataSchemaException as ex:
            self.add_validation_message(ValidationMessage(
                file=file_path,
                message=ex.message,
            ))

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


def check_for_zero_uncertainty(data):
    """
    Check that uncertainties are not all zero.
    
    :param data: data table in YAML format
    :return: raise ValidationError if uncertainties are all zero
    """
    for dependent_variable in data['dependent_variables']:

        if 'values' in dependent_variable:
            for value in dependent_variable['values']:

                if 'errors' in value:
                    zero_uncertainties = []
                    for error in value['errors']:

                        if 'symerror' in error:
                            error_plus = error_minus = error['symerror']
                        elif 'asymerror' in error:
                            error_plus = error['asymerror']['plus']
                            error_minus = error['asymerror']['minus']

                        error_plus = convert_to_float(error_plus)
                        error_minus = convert_to_float(error_minus)

                        if error_plus == 0 and error_minus == 0:
                            zero_uncertainties.append(True)
                        else:
                            zero_uncertainties.append(False)

                    if len(zero_uncertainties) > 0 and all(zero_uncertainties):
                        raise ValidationError('Uncertainties should not all be zero', instance=value)


def convert_to_float(error):
    """
    Convert error from a string to a float if possible.

    :param error: uncertainty from either 'symerror' or 'asymerror'
    :return: error as a float if possible, otherwise the original string
    """
    if isinstance(error, str):
        error = error.replace('%', '')  # strip percentage symbol
    try:
        error = float(error)
    except ValueError:
        pass  # for example, an empty string

    return error


def check_length_values(data):
    """
    Check that the length of the 'values' list is consistent for
    each of the independent_variables and dependent_variables.
    
    :param data: data table in YAML format
    :return: raise ValidationError if inconsistent
    """
    indep_count = [len(indep['values']) for indep in data['independent_variables']]
    dep_count = [len(dep['values']) for dep in data['dependent_variables']]
    if len(set(indep_count + dep_count)) > 1:  # if more than one unique count
        raise ValidationError("Inconsistent length of 'values' list: " + 
                              "independent_variables%s, dependent_variables%s" % (str(indep_count), str(dep_count)),
                              instance=data)