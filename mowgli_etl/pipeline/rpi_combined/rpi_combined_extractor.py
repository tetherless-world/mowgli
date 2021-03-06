import multiprocessing
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Dict, Tuple

from mowgli_etl._extractor import _Extractor
from mowgli_etl._mapper import _Mapper
from mowgli_etl._pipeline import _Pipeline
from mowgli_etl.mapper.mappers import Mappers
from mowgli_etl.pipeline_storage import PipelineStorage
from mowgli_etl.pipeline_wrapper import PipelineWrapper


def parallel_worker(force: bool, pipeline: _Pipeline, root_data_dir_path: Path) -> Tuple[Path, Path]:
    # plyvel is not multiprocessing-safe, so create a temporary directory for the ConceptNet index.
    with TemporaryDirectory() as concept_net_index_directory_path:
        with Mappers(concept_net_index_directory_path=Path(concept_net_index_directory_path)) as mappers:
            return serial_worker(force, pipeline, mappers, root_data_dir_path)


def serial_worker(force: bool, pipeline: _Pipeline, mappers: Tuple[_Mapper, ...], root_data_dir_path: Path) -> Tuple[
    Path, Path]:
    storage = PipelineStorage(pipeline_id=pipeline.id, root_data_dir_path=root_data_dir_path)
    pipeline_wrapper = PipelineWrapper(pipeline, storage)

    pipeline_wrapper.run(force=force, mappers=mappers)

    edges_csv_file_path = storage.loaded_data_dir_path / 'edges.csv'
    nodes_csv_file_path = storage.loaded_data_dir_path / 'nodes.csv'

    return edges_csv_file_path, nodes_csv_file_path


class RpiCombinedExtractor(_Extractor):
    """
    Extracts the CSKG formatted result of one or more pipelines
    """

    def __init__(self, *, pipelines: Tuple[_Pipeline, ...], parallel=False):
        super().__init__()
        self.__parallel = parallel
        self.__pipelines = pipelines

    def extract(self, *, force: bool = False, storage: PipelineStorage) -> Dict[str, Tuple[Path, ...]]:
        self._logger.info("Starting combined extraction")
        nodes_csv_file_paths, edges_csv_file_paths = [], []

        if self.__parallel:
            with multiprocessing.Pool() as multiprocessing_pool:
                for edges_csv_file_path, nodes_csv_file_path in \
                        multiprocessing_pool.starmap(parallel_worker,
                                                     tuple((force, pipeline, storage.root_data_dir_path) for pipeline in
                                                           self.__pipelines)):
                    edges_csv_file_paths.append(edges_csv_file_path)
                    nodes_csv_file_paths.append(nodes_csv_file_path)
        else:
            with Mappers() as mappers:
                for pipeline in self.__pipelines:
                    edges_csv_file_path, nodes_csv_file_path = serial_worker(force, pipeline, mappers,
                                                                             storage.root_data_dir_path)
                    edges_csv_file_paths.append(edges_csv_file_path)
                    nodes_csv_file_paths.append(nodes_csv_file_path)
        self._logger.info("Finished combined extraction")
        return {
            'nodes_csv_file_paths': tuple(nodes_csv_file_paths),
            'edges_csv_file_paths': tuple(edges_csv_file_paths)
        }
