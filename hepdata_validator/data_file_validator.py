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
import re

from packaging import version as packaging_version
import yaml

from hepdata_validator import Validator, ValidationMessage, YamlLoader
from jsonschema import ValidationError
from jsonschema.exceptions import by_relevance

__author__ = 'eamonnmaguire'


class DataFileValidator(Validator):
    """
    Validates the YAML/JSON data file.
    """
    base_path = os.path.dirname(__file__)
    schema_name = 'data_schema.json'

    def __init__(self, *args, **kwargs):
        super(DataFileValidator, self).__init__(*args, **kwargs)
        self.default_schema_file = self._get_schema_filepath(self.schema_name)
        self.custom_data_schemas = {}

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
                                            self.schema_version_string,
                                            "{0}_schema.json".format(type))

            with open(_schema_file, 'r') as f:
                custom_data_schema = json.load(f)
                self.custom_data_schemas[type] = custom_data_schema

            return custom_data_schema
        except Exception:
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
                    data = yaml.load(df, Loader=YamlLoader)
                    if data is None:
                        self.add_validation_message(ValidationMessage(
                            file=file_path,
                            message='No data found in file.'
                        ))
                        return False
            except Exception as e:
                self.add_validation_message(ValidationMessage(
                    file=file_path,
                    message='There was a problem parsing the file.\n' + e.__str__(),
                ))
                return False

        try:
            is_custom_schema = False
            sort_fn = None

            if file_type:
                is_custom_schema = True
                data_schema = self.load_custom_schema(file_type)
            elif 'type' in data:
                is_custom_schema = True
                data_schema = self.load_custom_schema(data['type'])
            else:
                with open(self.default_schema_file, 'r') as f:
                    data_schema = json.load(f)

                # Make 'oneOf' errors more relevant to give better error
                # messages about 'low' without 'high' etc
                sort_fn = by_relevance(strong='oneOf', weak=[])

            self._validate_json_against_schema(file_path, data, data_schema, sort_fn)

            if not is_custom_schema and \
               self.schema_version.major > 0:
                try:
                    self.check_error_values(file_path, data)
                    self.check_length_values(file_path, data)
                    if self.schema_version >= packaging_version.parse("1.1.0"):
                        self.check_independent_variable_values(file_path, data)
                except Exception:
                    # If the file did not validate against the schema, we
                    # ignore any exceptions as they're likely to be due to
                    # missing fields etc.
                    # Otherwise we return error as unexpected.
                    if not self.has_errors(file_path):
                        self.add_validation_message(ValidationMessage(
                            file=file_path,
                            message=f"An unexpected error occurred whilst validating {file_path}. Please contact info@hepdata.net if this issue recurs.",
                        ))  #pragma: no cover

        except UnsupportedDataSchemaException as ex:
            self.add_validation_message(ValidationMessage(
                file=file_path,
                message=ex.message,
            ))

        if self.has_errors(file_path):
            return False
        else:
            return True

    def check_independent_variable_values(self, file_path, data_item):
        """
        Check that 'independent_variables' values are not a range like 1.7-4.7.

        :param data_item: YAML document from submission.yaml
        :return: raise ValidationError if not numeric
        """
        for i, var in enumerate(data_item['independent_variables']):
            for j, v in enumerate(var['values']):
                if 'value' in v and isinstance(v['value'], str) and '-' in v['value']:
                    m = re.match(r'^[+-]?\d+(\.\d*)?([eE][+-]?\d+)?\s*-\s*[+-]?\d+(\.\d*)?([eE][+-]?\d+)?$', v['value'])
                    if m:
                        error = ValidationError(
                            "independent_variable 'value' must not be a string range (use 'low' and 'high' to represent a range): '%s'" % v['value'],
                            path=['independent_variables', i, 'values', j, 'value'],
                            instance=data_item['independent_variables'],
                            schema={"type": "number or string (not a range)"}
                        )
                        self.add_validation_error(file_path, error)

    def check_error_values(self, file_path, data):
        """
        Check that uncertainties are not all zero.
        Adds validation error if uncertainties are all zero.

        :param data: data table in YAML format
        """
        for dependent_variable in data['dependent_variables']:
            for i, value in enumerate(dependent_variable['values']):
                if 'errors' in value:
                    zero_uncertainties = []
                    for j, error in enumerate(value['errors']):
                        has_asymerror = False
                        if 'symerror' in error:
                            error_plus = error_minus = self.convert_to_float(
                                error['symerror'],
                                file_path=file_path,
                                path=['dependent_variables', 'values', i, 'errors', j, 'symerror'],
                                instance=data['dependent_variables']
                            )
                        elif 'asymerror' in error:
                            has_asymerror = True
                            error_plus = self.convert_to_float(
                                error['asymerror']['plus'],
                                file_path=file_path,
                                path=['dependent_variables', 'values', i, 'errors', j, 'asymerror', 'plus'],
                                instance=data['dependent_variables']
                            )
                            error_minus = self.convert_to_float(
                                error['asymerror']['minus'],
                                file_path=file_path,
                                path=['dependent_variables', 'values', i, 'errors', j, 'asymerror', 'minus'],
                                instance=data['dependent_variables']
                            )

                        if error_plus == '' and error_minus == '':
                            if has_asymerror:
                                msg = "asymerror plus and minus cannot both be empty"
                                sub_path = 'asymerror'
                            else:
                                msg = "symerror cannot be empty"
                                sub_path = 'symerror'
                            error = ValidationError(
                                msg,
                                path=['dependent_variables', 'values', i, 'errors', j, sub_path],
                                instance=data['dependent_variables']
                            )
                            self.add_validation_error(file_path, error)

                        if error_plus == 0 and error_minus == 0:
                            zero_uncertainties.append(True)
                        else:
                            zero_uncertainties.append(False)

                    if len(zero_uncertainties) > 0 and all(zero_uncertainties):
                        error = ValidationError(
                            "Uncertainties should not all be zero",
                            path=['dependent_variables', 'values', i, 'errors'],
                            instance=data['dependent_variables']
                        )
                        self.add_validation_error(file_path, error)

    def check_length_values(self, file_path, data):
        """
        Check that the length of the 'values' list is consistent for
        each of the independent_variables and dependent_variables.
        Adds validation error if uncertainties are all zero.

        :param data: data table in YAML format
        """
        indep_count = [len(indep['values']) for indep in data['independent_variables'] if 'values' in indep]
        dep_count = [len(dep['values']) for dep in data['dependent_variables'] if 'values' in dep]
        if len(set(indep_count + dep_count)) > 1:  # if more than one unique count
            error = ValidationError(
                "Inconsistent length of 'values' list: " +
                "independent_variables %s, dependent_variables %s" % (str(indep_count), str(dep_count)),
                instance=data
            )
            self.add_validation_error(file_path, error)

    def convert_to_float(self, error, file_path, path, instance):
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
            if error != '':  # empty string is allowed in some circumstances
                validation_error = ValidationError(
                    f"Invalid error value {error}: value must be a number (possibly ending in %)",
                    path=path,
                    instance=instance
                )
                self.add_validation_error(file_path, validation_error)

        return error


class UnsupportedDataSchemaException(Exception):
    """
    Represents an error on the request of a custom data schema which does not exist.
    """
    def __init__(self, message=''):
        self.message = message

    def __unicode__(self):
        return self.message
