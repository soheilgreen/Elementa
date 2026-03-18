"""Core data structures, state management, and utilities for Elementa."""

from .exceptions import (
    ElementaError,
    ParameterEvaluationError,
    GeometryBuildError,
    SolverError,
    ProjectLoadError,
    ProjectSaveError,
)
from .logger import get_logger
from .project_state import (
    ProjectState,
    ProjectSettings,
    GeometryItem,
    BooleanOperationItem,
    Material,
    PhysicsFeature,
    BoundaryConditionItem,
)
from .material_library import MATERIAL_LIBRARY, get_library_material_names, get_material_properties
from .evaluator import ParameterEvaluator