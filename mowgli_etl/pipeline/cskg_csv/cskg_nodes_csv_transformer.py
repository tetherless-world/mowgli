import csv
from pathlib import Path
from typing import Union, TextIO, Generator

from mowgli_etl.model.kg_node import KgNode
from mowgli_etl.pipeline._csv_transformer import _CsvTransformer


class CskgNodesCsvTransformer(_CsvTransformer):
    def transform(self, *, nodes_csv_file: Union[Path, TextIO]) -> Generator[KgNode, None, None]:
        if isinstance(nodes_csv_file, Path):
            nodes_csv_file_path = nodes_csv_file
            with open(nodes_csv_file_path) as nodes_csv_file:
                yield from self.__transform(nodes_csv_file=nodes_csv_file)
        else:
            yield from self.__transform(nodes_csv_file=nodes_csv_file)

    def __transform(self, *, nodes_csv_file: TextIO) -> Generator[KgNode, None, None]:
        csv_reader = csv.DictReader(nodes_csv_file, delimiter="\t", quoting=csv.QUOTE_NONE)
        for csv_row_i, csv_row in enumerate(csv_reader):
            try:
                yield \
                    KgNode.legacy(
                        aliases=self._get_optional_column(csv_row, "aliases"),
                        datasource=self._get_required_column(csv_row, "datasource"),
                        id=self._get_required_column(csv_row, "id"),
                        label=self._get_optional_column(csv_row, "label"),
                        other=self._get_optional_column(csv_row, "other"),
                        pos=self._get_optional_column(csv_row, "pos"),
                    )
            except ValueError as e:
                self._logger.warning("CSKG nodes CSV row %d %s: %s", csv_row_i, e, csv_row)
