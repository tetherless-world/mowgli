import logging
from typing import Generator, Union, Dict, Optional, Tuple

from mowgli_etl.model.kg_edge import KgEdge
from mowgli_etl.model.model import Model
from mowgli_etl.model.kg_node import KgNode
from mowgli_etl._mapper import _Mapper
from mowgli_etl._pipeline import _Pipeline
from mowgli_etl.model.kg_path import KgPath
from mowgli_etl.pipeline_storage import PipelineStorage
from mowgli_etl.storage._kg_edge_set import _KgEdgeSet
from mowgli_etl.storage._id_set import _IdSet
from mowgli_etl.storage._kg_node_set import _KgNodeSet
import stringcase

try:
    from mowgli_etl.storage.persistent_kg_edge_set import PersistentKgEdgeSet as EdgeSet
    from mowgli_etl.storage.persistent_id_set import PersistentIdSet as NodeIdSet
    from mowgli_etl.storage.persistent_kg_node_set import PersistentKgNodeSet as NodeSet
except ImportError:
    from mowgli_etl.storage.mem_kg_edge_set import MemKgEdgeSet as EdgeSet
    from mowgli_etl.storage.mem_id_set import MemIdSet as NodeIdSet
    from mowgli_etl.storage.mem_kg_node_set import MemKgNodeSet as NodeSet


class PipelineWrapper:
    def __init__(self, pipeline: _Pipeline, storage: PipelineStorage):
        self._logger = logging.getLogger(self.__class__.__name__)
        self.__pipeline = pipeline
        self.__storage = storage

    def extract(self, force: bool = False) -> Dict[str, object]:
        extract_kwds = self.__pipeline.extractor.extract(
            force=force, storage=self.__storage
        )
        return extract_kwds if extract_kwds is not None else {}

    @property
    def id(self) -> str:
        return self.__pipeline.id

    def map(
        self,
        model_generator: Generator[Model, None, None],
        mappers: Tuple[_Mapper, ...],
    ) -> Generator[Model, None, None]:
        for model in model_generator:
            yield model
            if isinstance(model, KgNode):
                node = model
                for mapper in mappers:
                    yield from mapper.map(node)

    def load(self, model_generator: Generator[Model, None, None]) -> None:
        load_method_cache = {}
        with self.__pipeline.loader.open(storage=self.__storage) as loader:
            for model in model_generator:
                try:
                    load_method = load_method_cache[model.__class__.__name__]
                except KeyError:
                    load_method_name = "load_" + stringcase.snakecase(
                        model.__class__.__name__
                    )
                    load_method = getattr(loader, load_method_name)
                    load_method_cache[model.__class__.__name__] = load_method

                load_method(model)

    def run(
        self,
        *,
        force: bool = False,
        mappers: Tuple[_Mapper, ...] = (),
        skip_whole_graph_check: Optional[bool] = False,
    ):
        """
        Run the entire pipeline.
        """
        extract_kwds = self.extract(force=force)
        model_generator = self.transform(
            force=force, skip_whole_graph_check=skip_whole_graph_check, **extract_kwds
        )
        if mappers:
            model_generator = self.map(model_generator, mappers)
        self.load(model_generator)

    def transform(
        self,
        force: bool = False,
        skip_whole_graph_check: Optional[bool] = False,
        **extract_kwds,
    ) -> Generator[Model, None, None]:
        transform_generator = self.__pipeline.transformer.transform(**extract_kwds)

        if skip_whole_graph_check:
            self._logger.info("skipping whole graph checking during transform")
            yield from transform_generator
            return

        with EdgeSet.temporary() as edge_set:
            with NodeSet.temporary() as node_set:
                with NodeIdSet.temporary() as used_node_ids_set:
                    yield from self.__transform(
                        edge_set=edge_set,
                        node_set=node_set,
                        transform_generator=transform_generator,
                        used_node_ids_set=used_node_ids_set,
                    )

    def __transform(
        self,
        *,
        edge_set: _KgEdgeSet,
        node_set: _KgNodeSet,
        transform_generator: Generator[Model, None, None],
        used_node_ids_set: _IdSet,
    ) -> Generator[Model, None, None]:
        for model in transform_generator:
            try:
                if self.__pipeline.single_source and model.source != self.__pipeline.id:
                    raise ValueError(
                        f"pipeline can only yield one datasource, the same as the pipeline id: expected={self.id}, actual={model.datasource}"
                    )
            except AttributeError:
                pass

            if isinstance(model, KgNode):
                node = model
                # KgNode ID's should be unique in the CSKG.
                existing_node = node_set.get(node.id)
                if existing_node is not None:
                    if existing_node == node:
                        # Common case: ignore exact duplicate nodes i.e., nodes that are the same in all fields.
                        # This happens frequently in the word association sources, where the same word can come
                        # up as a response to multiple cues.
                        continue
                    else:
                        # Throw an exception if two nodes have the same id but aren't the same in all of their fields
                        raise ValueError(
                            "nodes with same id, different contents: original=%s, duplicate=%s"
                            % (existing_node, node)
                        )
                else:
                    node_set.add(node)
            elif isinstance(model, KgEdge):
                edge = model
                # Edges should be unique in the CSKG, meaning that the tuple of (subject, predicate, object) should be unique.
                existing_edge = edge_set.get(edge.id)
                if existing_edge is not None:
                    # Don't try to handle the exact duplicate case differently. It should never happen.
                    raise ValueError(
                        "duplicate edge: original=%s, duplicate=%s"
                        % (existing_edge, edge)
                    )
                edge_set.add(edge)
                used_node_ids_set.add(edge.subject)
                used_node_ids_set.add(edge.object)
            yield model
        for node_id in node_set.keys():
            if node_id not in used_node_ids_set:
                raise ValueError("node %s not used by an edge" % node_id)
