from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Callable

@dataclass
class PhysicsState:
    """Generic state object passed to any physics solver.

    Physics-specific data (e.g. charge densities, heat sources) is
    communicated through :attr:`physics_features` and :attr:`physics_config`.
    Solvers should read feature values from those collections rather than
    expecting dedicated fields here.
    """
    mesh: Optional[Any] = None
    basis: Optional[Any] = None
    bc_items: List[Any] = field(default_factory=list)
    physics_config: Dict[str, Any] = field(default_factory=dict)
    materials: List[Any] = field(default_factory=list)
    physics_features: List[Any] = field(default_factory=list)
    results: Dict[str, Any] = field(default_factory=dict)
    study_type: str = "Stationary"
    time_config: Dict[str, float] = field(default_factory=lambda: {"t_start": 0.0, "t_end": 1.0, "dt": 0.1})
    progress_callback: Optional[Callable[[int], None]] = None
    abort_check: Optional[Callable[[], bool]] = None
