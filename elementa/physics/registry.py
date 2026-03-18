"""
Physics Plugin Registry
=======================
Provides the contracts (PhysicsDescriptor, FeatureType, ResultField)
and global PHYSICS_REGISTRY that every physics module registers into.

To add a new physics module:
  1. Create a new file (e.g. heat_transfer.py)
  2. Define a PhysicsDescriptor subclass with metadata + assemble_and_solve()
  3. Call register_physics(YourDescriptor) at module level
  4. Import it in physics/__init__.py
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Type

from .base import PhysicsState


@dataclass
class FeatureType:
    """Describes a feature that can be added under a physics node (e.g. Charge Density)."""
    kind: str               # Internal key, e.g. "charge_density"
    label: str              # Display name, e.g. "Charge Density"
    icon: str               # Icon filename, e.g. "electrostatics.png"
    default_props: Dict[str, str] = field(default_factory=lambda: {"value": "0.0"})
    default_domains: List[str] = field(default_factory=lambda: ["All"])
    prop_labels: Dict[str, str] = field(default_factory=dict)  # e.g. {"value": "Charge Density (ρ) [C/m³]"}


@dataclass
class ResultField:
    """Describes a result quantity produced by a physics solver."""
    key: str                # Result dict key, e.g. "phi"
    label: str              # Combo-box label, e.g. "V (Potential)"
    field_type: str         # "scalar" or "vector"
    unit: str               # Display unit, e.g. "V" or "V/m"


@dataclass
class DomainProperty:
    """A material/domain property required by a physics module."""
    key: str                # Material dict key, e.g. "relative_permittivity"
    label: str              # Display label, e.g. "Relative Permittivity (ε_r)"
    default: str            # Default string value, e.g. "1.0"
    unit: str = ""          # Display unit, e.g. "F/m"


@dataclass
class BoundaryConditionType:
    """Describes a boundary condition type for a physics module."""
    kind: str               # Internal key, e.g. "temperature"
    label: str              # Display name, e.g. "Temperature"
    default_props: Dict[str, str] = field(default_factory=dict)
    prop_labels: Dict[str, str] = field(default_factory=dict)


class PhysicsDescriptor:
    """
    Base class for physics plugin descriptors.

    Subclass this, fill in the class attributes, and implement
    assemble_and_solve(). Then call register_physics(YourDescriptor).
    """

    # ---- Metadata (override in subclasses) ----
    name: str = "BasePhysics"
    abbreviation: str = "bp"
    icon: str = "physics.png"
    bc_label: str = "Value"

    # ---- Supported study types ----
    supported_study_types: List[str] = ["Stationary"]

    # ---- Domain properties needed from materials ----
    domain_properties: List[DomainProperty] = []

    # ---- Feature types that can be added under this physics ----
    feature_types: List[FeatureType] = []

    # ---- Boundary condition types ----
    bc_types: List[BoundaryConditionType] = []

    # ---- Result fields produced by the solver ----
    result_fields: List[ResultField] = []

    # ---- Default physics_config values ----
    default_config: Dict[str, Any] = {}

    @classmethod
    def assemble_and_solve(cls, state: PhysicsState) -> PhysicsState:
        """Assemble matrices and solve.  Must populate state.results and state.basis."""
        raise NotImplementedError(f"{cls.name} has not implemented assemble_and_solve")

    @classmethod
    def create_panel(cls, project, owner):
        """
        Optional: return a custom QWidget for the physics settings panel.
        If None is returned, the generic panel will be used.
        """
        return None


# ---------------------------------------------------------------------------
# Global registry
# ---------------------------------------------------------------------------
PHYSICS_REGISTRY: Dict[str, PhysicsDescriptor] = {}


def register_physics(descriptor_cls: Type[PhysicsDescriptor]) -> None:
    """Register a physics descriptor class by its name."""
    PHYSICS_REGISTRY[descriptor_cls.name] = descriptor_cls


def get_physics(name: str) -> Optional[Type[PhysicsDescriptor]]:
    """Look up a registered physics descriptor by name."""
    return PHYSICS_REGISTRY.get(name)


def get_all_physics_names() -> List[str]:
    """Return a list of all registered physics names."""
    return list(PHYSICS_REGISTRY.keys())


def get_compatible_study_types(physics_names: List[str]) -> List[str]:
    """Return the intersection of supported study types for the given physics."""
    if not physics_names:
        return ["Stationary", "Time Dependent"]
    sets = []
    for name in physics_names:
        desc = PHYSICS_REGISTRY.get(name)
        if desc:
            sets.append(set(desc.supported_study_types))
    if not sets:
        return ["Stationary"]
    result = sets[0]
    for s in sets[1:]:
        result = result & s
    # Maintain a stable order
    ordered = []
    for st in ["Stationary", "Time Dependent"]:
        if st in result:
            ordered.append(st)
    return ordered
