import logging
from abc import ABC, abstractmethod

from mowgli.lib.cskg.edge import Edge
from mowgli.lib.cskg.node import Node
from mowgli.lib.etl._pipeline_storage import _PipelineStorage


class _Loader(ABC):
    def __init__(self):
        self._logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def close(self) -> None:
        """
        Close this loader.
        """

    def __enter__(self):
        return self

    def __exit__(self, *args, **kwds):
        self.close()

    @abstractmethod
    def open(self, storage: _PipelineStorage):
        """
        Open this loader before calling load_* methods.
        :param pipeline_storage:
        :return: self
        """
        return self

    @abstractmethod
    def load_edge(self, edge: Edge, pi):
        pass

    @abstractmethod
    def load_node(self, node: Node):
        pass
