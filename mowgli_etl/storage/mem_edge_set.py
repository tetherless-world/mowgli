from typing import Optional

from mowgli_etl.model.edge import Edge
from mowgli_etl.storage._edge_set import _EdgeSet


class MemEdgeSet(_EdgeSet):
    def __init__(self):
        _EdgeSet.__init__(self)
        self.__edges = {}

    def add(self, edge: Edge) -> None:
        key = self._construct_edge_key(object=edge.object, predicate=edge.predicate, subject=edge.subject)
        self.__edges[key] = edge

    def close(self):
        pass

    def get(self, *, object: str, predicate: str, subject: str, default: Optional[Edge] = None) -> Optional[Edge]:
        key = self._construct_edge_key(object=object, predicate=predicate, subject=subject)
        return self.__edges.get(key, default)

    @classmethod
    def temporary(cls):
        return cls()
