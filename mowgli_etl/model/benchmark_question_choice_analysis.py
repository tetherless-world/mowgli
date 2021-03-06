from typing import NamedTuple, Tuple

from mowgli_etl.model.benchmark_question_answer_paths import BenchmarkQuestionAnswerPaths


class BenchmarkQuestionChoiceAnalysis(NamedTuple):
    choice_id: str
    question_answer_paths: Tuple[BenchmarkQuestionAnswerPaths, ...]
