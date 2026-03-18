from .base import PhysicsState
from .registry import (
    PhysicsDescriptor,
    FeatureType,
    ResultField,
    DomainProperty,
    PHYSICS_REGISTRY,
    register_physics,
    get_physics,
    get_all_physics_names,
    get_compatible_study_types,
)

# Import physics modules so they auto-register their descriptors
from .electrostatics import ElectrostaticsDescriptor
from .heat_transfer import HeatTransferDescriptor

__all__ = [
    "PhysicsState",
    "PhysicsDescriptor",
    "FeatureType",
    "ResultField",
    "DomainProperty",
    "PHYSICS_REGISTRY",
    "register_physics",
    "get_physics",
    "get_all_physics_names",
    "get_compatible_study_types",
    "ElectrostaticsDescriptor",
    "HeatTransferDescriptor",
]

