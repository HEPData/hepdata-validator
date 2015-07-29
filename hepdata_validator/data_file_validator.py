import os
from hepdata.modules.hepdata_records.validator import Validator

__author__ = 'eamonnmaguire'

class DataFileValidator(Validator):

    """
    Validates the Data file YAML/JSON file
    """
    base_path = os.path.dirname(__file__)
    schema_file = base_path + '/schemas/data_schema.json'

