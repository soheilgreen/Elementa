# elementa.physics — API Reference

## `PhysicsState`

Data container passed to every physics solver.

```python
@dataclass
class PhysicsState:
    mesh: Optional[Any] = None
    basis: Optional[Any] = None
    bc_items: List[Any] = field(default_factory=list)
    physics_config: Dict[str, Any] = field(default_factory=dict)
    materials: List[Any] = field(default_factory=list)
    physics_features: List[Any] = field(default_factory=list)
    results: Dict[str, Any] = field(default_factory=dict)
    study_type: str = "Stationary"
    time_config: Dict[str, float] = field(...)
    progress_callback: Optional[Callable[[int], None]] = None
    abort_check: Optional[Callable[[], bool]] = None
```

Solvers read `mesh`, `bc_items`, `physics_config`, `materials`, and `physics_features`. They write `basis` and `results` before returning.

---

## Descriptor Classes

### `PhysicsDescriptor`

Base class for all physics plugin descriptors.

```python
class PhysicsDescriptor:
    name: str                              # Registry key
    abbreviation: str                      # Short label
    icon: str                              # Icon filename
    bc_label: str                          # Primary BC display label
    supported_study_types: List[str]
    domain_properties: List[DomainProperty]
    feature_types: List[FeatureType]
    bc_types: List[BoundaryConditionType]
    result_fields: List[ResultField]
    default_config: Dict[str, Any]

    @classmethod
    def assemble_and_solve(cls, state: PhysicsState) -> PhysicsState: ...
```

### `FeatureType`

```python
@dataclass
class FeatureType:
    kind: str
    label: str
    icon: str
    default_props: Dict[str, str]
    default_domains: List[str]
    prop_labels: Dict[str, str]
```

### `ResultField`

```python
@dataclass
class ResultField:
    key: str         # Key in results dict
    label: str       # Display label
    field_type: str  # "scalar" or "vector"
    unit: str
```

### `DomainProperty`

```python
@dataclass
class DomainProperty:
    key: str
    label: str
    default: str
    unit: str = ""
```

### `BoundaryConditionType`

```python
@dataclass
class BoundaryConditionType:
    kind: str
    label: str
    default_props: Dict[str, str]
    prop_labels: Dict[str, str]
```

---

## Registry Functions

```python
def register_physics(descriptor_cls: Type[PhysicsDescriptor]) -> None:
    """Register a descriptor class by its name."""

def get_physics(name: str) -> Optional[Type[PhysicsDescriptor]]:
    """Look up a descriptor by name."""

def get_all_physics_names() -> List[str]:
    """List all registered physics names."""

def get_compatible_study_types(physics_names: List[str]) -> List[str]:
    """Return intersection of supported study types for the given modules."""
```

---

## Built-in Descriptors

### `ElectrostaticsDescriptor`

Solves $-\nabla \cdot (\varepsilon_0 \varepsilon_r \nabla \varphi) = \rho$.

- **Result keys:** `phi` (scalar, V), `E` (vector tuple, V/m)
- **Study types:** Stationary

### `HeatTransferDescriptor`

Solves $\rho C_p \partial_t T - \nabla \cdot (k \nabla T) = Q$.

- **Result keys:** `T` (scalar or list of arrays, K), `q` (vector tuple or list, W/m²), `times` (list of floats, Time Dependent only)
- **Study types:** Stationary, Time Dependent
- **Time integration:** Backward Euler
