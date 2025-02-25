
# Para rodar os testes: 
# /tests/unit> python3 -m pytest -s -v

import pytest
from src.main import parse_json_response  


@pytest.mark.unit
def test_parse_json_response():
    json_response = {"value": "22"}
    result = parse_json_response(json_response, "value")
    assert result == "22"

