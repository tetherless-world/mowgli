from pathlib import Path
from typing import Dict
from zipfile import ZipFile

import pytest

from mowgli_etl.model.concept_net_predicates import HAS_A
from mowgli_etl.model.kg_edge import KgEdge
from mowgli_etl.model.kg_node import KgNode
from tests.mowgli_etl_test.http_client.mock_etl_http_client import MockEtlHttpClient


@pytest.fixture
def part_whole_zip_url() -> str:
    return "https://example.com/webchild_partof.zip"


@pytest.fixture
def wordnet_sense_url() -> str:
    return "https://example.com/webchild_wordnet.txt"


@pytest.fixture
def part_whole_archive_filenames() -> Dict[str, str]:
    return {
        "memberof_filename": "test_web_child_partof_memberof.txt",
        "physical_filename": "test_web_child_partof_physical.txt",
        "substanceof_filename": "test_web_child_partof_substanceof.txt",
    }


@pytest.fixture
def part_whole_zip_path(tmp_path_factory, part_whole_archive_filenames) -> Path:
    webchild_test_dir = Path(__file__).parent
    zip_path = tmp_path_factory.mktemp("webchild-zip") / "webchild_partof.zip"
    zip_obj = ZipFile(zip_path, "w")
    for filename in part_whole_archive_filenames.values():
        zip_obj.write(webchild_test_dir / filename, arcname=filename)
    zip_obj.close()
    return zip_path


@pytest.fixture
def wordnet_sense_path() -> Path:
    return Path(__file__).parent / "test_WordNetWrapper.txt"


@pytest.fixture
def web_child_test_http_client(
    part_whole_zip_url, part_whole_zip_path, wordnet_sense_url, wordnet_sense_path
) -> MockEtlHttpClient:
    client = MockEtlHttpClient()
    client.add_file_mock_response(part_whole_zip_url, part_whole_zip_path)
    client.add_file_mock_response(wordnet_sense_url, wordnet_sense_path)
    return client

@pytest.fixture
def web_child_transform_args():
    filenames = {
        "memberof_csv_file_path": "test_web_child_partof_memberof.txt",
        "physical_csv_file_path": "test_web_child_partof_physical.txt",
        "substanceof_csv_file_path": "test_web_child_partof_substanceof.txt",
        "wordnet_csv_file_path": "test_WordNetWrapper.txt",
    }
    return {k: Path(__file__).parent / v for k, v in filenames.items()}

