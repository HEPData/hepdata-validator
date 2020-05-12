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
from abc import ABCMeta
from abc import abstractmethod

# This is compatible both with Python2 and Python3
try:
    from urllib.parse import urljoin
except ImportError:                     # pragma: no cover
    from urlparse import urljoin        # pragma: no cover


class SchemaDownloaderInterface(object):
    """
    Interface for the schema downloader objects.
    Used to validate schemas available across the internet.
    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def get_schema_spec(self, schema_name):
        """
        Retrieves the specified schema from a remote URL.

        :param schema_name: str.
        :return: dict.
        """

        raise NotImplementedError()

    @abstractmethod
    def get_schema_type(self, schema_name):
        """
        Builds the data type of the file given its schema name.

        :param schema_name: str.
        :return: str.
        """

        raise NotImplementedError()

    @abstractmethod
    def save_locally(self, schema_name, schema_spec, overwrite):
        """
        Saves the remote schema in the local file system.

        :param schema_name: str.
        :param schema_spec: str.
        :param overwrite: bool.
        :return: None.
        """

        raise NotImplementedError()


class HTTPSchemaDownloader(SchemaDownloaderInterface):
    """
    Object to download schemas using HTTP / HTTPS.
    Used to validate schemas available across the internet.
    """

    def __init__(self, schemas_resolver, schemas_url):
        """
        Initializes the local folder where schemas will be stored.

        :param schemas_resolver: SchemaResolverInterface
        :param schemas_url: str.
        """

        if not schemas_url.endswith("/"):
            schemas_url += "/"

        self.org = None
        self.project = None
        self.version = None

        self.schemas_path = None
        self.schemas_resolver = schemas_resolver
        self.schemas_url = schemas_url

        self._parse_remote_url(self.schemas_url)
        self._build_local_path("schemas_remote", self.org, self.project, self.version)

    def _parse_remote_url(self, url):
        """
        Parses a remote URL supposing the following structure:
        http(s)://<organization>/<project>/schemas/<version>/

        :param url: str
        """

        nodes = url.split("/")

        try:
            assert re.compile(r"https?:").match(nodes[0])
            assert re.compile(r"[\w.-]+").match(nodes[2])
            assert re.compile(r"[\w.-]+").match(nodes[3])
            assert re.compile(r"schemas").match(nodes[4])
            assert re.compile(r"v?\d+.\d+(.\d+)?").match(nodes[5])
        except (AssertionError, IndexError):
            raise ValueError("Invalid remote schemas URL")
        else:
            self.org = nodes[2]
            self.project = nodes[3]
            self.version = nodes[5]

    def _build_local_path(self, *paths):
        """
        Builds the schemas local saving path.

        :param paths: str.
        """

        base_path = os.path.dirname(__file__)
        saving_path = os.path.join(base_path, *paths)
        self.schemas_path = saving_path

    def get_schema_spec(self, schema_name):
        """
        Downloads the specified schema from a remote URL.

        :param schema_name: str.
        :return: dict.
        """

        schema_url = urljoin(self.schemas_url, schema_name)
        schema_spec = self.schemas_resolver.resolve(schema_url)

        return schema_spec

    def get_schema_type(self, schema_name):
        """
        Builds the data type of the file given its schema name.

        :param schema_name: str.
        :return: str.
        """

        return urljoin(self.schemas_url, schema_name)

    def save_locally(self, schema_name, schema_spec, overwrite=False):
        """
        Saves the remote schema in the local file system.

        :param schema_name: str.
        :param schema_spec: dict.
        :param overwrite: bool.
        :return: None.
        """

        file_path = os.path.join(self.schemas_path, schema_name)
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
            schema_str = json.dumps(schema_spec, indent=2)
            f.write(schema_str)
