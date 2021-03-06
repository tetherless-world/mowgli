import bz2
import logging
import os.path
import pickle
from io import TextIOWrapper
from pathlib import Path
from shutil import rmtree
from typing import Optional, Union, TextIO

import plyvel
from tqdm import tqdm

from mowgli_etl import paths
from mowgli_etl._closeable import _Closeable
from mowgli_etl.pipeline.cskg_csv.cskg_nodes_csv_transformer import CskgNodesCsvTransformer
from mowgli_etl.storage.level_db import LevelDb


class ConceptNetIndex(_Closeable):
    __DIRECTORY_PATH_DEFAULT = paths.DATA_DIR / "concept_net" / "indexed"
    __NODES_CSV_FILE_DEFAULT = paths.DATA_DIR / "concept_net" / "extracted" / "nodes.csv.bz2"

    def __init__(self, db: LevelDb):
        self.__db = db

    @classmethod
    def __build(cls, *, db: LevelDb, directory_path: Path, nodes_csv_file: TextIO, limit: Optional[int],
                report_progress: bool):
        logger = logging.getLogger(cls.__name__)
        logger.info("building ConceptNet index at %s", directory_path)
        nodes = CskgNodesCsvTransformer().transform(nodes_csv_file=nodes_csv_file)
        if report_progress:
            nodes = tqdm(nodes)
        for node_i, node in enumerate(nodes):
            if len(node.labels) != 1:
                raise AssertionError(f"node {node.id} has aliases")
            node_label = node.labels[0]
            if node_label.lower() != node_label:
                raise AssertionError(f"label is not lower-case: {node_label}")

            assert '/' not in node_label
            key = cls.__label_to_key(node_label)

            # Store the node ID(s) as the value
            # Other information, such as the part of speech, can be reconstructed from it.
            value = node.id

            existing_values = db.get(key)
            if existing_values is not None:
                existing_values = pickle.loads(existing_values)
                if isinstance(existing_values, str):
                    new_values = [existing_values, value]
                else:
                    assert isinstance(existing_values, list)
                    existing_values.append(value)
                    new_values = existing_values
            else:
                new_values = node.id

            db.put(node_label.encode("utf-8"), pickle.dumps(new_values))

            if limit is not None and node_i + 1 == limit:
                break
        db.compact_range()  # Compact the underlying storage
        logger.info("built ConceptNet index")

    def close(self):
        self.__db.close()

    @classmethod
    def create(
            cls,
            *,
            directory_path: Optional[Path] = __DIRECTORY_PATH_DEFAULT,
            limit: Optional[int] = None,
            nodes_csv_file: Union[Path, TextIO] = __NODES_CSV_FILE_DEFAULT,
            report_progress: bool = False
    ):
        if directory_path.exists():
            rmtree(directory_path)
        directory_path.mkdir(parents=True)
        db = LevelDb(directory_path=directory_path, create_if_missing=True, error_if_exists=True)

        build_kwds = {
            "db": db,
            "directory_path": directory_path,
            "limit": limit,
            "report_progress": report_progress
        }

        if isinstance(nodes_csv_file, TextIO):
            cls.__build(nodes_csv_file=nodes_csv_file, **build_kwds)
        elif isinstance(nodes_csv_file, Path):
            nodes_csv_file_path = nodes_csv_file
            nodes_csv_file_ext = os.path.splitext(nodes_csv_file_path.name)[-1].lower()
            if nodes_csv_file_ext == ".bz2":
                with bz2.BZ2File(nodes_csv_file_path) as nodes_csv_file:
                    cls.__build(nodes_csv_file=TextIOWrapper(nodes_csv_file), **build_kwds)
            else:
                with open(nodes_csv_file_path) as nodes_csv_file:
                    cls.__build(nodes_csv_file=nodes_csv_file, **build_kwds)
        else:
            raise ValueError(nodes_csv_file)

        return cls(db)

    @classmethod
    def open(cls, directory_path: Optional[Path] = __DIRECTORY_PATH_DEFAULT):
        try:
            return cls(LevelDb(directory_path=directory_path, create_if_missing=False))
        except plyvel.Error:
            raise FileNotFoundError

    def get(self, label: str, *, pos: Optional[str] = None) -> Optional[str]:
        """
        Get the ConceptNet node ID corresponding to a label and optional part of speech.
        """
        value = self.__db.get(self.__label_to_key(label))
        if value is None:
            return None
        node_id = pickle.loads(value)
        if isinstance(node_id, str):
            return node_id
        node_ids = node_id
        assert isinstance(node_ids, list)
        if pos is None:
            return node_ids[0]
        parsed_node_ids = []
        # Parse the node id's with the same label
        # If there's one that corresponds exactly with the requested qualifiers, return it.
        node_id_without_qualifiers = None
        for node_id in node_ids:
            node_id_split = node_id.split('/')
            assert len(node_id_split) >= 4
            unqualified_node_id, qualifiers = '/'.join(node_id_split[:4]), node_id_split[4:]
            if qualifiers:
                node_pos = qualifiers.pop(0)
                if node_pos == pos:
                    return node_id
            else:
                node_id_without_qualifiers = node_id
        # No node id corresponds exactly with the requested qualifiers, return a node id without qualifiers if we have one.
        return node_id_without_qualifiers

    @staticmethod
    def __label_to_key(label: str):
        return label.lower().encode("utf-8")
