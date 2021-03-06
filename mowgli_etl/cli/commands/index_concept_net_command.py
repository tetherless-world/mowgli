from configargparse import ArgParser

from mowgli_etl.cli.commands._command import _Command
from mowgli_etl.mapper.concept_net.concept_net_index import ConceptNetIndex


class IndexConceptNetCommand(_Command):
    """
    Command line utility to pre-index ConceptNet from a CSKG release.
    """

    def add_arguments(self, arg_parser: ArgParser, add_parent_arguments):
        pass

    def __call__(self, args):
        ConceptNetIndex.create(report_progress=True)
