from abc import ABC, abstractmethod
from typing import Optional

from mowgli_etl._closeable import _Closeable
from mowgli_etl.model.edge import Edge


class _EdgeSet(_Closeable):
    """
    Abstract base class for edge set data structure implementations.
    """

    @abstractmethod
    def add(self, edge: Edge) -> None:
        """
        Add an edge to the set.
        """

    def _construct_edge_key(self, *, object: str, predicate: str, subject: str) -> str:
        return f"{subject}\t{predicate}\t{object}"

    def __contains__(self, edge: Edge) -> bool:
        return self.get(object=edge.object, predicate=edge.predicate, subject=edge.subject) is not None

    @abstractmethod
    def get(self, *, object: str, predicate: str, subject: str, default: Optional[Edge] = None) -> Optional[Edge]:
        """
        Get an edge by its "signature" parameters.
        :return: the edge if it's part of the set, otherwise None
        """

    @classmethod
    @abstractmethod
    def temporary(cls):
        """
        Factory method to create a temporary edge set.
        """
