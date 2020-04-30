from abc import ABC
from typing import Optional, Generator

from mowgli.lib.cskg.node import Node


class _NodeSet(ABC):
    def add(self, node: Node) -> None:
        """
        Add a node to the set.
        """

    def __contains__(self, node_id):
        return self.get(node_id) is not None

    def get(self, node_id: str, default: Optional[Node] = None) -> Optional[Node]:
        """
        Get a node by id from the set.
        :return: the node corresponding to the id if the former is in the set, otherwise None
        """

    def keys(self) -> Generator[str, None, None]:
        """
        Iterate over the node id's in the set as a generator.
        """
