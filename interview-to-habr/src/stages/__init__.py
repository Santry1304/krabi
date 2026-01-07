"""Pipeline stages module."""

from .base import BaseStage, StageResult
from .s01_load import LoadStage
from .s02_format import FormatStage
from .s03_compare import CompareStage
from .s04_plan import PlanStage
from .s05_write import WriteStage
from .s06_merge import MergeStage
from .s07_edit import EditStage
from .s08_analyze import AnalyzeStage
from .s09_select import SelectStage, MATERIAL_TYPES
from .s10_generate import GenerateStage

# Stage registry
STAGES = {
    1: LoadStage,
    2: FormatStage,
    3: CompareStage,
    4: PlanStage,
    5: WriteStage,
    6: MergeStage,
    7: EditStage,
    8: AnalyzeStage,
    9: SelectStage,
    10: GenerateStage,
}


def create_stage(stage_num: int, **kwargs) -> BaseStage:
    """
    Factory for creating stages.

    Args:
        stage_num: Stage number (1-10)
        **kwargs: Stage-specific arguments

    Returns:
        Stage instance

    Raises:
        ValueError: If stage number invalid
    """
    if stage_num not in STAGES:
        raise ValueError(f"Invalid stage number: {stage_num}. Must be 1-10.")

    return STAGES[stage_num](**kwargs)


__all__ = [
    'BaseStage',
    'StageResult',
    'LoadStage',
    'FormatStage',
    'CompareStage',
    'PlanStage',
    'WriteStage',
    'MergeStage',
    'EditStage',
    'AnalyzeStage',
    'SelectStage',
    'GenerateStage',
    'MATERIAL_TYPES',
    'STAGES',
    'create_stage',
]
