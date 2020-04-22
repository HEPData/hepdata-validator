import json
import os
import pytest
import shutil as sh
from hepdata_validator.schema_downloader import HTTPSchemaDownloader
from hepdata_validator.schema_resolver import DummySchemaResolver
from requests.exceptions import HTTPError
from mock import patch


####################################################
#                 Tests fixtures                   #
####################################################


@pytest.fixture(scope="module")
def http_downloader():
    """
    Generates a valid HTTPSchemaDownloader using example names
    """

    return HTTPSchemaDownloader(
        schemas_resolver=DummySchemaResolver(),
        schemas_url="https://testing.com/test-project/schemas/1.0.0/",
    )


####################################################
#                   Tests mocks                    #
####################################################


class MockedResponse(object):

    def __init__(self, content, http_code):
        self.content = content
        self.http_code = http_code

    def raise_for_status(self):
        if self.http_code != 200:
            raise HTTPError

    def json(self):
        return json.loads(self.content)


def get_patched_valid_response(url):
    return MockedResponse('{"field_1": "value_1", "field_2": "value_2"}', 200)


def get_patched_invalid_response(url):
    return MockedResponse("Not found", 404)


####################################################
#            HTTPSchemaDownloader tests            #
####################################################


@pytest.mark.parametrize(
    "url",
    [
        "ftp://testing.com/project/schemas/1.0.0",
        "https://testing.com/project/schemas/v1",
        "https://testing.com/schemas/1.0.0",
        "https://testing.com/project/1.0.0",
        "https://testing.com/1.0.0",
    ],
)
def test_http_downloader_invalid_url(url):
    """
    Tests the correct validation of urls by the HTTPSchemaDownloader
    """

    with pytest.raises(ValueError):
        HTTPSchemaDownloader(schemas_resolver=DummySchemaResolver(), schemas_url=url)


@patch('requests.get', new=get_patched_valid_response)
def test_http_downloader_get_schema_spec(http_downloader):
    """
    Tests the HTTPSchemaDownloader with a real schema name
    """

    file_name = "real_schema.json"

    schema_spec = http_downloader.get_schema_spec(file_name)
    assert len(schema_spec) > 0


@patch('requests.get', new=get_patched_invalid_response)
def test_http_downloader_get_missing_schema(http_downloader):
    """
    Tests the HTTPSchemaDownloader with a missing schema name
    """

    file_name = "missing_schema.json"

    with pytest.raises(HTTPError):
        http_downloader.get_schema_spec(file_name)


def test_http_downloader_get_schema_type(http_downloader):
    """
    Tests the HTTPSchemaDownloader data type building
    """

    file_name = "custom.json"

    schema_type = http_downloader.get_schema_type(file_name)
    assert schema_type == "testing.com_test-project_1.0.0_custom"


def test_http_downloader_save_schema(http_downloader):
    """
    Tests the HTTPSchemaDownloader with an invalid initialization
    """

    schema_name = "dummy.json"
    schema_spec = {"key_1": "value_1", "key_2": "value_2"}

    http_downloader.save_locally(schema_name, schema_spec, overwrite=True)

    expected_folder = http_downloader.schemas_path
    expected_path = os.path.join(expected_folder, schema_name)

    assert os.path.isfile(expected_path)


def test_http_downloader_save_existing_schema(http_downloader):
    """
    Tests the HTTPSchemaDownloader with an invalid initialization
    """

    schema_name = "dummy.json"
    schema_spec_1 = {"key_1": "value_1", "key_2": "value_2"}
    schema_spec_2 = {"key_1": "new_value_1", "key_2": "new_value_2"}

    http_downloader.save_locally(schema_name, schema_spec_1, overwrite=True)
    http_downloader.save_locally(schema_name, schema_spec_2, overwrite=False)

    expected_folder = http_downloader.schemas_path
    expected_path = os.path.join(expected_folder, schema_name)

    with open(expected_path, 'r') as f:
        file_content = f.read()

    assert json.loads(file_content) == schema_spec_1


def test_http_downloader_invalid_schema_folder(http_downloader):
    """
    Tests the HTTPSchemaDownloader with an invalid folder
    """

    expected_folder = http_downloader.schemas_path

    # Create folder with restrictive permissions
    sh.rmtree(expected_folder)
    os.makedirs(expected_folder, mode=0o400)

    schema_name = "dummy.json"
    schema_spec = {"key_1": "value_1", "key_2": "value_2"}

    with pytest.raises(OSError):
        http_downloader.save_locally(schema_name, schema_spec, overwrite=True)

    sh.rmtree(expected_folder)
