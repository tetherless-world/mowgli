from mowgli_etl.loader._kg_edge_loader import _KgEdgeLoader
from mowgli_etl.loader._kg_node_loader import _KgNodeLoader
from mowgli_etl.loader.cskg_csv.cskg_csv_edge_loader import CskgCsvEdgeLoader
from mowgli_etl.loader.cskg_csv.cskg_csv_node_loader import CskgCsvNodeLoader
from mowgli_etl.model.kg_edge import KgEdge
from mowgli_etl.model.kg_node import KgNode


class CskgCsvLoader(_KgEdgeLoader, _KgNodeLoader):
    def __init__(self, *, bzip: bool = False):
        self.__edge_loader = CskgCsvEdgeLoader(bzip=bzip)
        self.__node_loader = CskgCsvNodeLoader(bzip=bzip)

    def open(self, storage):
        self.__edge_loader.open(storage)
        self.__node_loader.open(storage)
        return self

    def close(self):
        self.__edge_loader.close()
        self.__node_loader.close()

    def load_kg_edge(self, edge: KgEdge):
        self.__edge_loader.load_kg_edge(edge)

    def load_kg_node(self, node: KgNode):
        self.__node_loader.load_kg_node(node)
