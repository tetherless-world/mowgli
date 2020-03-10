from typing import Generator, Union, Dict

from mowgli.lib.cskg.edge import Edge
from mowgli.lib.cskg.node import Node
from mowgli.lib.etl._pipeline import _Pipeline
from mowgli.lib.etl.pipeline_storage import PipelineStorage


class PipelineWrapper:
    def __init__(self, pipeline: _Pipeline, storage: PipelineStorage):
        self.__pipeline = pipeline
        self.__storage = storage

    def extract(self, force: bool = False) -> Dict[str, object]:
        extract_kwds = self.__pipeline.extractor.extract(force=force, storage=self.__storage)
        return extract_kwds if extract_kwds is not None else {}

    def extract_transform_load(self, force: bool = False):
        extract_kwds = self.extract(force=force)
        graph_generator = self.transform(force=force, **extract_kwds)
        self.load(graph_generator)

    @property
    def id(self) -> str:
        return self.__pipeline.id

    def load(self, graph_generator: Generator[Union[Node, Edge], None, None]) -> None:
        with self.__pipeline.loader.open(storage=self.__storage) as loader:
            for node_or_edge in graph_generator:
                if isinstance(node_or_edge, Node):
                    loader.load_node(node_or_edge)
                elif isinstance(node_or_edge, Edge):
                    loader.load_edge(node_or_edge)
                else:
                    raise ValueError(type(node_or_edge))

    def transform(self, force: bool = False, **extract_kwds) -> Generator[Union[Edge, Node], None, None]:
        edges = {}
        nodes = {}

        for node_or_edge in self.__pipeline.transformer.transform(**extract_kwds):
            if isinstance(node_or_edge, Node):
                node = node_or_edge
                existing_node = nodes.get(node.id)
                if existing_node is not None and existing_node != node:
                    raise ValueError("nodes with same id, different contents: " + node)
            elif isinstance(node_or_edge, Edge):
                edge = node_or_edge
                subject_edges = edges.setdefault(edge.subject, {})
                predicate_edges = subject_edges.setdefault(edge.predicate, {})
                object_edge = predicate_edges.get(edge.object)
                if object_edge is not None:
                    raise ValueError("duplicate edge: " + edge)
                predicate_edges[edge.object] = edge
            yield node_or_edge
