class ElementaError(Exception):
    """Base exception for Elementa-specific errors."""
    pass

class ParameterEvaluationError(ElementaError):
    """Raised when parameter evaluation fails (e.g., circular dependencies or invalid expressions)."""
    pass

class GeometryBuildError(ElementaError):
    """Raised when gmsh fails to build geometry or execute boolean operations."""
    pass

class SolverError(ElementaError):
    """Raised when the physics solver fails to compute a solution."""
    pass

class ProjectLoadError(ElementaError):
    """Raised when loading a project from a file fails."""
    pass

class ProjectSaveError(ElementaError):
    """Raised when saving a project to a file fails."""
    pass
