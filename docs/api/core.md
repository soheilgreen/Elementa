# elementa.core — API Reference

## Exceptions

### `ElementaError`
Base class for all Elementa-specific exceptions. Inherits from `Exception`.

### `ParameterEvaluationError(ElementaError)`
Raised when a symbolic parameter expression cannot be evaluated (invalid syntax, circular dependency, unknown name).

### `GeometryBuildError(ElementaError)`
Raised when gmsh fails to build a primitive or execute a boolean operation.

### `SolverError(ElementaError)`
Raised when a physics solver fails to produce a solution.

### `ProjectLoadError(ElementaError)`
Raised when loading a project from a `.elem` file fails.

### `ProjectSaveError(ElementaError)`
Raised when saving a project to a `.elem` file fails.

---

## Data Classes

### `ProjectSettings`

```python
@dataclass
class ProjectSettings:
    name: str = "Component1"
    space_dim: int = 2
    description: str = ""
```

### `GeometryItem`

```python
@dataclass
class GeometryItem:
    kind: str           # e.g. "rectangle", "disk"
    name: str           # user-assigned name
    params: Dict[str, str]  # parameter expressions keyed by param name
```

### `BooleanOperationItem`

```python
@dataclass
class BooleanOperationItem:
    kind: str           # "union", "difference", "intersection"
    name: str
    inputs: List[str]   # names of input GeometryItems
```

### `Material`

```python
@dataclass
class Material:
    name: str
    properties: Dict[str, Any]  # e.g. {"thermal_conductivity": "200.0"}
    domains: List[str]          # e.g. ["All"] or ["inner", "outer"]
```

### `BoundaryConditionItem`

```python
@dataclass
class BoundaryConditionItem:
    name: str
    kind: str                       # e.g. "temperature", "ground"
    properties: Dict[str, str]      # e.g. {"value": "293.15"}
    boundaries: List[str]           # physical group names
```

---

## `ProjectState`

Central application state object. Inherits from `QObject`.

**Signals:**

| Signal | Type | Description |
|--------|------|-------------|
| `state_changed` | `pyqtSignal()` | Any general change |
| `geometry_changed` | `pyqtSignal()` | Geometry items updated |
| `mesh_changed` | `pyqtSignal()` | Mesh generated or loaded |
| `results_changed` | `pyqtSignal()` | Results updated |
| `selection_changed` | `pyqtSignal(set)` | Boundary/domain selection |

**Key methods:**

```python
def reset() -> None
def save_project(path: str) -> bool
def load_project(path: str) -> bool
def add_geometry_item(item: GeometryItem) -> None
def remove_geometry_item(name: str) -> None
def add_boundary_condition(bc: BoundaryConditionItem) -> None
def set_results(basis, results_dict: Dict[str, Any]) -> None
```

---

## `ParameterEvaluator`

```python
class ParameterEvaluator:
    @staticmethod
    def resolve_parameters(raw: Dict[str, str]) -> Dict[str, float]:
        """Resolve all symbolic parameters, handling inter-dependencies."""

    @staticmethod
    def evaluate_expression(expr: str, params: Dict[str, float]) -> float:
        """Evaluate a single expression string."""

    @staticmethod
    def evaluate_points(expr: str, params: Dict[str, float]) -> List[Tuple[float, float]]:
        """Evaluate a polygon points expression string."""
```

---

## `CADBuilder`

```python
class CADBuilder:
    @staticmethod
    def build_model(project: ProjectState) -> ElementaCAD:
        """Build the full CAD model from project state. Raises GeometryBuildError."""
```

---

## Material Library

```python
MATERIAL_LIBRARY: Dict[str, Dict[str, Any]]

def get_library_material_names() -> List[str]
def get_material_properties(name: str) -> Dict[str, Any]
```

---

## Logger

```python
def get_logger(name: str) -> logging.Logger
```

Returns a configured `logging.Logger` with a `StreamHandler` at `INFO` level.
