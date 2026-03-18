import json
import os
import shutil
import tempfile
import zipfile
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Set

import numpy as np
from PyQt6.QtCore import QObject, pyqtSignal

from .logger import get_logger
from .exceptions import ProjectLoadError, ProjectSaveError

logger = get_logger(__name__)

# Re-using existing data classes or defining new ones if needed
@dataclass
class GeometryItem:
    kind: str
    name: str
    params: Dict[str, str]

@dataclass
class BooleanOperationItem:
    kind: str
    name: str
    inputs: List[str]

@dataclass
class Material:
    name: str
    properties: Dict[str, Any]
    domains: List[str] = field(default_factory=list)

@dataclass
class PhysicsFeature:
    kind: str
    name: str
    properties: Dict[str, str]
    domains: List[str] = field(default_factory=list)

@dataclass
class BoundaryConditionItem:
    name: str # e.g. "Temperature 1"
    kind: str # e.g. "temperature"
    properties: Dict[str, str] = field(default_factory=dict)
    boundaries: List[str] = field(default_factory=list)

@dataclass
class ProjectSettings:
    name: str = "Component1"
    space_dim: int = 2
    description: str = ""

class ProjectState(QObject):
    # Signals
    state_changed = pyqtSignal()  # General update
    selection_changed = pyqtSignal(set)
    geometry_changed = pyqtSignal()
    mesh_changed = pyqtSignal()
    results_changed = pyqtSignal()
    plots_changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.reset()

    def reset(self):
        """Resets the project to a default empty state."""
        self.settings = ProjectSettings()
        self.project_path: Optional[str] = None
        
        # Model definitions
        self.parameters: Dict[str, str] = {}
        self.geometry_items: List[GeometryItem] = []
        self.boolean_operations: List[BooleanOperationItem] = []
        
        # Physics and Study
        self.selected_physics: List[str] = ["Electrostatics"]
        self.selected_study: str = "Stationary"
        self.time_config: Dict[str, float] = {"t_start": 0.0, "t_end": 1.0, "dt": 0.1}
        self.param_sweep_config: Dict[str, Any] = {"enabled": False, "parameter": "", "start": 0.0, "end": 1.0, "step": 0.1}
        self.materials_list: List[Material] = [Material("Material 1", {"relative_permittivity": "1.0"}, ["All"])]
        self.physics_features: List[PhysicsFeature] = []
        self.bc_items: List[BoundaryConditionItem] = []
        
        # Physics active config — defaults populated from the physics registry
        self.physics_config: Dict[str, Any] = self._build_default_physics_config()

        # Transient / Computed state
        self.msh_path: Optional[str] = None
        self.mesh: Optional[Any] = None
        self.basis: Optional[Any] = None
        self.results: Dict[str, Any] = {} # Store phi, E, etc.
        self.plots: List[Dict[str, Any]] = [] # Store plot specifications
        self.probes: List[Dict[str, Any]] = [] # Store probe specifications
        self.selected_boundaries: Set[str] = set()
        self.selected_domains: Set[str] = set()
        self.active_panel_context: str = ""
        self.current_time_index: int = 0
        self.current_sweep_index: int = 0
        
        # Internal
        self._temp_dir = tempfile.mkdtemp(prefix="elementa_")

    def cleanup(self):
        if os.path.exists(self._temp_dir):
            shutil.rmtree(self._temp_dir)

    @property
    def space_dim(self) -> int:
        return self.settings.space_dim

    @space_dim.setter
    def space_dim(self, dim: int):
        self.settings.space_dim = dim
        self.state_changed.emit()

    @property
    def project_name(self) -> str:
        return self.settings.name

    @project_name.setter
    def project_name(self, name: str):
        self.settings.name = name
        self.state_changed.emit()

    def add_geometry_item(self, item: GeometryItem):
        self.geometry_items.append(item)
        self.geometry_changed.emit()

    def remove_geometry_item(self, name: str):
        self.geometry_items = [g for g in self.geometry_items if g.name != name]
        self.boolean_operations = [b for b in self.boolean_operations if b.name != name]
        self.geometry_changed.emit()

    def add_boolean_operation(self, item: BooleanOperationItem):
        self.boolean_operations.append(item)
        self.geometry_changed.emit()

    def set_mesh(self, mesh):
        self.mesh = mesh
        self.mesh_changed.emit()

    def add_material(self, mat: Material):
        self.materials_list.append(mat)
        self.state_changed.emit()

    def remove_material(self, name: str):
        self.materials_list = [m for m in self.materials_list if m.name != name]
        self.state_changed.emit()

    def add_physics_feature(self, feature: PhysicsFeature):
        self.physics_features.append(feature)
        self.state_changed.emit()

    def remove_physics_feature(self, name: str):
        self.physics_features = [f for f in self.physics_features if f.name != name]
        self.state_changed.emit()

    def add_boundary_condition(self, bc: BoundaryConditionItem):
        self.bc_items.append(bc)
        self.state_changed.emit()

    def remove_boundary_condition(self, name: str):
        self.bc_items = [bc for bc in self.bc_items if bc.name != name]
        self.state_changed.emit()

    def set_results(self, basis, results_dict: Dict[str, Any]):
        self.basis = basis
        self.results = results_dict
        self.results_changed.emit()

    def add_plot(self, spec: Dict[str, Any]):
        self.plots.append(spec)
        self.plots_changed.emit()

    def update_plot(self, index: int, spec: Dict[str, Any]):
        if 0 <= index < len(self.plots):
            self.plots[index] = spec
            self.plots_changed.emit()

    def _build_default_physics_config(self) -> Dict[str, Any]:
        """Build initial physics_config by merging defaults from all selected physics."""
        from ..physics.registry import get_physics
        config: Dict[str, Any] = {}
        for phys_name in self.selected_physics:
            desc = get_physics(phys_name)
            if desc and hasattr(desc, 'default_config'):
                config.update(desc.default_config)
        return config

    def save_project(self, path: str):
        """Saves the project state, mesh, and results to a ZIP file."""
        try:
            # 1. Prepare State JSON
            state_dict = {
                "settings": asdict(self.settings),
                "parameters": self.parameters,
                "geometry_items": [asdict(g) for g in self.geometry_items],
                "boolean_operations": [asdict(b) for b in self.boolean_operations],
                "selected_physics": self.selected_physics,
                "materials_list": [asdict(m) for m in self.materials_list],
                "selected_study": self.selected_study,
                "time_config": self.time_config,
                "param_sweep_config": self.param_sweep_config,
                "current_time_index": self.current_time_index,
                "current_sweep_index": self.current_sweep_index,
                "bc_items": [asdict(b) for b in self.bc_items],
                "physics_features": [asdict(f) for f in self.physics_features],
                "physics_config": self.physics_config,
                "plots": self.plots,
                "probes": self.probes,
            }
            
            with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as zf:
                # Save state.json
                zf.writestr("state.json", json.dumps(state_dict, indent=2))
                
                # Save Mesh (if exists)
                if self.mesh:
                    # We assume self.mesh was loaded from a file or we can export it.
                    # Ideally, we should have the path to the msh file in self.msh_path
                    # If not, we might fail to save the exact mesh if we can't export from skfem object easily back to gmsh format without gmsh.
                    # However, in main_window.py, we set self.project.msh_path when generating mesh.
                    if hasattr(self, 'msh_path') and self.msh_path and os.path.exists(self.msh_path):
                         zf.write(self.msh_path, "mesh.msh")
                    else:
                        logger.warning("Mesh object exists but msh_path is missing or invalid. Mesh not saved.")

                # Save Results (numpy arrays)
                if self.results:
                    np.savez(os.path.join(self._temp_dir, "results.npz"), **self.results)
                    zf.write(os.path.join(self._temp_dir, "results.npz"), "results.npz")

            self.project_path = path
            return True
        except Exception as e:
            logger.error(f"Failed to save project: {e}")
            raise ProjectSaveError(f"Failed to save project to {path}") from e

    def load_project(self, path: str):
        """Loads the project from a ZIP file."""
        try:
            self.reset()
            with zipfile.ZipFile(path, 'r') as zf:
                # Load state.json
                state_json = zf.read("state.json").decode('utf-8')
                data = json.loads(state_json)
                
                self.settings = ProjectSettings(**data.get("settings", {}))
                self.parameters = data.get("parameters", {})
                self.geometry_items = [GeometryItem(**g) for g in data.get("geometry_items", [])]
                self.boolean_operations = [BooleanOperationItem(**b) for b in data.get("boolean_operations", [])]
                self.selected_physics = data.get("selected_physics", ["Electrostatics"])
                self.materials_list = [Material(**m) for m in data.get("materials_list", [])]
                self.selected_study = data.get("selected_study", "Stationary")
                self.time_config = data.get("time_config", {"t_start": 0.0, "t_end": 1.0, "dt": 0.1})
                self.param_sweep_config = data.get("param_sweep_config", {"enabled": False, "parameter": "", "start": 0.0, "end": 1.0, "step": 0.1})
                self.current_time_index = data.get("current_time_index", 0)
                self.current_sweep_index = data.get("current_sweep_index", 0)
                self.bc_items = [BoundaryConditionItem(**b) for b in data.get("bc_items", [])]
                self.physics_features = [PhysicsFeature(**f) for f in data.get("physics_features", [])]
                self.physics_config = data.get("physics_config", self._build_default_physics_config())
                self.plots = data.get("plots", [])
                self.probes = data.get("probes", [])
                
                # Load Mesh
                if "mesh.msh" in zf.namelist():
                    zf.extract("mesh.msh", self._temp_dir)
                    self.msh_path = os.path.join(self._temp_dir, "mesh.msh")
                    from skfem import Mesh, InteriorBasis, ElementTriP1, ElementTetP1
                    self.mesh = Mesh.load(self.msh_path)
                    # Reconstruct basis based on mesh dimensionality
                    Element = ElementTetP1 if self.mesh.dim() == 3 else ElementTriP1
                    self.basis = InteriorBasis(self.mesh, Element())

                # Load Results
                if "results.npz" in zf.namelist():
                    zf.extract("results.npz", self._temp_dir)
                    loaded = np.load(os.path.join(self._temp_dir, "results.npz"))
                    self.results = {k: loaded[k] for k in loaded.files}
            
            self.project_path = path
            self.state_changed.emit()
            # If we loaded mesh and results, emit those signals too so UI updates
            if self.mesh:
                self.mesh_changed.emit()
            if self.results:
                self.results_changed.emit()
                
            return True
        except Exception as e:
            logger.error(f"Failed to load project: {e}", exc_info=True)
            raise ProjectLoadError(f"Failed to load project from {path}") from e
