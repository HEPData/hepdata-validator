import json
import os
import pytest
from hepdata_validator.schema_resolver import JsonSchemaResolver

# This is compatible both with Python2 and Python3
try:
    FileNotFoundError
except NameError:                       # pragma: no cover
    FileNotFoundError = IOError         # pragma: no cover


####################################################
#                 Tests fixtures                   #
####################################################


@pytest.fixture(scope="module")
def data_path():
    """
    Returns the absolute path to the test files
    """

    base_dir = os.path.dirname(os.path.realpath(__file__))
    return os.path.join(base_dir, 'test_data')


@pytest.fixture(scope="module")
def json_resolver():
    """
    Generates a valid JsonSchemaResolver using a real URL
    """

    return JsonSchemaResolver("https://scikit-hep.org/pyhf/schemas/1.0.0/")


####################################################
#             JsonSchemaResolver tests             #
####################################################


def test_json_resolver_creation():
    """
    Tests the creation of a JsonSchemaResolver object
    """

    invalid_url = "https://testing.com/test-project/schemas/1.0.0"
    correct_url = "https://testing.com/test-project/schemas/1.0.0/"

    resolver = JsonSchemaResolver(invalid_url)

    assert resolver.schemas_uri == correct_url


def test_json_resolver_existing_schema(json_resolver, data_path):
    """
    Tests the JsonSchemaResolver resolution of an existing schema
    """

    file_name = "workspace.json"
    remote_spec = json_resolver.resolve(file_name)

    local_path = os.path.join(data_path, 'custom_remote_data_schema.json')

    with open(local_path, 'r') as file:
        local_spec = file.read()
        local_spec = json.loads(local_spec)

    assert remote_spec == local_spec


def test_json_resolver_non_existing_schema(json_resolver):
    """
    Tests the JsonSchemaResolver resolution of a non-existing schema
    """

    file_name = "random_name.json"

    with pytest.raises(FileNotFoundError):
        json_resolver.resolve(file_name)
