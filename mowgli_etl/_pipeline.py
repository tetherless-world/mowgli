from abc import ABC
from typing import Optional, Union

from configargparse import ArgParser

from mowgli_etl._extractor import _Extractor
from mowgli_etl._loader import _Loader
from mowgli_etl._transformer import _Transformer
from mowgli_etl.loader.cskg_csv.cskg_csv_loader import CskgCsvLoader
from mowgli_etl.loader.rdf.quad_rdf_loader import QuadRdfLoader
from mowgli_etl.loader.rdf.triple_rdf_loader import TripleRdfLoader


class _Pipeline(ABC):
    def __init__(self, *, extractor: _Extractor, id: str, transformer: _Transformer, loader: Optional[Union[_Loader, str]] = None, single_datasource=True, **kwds):
        """
        Construct an extract-transform pipeline.
        :param extractor: extractor implementation
        :param id: unique identifier for this pipeline instance, may be adapted from arguments
        :param transformer: transformer implementation
        :param kwds: ignored
        """
        self.__extractor = extractor
        self.__id = id
        if not isinstance(loader, _Loader):
            loader = self.__create_loader(id=id, loader=loader, **kwds)
        self.__loader = loader
        self.__single_datasource = single_datasource
        self.__transformer = transformer

    @classmethod
    def add_arguments(cls, arg_parser: ArgParser) -> None:
        """
        Add pipeline-specific arguments. The parsed arguments are passed to the constructor as keywords.
        """
        cls.__add_loader_arguments(arg_parser)

    @classmethod
    def __add_loader_arguments(cls, arg_parser):
        arg_parser.add_argument("--loader", default="cskg_csv")

    def __create_loader(self, id: str, loader: Optional[str] = None, **loader_kwds) -> _Loader:
        if loader is None:
            loader = "cskg_csv"
        else:
            loader = loader.lower()

        if loader == "cskg_csv":
            return CskgCsvLoader()
        elif loader.startswith("quad_rdf_"):
            return QuadRdfLoader(format=loader[len("quad_rdf_"):], pipeline_id=id)
        elif loader.startswith("triple_rdf_"):
            return TripleRdfLoader(format=loader[len("triple_rdf_"):], pipeline_id=id)
        else:
            raise NotImplementedError(loader)

    @property
    def extractor(self) -> _Extractor:
        return self.__extractor

    @property
    def id(self) -> str:
        return self.__id

    @property
    def loader(self) -> _Loader:
        return self.__loader

    @property
    def single_datasource(self) -> bool:
        return self.__single_datasource

    @property
    def transformer(self) -> _Transformer:
        return self.__transformer
