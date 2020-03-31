import importlib.util
import os.path
import re
from inspect import isclass
from types import FunctionType
from typing import Type, Tuple, Optional

from configargparse import ArgParser

from mowgli import paths
from mowgli.cli.commands._command import _Command
from mowgli.lib.etl._pipeline import _Pipeline
from mowgli.lib.etl.pipeline_storage import PipelineStorage
from mowgli.lib.etl.pipeline_wrapper import PipelineWrapper


class EtlCommand(_Command):
    def __init__(self):
        super().__init__()
        self.__pipeline_class_dict = self.__import_pipeline_classes()

    def add_arguments(self, arg_parser: ArgParser, add_parent_args: FunctionType):
        self.__add_general_etl_args(arg_parser)
        subparsers = arg_parser.add_subparsers(
            title="pipeline modules",
            help="module name for the pipeline implementation",
            dest="pipeline_module",
            required=True
        )
        for pipeline_name, pipeline_class in self.__pipeline_class_dict.items():
            subparser = subparsers.add_parser(pipeline_name)
            add_parent_args(subparser)
            self.__add_general_etl_args(subparser)
            pipeline_class.add_arguments(subparser)

    def __add_general_etl_args(self, arg_parser):
        arg_parser.add_argument(
            "--data-dir-path",
            help="path to a directory to store extracted and transformed data",
        )
        arg_parser.add_argument(
            "-f",
            "--force",
            action="store_true",
            help="force extract and transform, ignoring any cached data",
        )
        arg_parser.add_argument(
            "--force-extract",
            action="store_true",
            help="force extract, ignoring any cached data",
        )
        arg_parser.add_argument(
            "--force-transform",
            action="store_true",
            help="force transform, ignoring any cached data",
        )
        arg_parser.add_argument(
            "--fuseki-data-url", default="http://fuseki:3030/ds/data"
        )

    def __call__(self, args):
        pipeline_class = self.__pipeline_class_dict[args.pipeline_module]

        pipeline = self.__instantiate_pipeline(args, pipeline_class)
        pipeline_storage = PipelineStorage(
            pipeline_id=pipeline.id,
            root_data_dir_path=self.__create_data_dir_path(args),
        )
        pipeline_wrapper = PipelineWrapper(pipeline=pipeline, storage=pipeline_storage)

        force = bool(getattr(args, "force", False))
        force_extract = force or bool(getattr(args, "force_extract", False))
        force_transform = force or bool(getattr(args, "force_transform", False))

        extract_kwds = pipeline_wrapper.extract(force=force_extract)
        graph_generator = pipeline_wrapper.transform(
            force=force_transform, **extract_kwds
        )
        pipeline_wrapper.load(graph_generator)

    def __create_data_dir_path(self, args) -> str:
        data_dir_path = args.data_dir_path
        if data_dir_path is None:
            for data_dir_path in (
                # In the container
                "/data",
                # In the checkout
                paths.DATA_DIR,
            ):
                if os.path.isdir(data_dir_path):
                    break
        if not os.path.isdir(data_dir_path):
            raise ValueError("data dir path %s does not exist" % data_dir_path)
        if not os.path.isdir(data_dir_path):
            os.makedirs(data_dir_path)
            self._logger.info("created pipeline data directory %s", data_dir_path)
        return data_dir_path

    def __import_pipeline_class_from_file(
        self, file_path
    ) -> Optional[Tuple[str, Type[_Pipeline]]]:
        module_name = re.sub(r"\.py$", "", file_path.name)
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        pipeline_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(pipeline_module)
        for attr in dir(pipeline_module):
            value = getattr(pipeline_module, attr)
            if (
                isclass(value)
                and issubclass(value, _Pipeline)
                and value is not _Pipeline
            ):
                pipeline_name = re.sub(r"_pipeline\.py$", "", file_path.name)
                return pipeline_name, value

    def __import_pipeline_classes(self):
        pipeline_class_dict = {}
        etl_dir = paths.SRC_ROOT / "lib" / "etl"
        assert etl_dir.is_dir()
        for pipeline_dir in etl_dir.iterdir():
            if not pipeline_dir.is_dir():
                continue
            for pipeline_file_path in pipeline_dir.glob("*_pipeline.py"):
                pipeline_tuple = self.__import_pipeline_class_from_file(
                    pipeline_file_path
                )
                if pipeline_tuple is not None:
                    pipeline_name, pipeline_class = pipeline_tuple
                    pipeline_class_dict[pipeline_name] = pipeline_class
                else:
                    self._logger.warn(
                        f"No pipeline class found in file {pipeline_file_path}"
                    )
        return pipeline_class_dict

    def __instantiate_pipeline(self, args, pipeline_class, **kwds) -> _Pipeline:
        pipeline_kwds = vars(args).copy()
        pipeline_kwds.pop("c")
        pipeline_kwds.pop("data_dir_path")
        pipeline_kwds.pop("force")
        pipeline_kwds.pop("force_extract")
        pipeline_kwds.pop("force_transform")
        pipeline_kwds.pop("logging_level")
        pipeline_kwds.pop("pipeline_module")
        pipeline_kwds.update(kwds)
        return pipeline_class(**pipeline_kwds)