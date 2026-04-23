"""Shared test fixtures."""
from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixtures_dir():
    return FIXTURES_DIR


@pytest.fixture
def sample_csv_content():
    return "name,age,city\nAlice,30,New York\nBob,25,London\nCharlie,35,Paris\n"


@pytest.fixture
def sample_json_content():
    return '[{"name":"Alice","age":30,"city":"New York"},{"name":"Bob","age":25,"city":"London"}]'


@pytest.fixture
def sample_yaml_content():
    return "---\n- name: Alice\n  age: 30\n  city: New York\n- name: Bob\n  age: 25\n  city: London\n"


@pytest.fixture
def sample_tsv_content():
    return "name\tage\tcity\nAlice\t30\tNew York\nBob\t25\tLondon\n"


@pytest.fixture
def sample_xml_content():
    return '<?xml version="1.0"?>\n<data>\n  <row><name>Alice</name><age>30</age><city>New York</city></row>\n  <row><name>Bob</name><age>25</age><city>London</city></row>\n</data>\n'
