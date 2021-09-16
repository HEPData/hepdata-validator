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

import requests
from abc import ABCMeta
from abc import abstractmethod
from copy import deepcopy
from jsonschema import RefResolver
from jsonschema import RefResolutionError

# This is compatible both with Python2 and Python3
try:
    from urllib.parse import urljoin
except ImportError:                     # pragma: no cover
    from urlparse import urljoin        # pragma: no cover

# This is compatible both with Python2 and Python3
try:
    FileNotFoundError
except NameError:                       # pragma: no cover
    FileNotFoundError = IOError         # pragma: no cover


class SchemaResolverInterface(object):
    """
    Interface for the schema resolver objects.
    Used to resolve $ref within the defined schemas.
    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def resolve(self, schema_uri):
        """
        Resolves an entire JSON schema.

        :param schema_uri: str.
        :return: dict.
        """

        raise NotImplementedError()


class DummySchemaResolver(SchemaResolverInterface):
    """ Dummy object to resolve schemas using `requests` as references fetcher. """

    def resolve(self, schema_uri):
        """
        Gets the schema content (dummy).

        :param schema_uri: str.
        :return: dict.
        """

        schema_resp = requests.get(schema_uri)
        schema_resp.raise_for_status()

        return schema_resp.json()       # pragma: no cover


class JsonSchemaResolver(SchemaResolverInterface):
    """
    Object to resolve schemas using `jsonschema` as references fetcher
    The implementation is based on the one provided by Giordon Stark:
    https://gist.github.com/kratsg/96cec81df8c0d78ebdf14bf7b800e938
    """

    def __init__(self, schemas_uri):
        """
        Initializes the inner $ref `jsonschema` resolver.

        :param schemas_uri: str.
        """

        if not schemas_uri.endswith("/"):
            schemas_uri += "/"

        self.schemas_uri = schemas_uri
        self.ref_fetcher = RefResolver(base_uri=self.schemas_uri, referrer=None)

    def _walk_dict(self, obj, ref):
        """
        Iterates a dictionary within the schema resolving every $ref.

        :param obj: dict.
        :param ref: str.
        :return: dict.
        """

        out_obj = deepcopy(obj)

        for key in obj:

            if key == '$ref':
                path = urljoin(ref, out_obj.pop(key))
                new_ref, new_obj = self.ref_fetcher.resolve(path)
                resolved_obj = self._walk_dict(new_obj, new_ref)
                out_obj.update(resolved_obj)

            elif isinstance(obj[key], dict):
                out_obj[key] = self._walk_dict(obj[key], ref)

            elif isinstance(obj[key], list):
                out_obj[key] = self._walk_list(obj[key], ref)

        return out_obj

    def _walk_list(self, seq, ref):
        """
        Iterates a sequence within the schema resolving every $ref.

        :param seq: list.
        :param ref: str.
        :return: list.
        """

        items = []

        for item in seq:
            if isinstance(item, dict):
                item = self._walk_dict(item, ref)
                items.append(item)
            else:
                items.append(item)

        return items

    def resolve(self, schema_uri):
        """
        Resolves a JSON schema either from a remote or a local URI.

        :param schema_uri: str.
        :return: dict.
        """

        try:
            top_ref, top_obj = self.ref_fetcher.resolve(schema_uri)
            resolved_schema = self._walk_dict(top_obj, top_ref)
        except RefResolutionError:
            raise FileNotFoundError(f"Unable to find the desired schema {schema_uri}")

        return resolved_schema
