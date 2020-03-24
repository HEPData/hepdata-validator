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

import os
import requests
from abc import ABCMeta
from abc import abstractmethod


class SchemaDownloaderInterface(object):
    """
    Interface for the schema downloader objects.
    Used to validate schemas available across the internet.
    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def get_schema(self, schema_name):
        """
        Retrieves the specified schema from a remote URL.
        :param schema_name: str.
        :return: str.
        """

        raise NotImplementedError()

    @abstractmethod
    def save_locally(self, schema_name, schema_spec, overwrite):
        """
        Saves the remote schema in the local file system
        :param schema_name: str.
        :param schema_spec: str.
        :param overwrite: bool.
        :return: None.
        """

        raise NotImplementedError()


class HTTPSchemaDownloader(SchemaDownloaderInterface):
    """
    Object to download schemas using HTTP / HTTPS
    Used to validate schemas available across the internet.
    """

    def __init__(self, endpoint, company, version):
        """
        Initializes the local folder where schemas will be stored.
        :param endpoint: str.
        :param company: str.
        :param version: str.
        """

        self.endpoint = endpoint
        self.company = company
        self.version = version

        self.saved_schema_folder = "schemas_remote"
        self.saved_schema_path = self._build_local_path(company, version)

    def _build_local_path(self, company, version):
        """
        Builds the remote schemas complete URL, up to the schema names
        :param company: str
        :param version: str.
        :return: str.
        """

        base_path = os.path.dirname(__file__)
        return os.path.join(base_path, self.saved_schema_folder, company, version)

    def get_schema(self, schema_name):
        """
        Downloads the specified schema from a remote URL.
        :param schema_name: str.
        :return: str.
        """

        schema_url = self.endpoint + "/" + schema_name
        schema_resp = requests.get(schema_url)
        schema_resp.raise_for_status()

        return schema_resp.text

    def save_locally(self, schema_name, schema_spec, overwrite=False):
        """
        Saves the remote schema in the local file system
        :param schema_name: str.
        :param schema_spec: str.
        :param overwrite: bool.
        :return: None.
        """

        file_path = os.path.join(self.saved_schema_path, schema_name)
        file_folder = os.path.dirname(file_path)

        # Skip download if the file exist
        if os.path.isfile(file_path) and not overwrite:
            return

        # This is compatible both with Python2 and Python3
        try:
            os.makedirs(file_folder)
        except OSError:
            if not os.path.isdir(file_folder) or not os.access(file_folder, os.W_OK):
                raise

        with open(file_path, 'w') as f:
            f.write(schema_spec)
