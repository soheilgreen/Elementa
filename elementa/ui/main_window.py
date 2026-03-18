from __future__ import annotations
import os
import sys
import json
from typing import Optional, Dict, List, Any

import gmsh
from PyQt6.QtCore import Qt, QSettings, QSize, QTimer, pyqtSignal, QModelIndex, QThread
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import (
    QMainWindow, QDockWidget, QMessageBox, QFileDialog, QTabWidget,
    QStatusBar, QLabel, QToolBar, QTextEdit, QApplication, QWidget, QVBoxLayout,
    QProgressDialog
)

from skfem import Mesh

# --- Local Imports ---
try:
    from ..cad.cad import ElementaCAD
    from ..core.project_state import ProjectState, GeometryItem, BooleanOperationItem
    from .graphics_canvas import InteractiveCanvas
    from .model_builder import ModelBuilder
    from .property_panel import PropertyPanel
    from .welcome_window import WelcomeWindow
    from .new_project_wizard import NewProjectWizard
    from .project_manager import ProjectManager
    from .icon_manager import get_icon
    from .ribbon_toolbar import RibbonToolbar
except ImportError as e:
    print(f"Fatal Error: Could not import a required module: {e}.")
    print("Please ensure all UI and backend files are in the correct directory structure.")
    sys.exit()


class LogConsole(QTextEdit):
    """A simple read-only text widget for logging messages."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setStyleSheet("QTextEdit { background-color: #f0f0f0; font-family: Consolas, monaco, monospace; }")

    def log(self, msg: str):
        self.append(msg)


class SolverThread(QThread):
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    finished_solve = pyqtSignal(object)  # passing PhysicsState
    error = pyqtSignal(str)

    def __init__(self, model_state, selected_physics, parent=None):
        super().__init__(parent)
        self.model_state = model_state
        self.selected_physics = selected_physics
        self._is_aborted = False

        self.model_state.progress_callback = self.progress.emit
        self.model_state.abort_check = self.is_aborted

    def is_aborted(self):
        return self._is_aborted

    def abort(self):
        self._is_aborted = True

    def run(self):
        from ..physics.registry import get_physics
        from ..core.evaluator import ParameterEvaluator
        
        sweep_cfg = self.model_state.physics_config.get("__sweep_config__", {})
        is_sweep = sweep_cfg.get("enabled", False)
        
        if is_sweep:
            param_name = sweep_cfg.get("parameter", "")
            try:
                start, end, step = float(sweep_cfg["start"]), float(sweep_cfg["end"]), float(sweep_cfg["step"])
            except:
                self.error.emit("Invalid sweep parameters.")
                return
                
            if step == 0:
                self.error.emit("Sweep step cannot be zero.")
                return
                
            steps = int(abs((end - start) / step)) + 1
            vals = [start + i*step for i in range(steps)]
            
            all_results = None
            times = list(vals)
            model_basis = None
            
            for i, val in enumerate(vals):
                if self._is_aborted:
                    self.error.emit("Solve aborted by user.")
                    return
                
                self.status.emit(f"Sweep step {i+1}/{len(vals)}: {param_name}={val:.4g}...")
                
                # Signal main thread to regenerate mesh for this parameter value
                # (A real implementation needs thread-safe queueing to the main thread block, 
                # but for this prototype, we'll assume pure-Python parameters evaluate fast enough 
                # or geometry doesn't strictly break if we cheat slightly, although ideally we'd use QMetaObject.invokeMethod.
                # To be safe from gmsh crashes, we must emit a signal or use safe callback)
            self.error.emit("Parametric mesh generation in background thread is unsafe. Requires synchronous main-thread meshing queue. (Not fully implemented yet)")
            return
                
        else:
            state = self.model_state
            try:
                for phys_name in self.selected_physics:
                    if self._is_aborted:
                        raise InterruptedError("Solve aborted by user.")
                    desc = get_physics(phys_name)
                    if desc is None:
                        self.error.emit(f"No solver registered for physics: {phys_name}")
                        return
                    self.status.emit(f"Solving {phys_name}...")
                    state = desc.assemble_and_solve(state)
                
                self.finished_solve.emit(state)
            except InterruptedError as e:
                self.error.emit(str(e))
            except Exception as e:
                import traceback
                traceback.print_exc()
                self.error.emit(f"Solver failed:\n{e}")


class ElementaMainWindow(QMainWindow):
    """The main application window."""
    def __init__(self, auto_show_welcome: bool = True):
        super().__init__()
        self.setWindowTitle("Elementa V1")
        self.resize(1200, 800)
        self.setWindowIcon(get_icon("Elementa_64.ico"))

        self.settings_store = QSettings("Elementa", "ElementaWorkbench")
        self.proj_mgr = ProjectManager(self.settings_store)

        self.project = ProjectState()
        self._cad: Optional[ElementaCAD] = None
        self._plot_windows = [] # Keep references to floating plot windows
        
        self._setup_ui()
        self._setup_actions()
        self._setup_menus_and_toolbars()
        self._setup_status_bar()
        self._connect_signals()
        
        self.model_builder.rebuild(self.project)
        
        # Initialize ribbon toolbar for current project dimensionality
        self.ribbon.update_for_context("", self.project.space_dim)

        if auto_show_welcome:
            QTimer.singleShot(200, self.show_welcome)

    def _setup_ui(self):
        self.canvas = InteractiveCanvas(self)
        self.tabs = QTabWidget()
        self.tabs.addTab(self.canvas, "Graphics")
        self.setCentralWidget(self.tabs)

        self.model_builder = ModelBuilder(self)
        dock_left = QDockWidget("Model Builder", self)
        dock_left.setWidget(self.model_builder)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, dock_left)

        self.property_panel = PropertyPanel(self.project, self)
        dock_right = QDockWidget("Settings", self)
        dock_right.setWidget(self.property_panel)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock_right)

        self.console = LogConsole(self)
        dock_console = QDockWidget("Log", self)
        dock_console.setWidget(self.console)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, dock_console)

    def _setup_actions(self):
        self.act_new = QAction(get_icon("newmodel.png"), "&New Project…", self)
        self.act_open = QAction(get_icon("openfile.png"), "&Open Project…", self)
        self.act_save = QAction(get_icon("save.png"), "&Save", self)
        self.act_save_as = QAction(get_icon("save.png"), "Save &As…", self)
        self.act_exit = QAction(QIcon.fromTheme("application-exit"), "E&xit", self)
        self.act_build_geom = QAction(get_icon("geometry.png"), "Build Geometry", self)
        self.act_mesh_gen = QAction(get_icon("mesh.png"), "Generate Mesh", self)
        self.act_solve = QAction(get_icon("solve.png"), "Compute", self)

    def _setup_menus_and_toolbars(self):
        mb = self.menuBar()
        
        # File Menu
        m_file = mb.addMenu("&File")
        m_file.addActions([self.act_new, self.act_open, self.act_save, self.act_save_as])
        m_file.addSeparator()
        m_file.addAction(self.act_exit)
        
        # Edit Menu
        m_edit = mb.addMenu("&Edit")
        act_undo = QAction(QIcon.fromTheme("edit-undo"), "Undo", self)
        act_undo.setShortcut("Ctrl+Z")
        act_undo.triggered.connect(lambda: self.log("Undo not yet implemented"))
        m_edit.addAction(act_undo)
        
        act_redo = QAction(QIcon.fromTheme("edit-redo"), "Redo", self)
        act_redo.setShortcut("Ctrl+Y")
        act_redo.triggered.connect(lambda: self.log("Redo not yet implemented"))
        m_edit.addAction(act_redo)
        
        # Geometry Menu
        m_geom = mb.addMenu("&Geometry")
        m_geom.addAction(self.act_build_geom)
        
        # Mesh Menu
        m_mesh = mb.addMenu("&Mesh")
        m_mesh.addAction(self.act_mesh_gen)
        
        # Physics Menu
        m_physics = mb.addMenu("&Physics")
        act_add_physics = QAction(get_icon("physics.png"), "Add Physics", self)
        act_add_physics.triggered.connect(lambda: self.log("Add Physics not yet implemented"))
        m_physics.addAction(act_add_physics)
        
        # Study Menu
        m_study = mb.addMenu("&Study")
        m_study.addAction(self.act_solve)
        
        # Results Menu
        m_results = mb.addMenu("&Results")
        act_surface_plot = QAction(get_icon("plot_surface.png"), "Add Surface Plot", self)
        act_surface_plot.triggered.connect(lambda: self.add_plot("Surface"))
        m_results.addAction(act_surface_plot)
        
        act_arrow_plot = QAction(get_icon("plot_arrow.png"), "Add Arrow Plot", self)
        act_arrow_plot.triggered.connect(lambda: self.add_plot("Arrow"))
        m_results.addAction(act_arrow_plot)

        act_point_probe = QAction(get_icon("probe_point.png"), "Add Point Probe", self)
        act_point_probe.triggered.connect(lambda: self.add_probe("Point Probe"))
        m_results.addAction(act_point_probe)

        act_line_probe = QAction(get_icon("probe_line.png"), "Add Line Probe", self)
        act_line_probe.triggered.connect(lambda: self.add_probe("Line Probe"))
        m_results.addAction(act_line_probe)
        
        # View Menu
        m_view = mb.addMenu("&View")
        act_zoom_fit = QAction(QIcon.fromTheme("zoom-fit-best"), "Zoom to Fit", self)
        act_zoom_fit.triggered.connect(lambda: self.log("Zoom to Fit not yet implemented"))
        m_view.addAction(act_zoom_fit)
        
        # Help Menu
        m_help = mb.addMenu("&Help")
        act_about = QAction(get_icon("help.png"), "About Elementa", self)
        act_about.triggered.connect(lambda: QMessageBox.about(self, "About Elementa", "Elementa V1.0\nAn Open Source Finite Element Method Simulation Software.\n\nMarch 2026, Soheil Hajibaba"))
        m_help.addAction(act_about)

        # Create ribbon toolbar instead of standard toolbar
        self.ribbon = RibbonToolbar(self)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.ribbon)

    def _setup_status_bar(self):
        self.status_bar = QStatusBar(self)
        self.setStatusBar(self.status_bar)
        self.status_label = QLabel("Ready")
        self.status_bar.addPermanentWidget(self.status_label)

    def _connect_signals(self):
        self.act_new.triggered.connect(self.on_new_project)
        self.act_open.triggered.connect(self.on_open_project)
        self.act_save.triggered.connect(self.on_save_project)
        self.act_save_as.triggered.connect(self.on_save_as_project)
        self.act_exit.triggered.connect(self.close)
        self.act_build_geom.triggered.connect(self.on_build_geometry)
        self.act_mesh_gen.triggered.connect(self.on_generate_mesh)
        self.act_solve.triggered.connect(self.on_solve)

        self.model_builder.selectionModel().currentChanged.connect(self.on_model_selection_changed)
        self.canvas.boundarySelected.connect(self.on_boundary_selected)
        self.canvas.domainSelected.connect(self.on_domain_selected)
        
        def _handle_probe(coord):
            # Check if we are currently editing a Point Probe node in the property panel
            ctx = self.project.active_panel_context
            if ctx.startswith("plot_"):
                try:
                    idx = int(ctx.split("_")[1])
                    if 0 <= idx < len(self.project.plots):
                        spec = self.project.plots[idx]
                        if spec.get("type") == "Probe":
                            spec["coord_x"] = coord[0]
                            spec["coord_y"] = coord[1]
                            if len(coord) > 2:
                                spec["coord_z"] = coord[2]
                            self.project.update_plot(idx, spec)
                            # Re-evaluate and refresh
                            self.on_plot_request(spec)
                            return
                except:
                    pass

            if not self.act_point_probe.isChecked() or not self.project.basis: return
            self.log(f"Clicked at {coord}. To evaluate specific fields, add a 'Point Probe' node under Results and select it.")
        self.canvas.pointProbed.connect(_handle_probe)
        self.property_panel.selectionChanged.connect(self.canvas.set_selected_boundaries)
        self.property_panel.domainSelectionChanged.connect(self.canvas.set_selected_domains)
        
        # Project State Signals
        self.project.state_changed.connect(self._on_project_state_changed)
        self.project.geometry_changed.connect(lambda: self.model_builder.rebuild(self.project))
        self.project.mesh_changed.connect(self._on_mesh_changed)
        self.project.results_changed.connect(self._on_results_changed)
        self.project.plots_changed.connect(lambda: self.model_builder.rebuild(self.project))
        
        # Ribbon Toolbar Signals - File
        self.ribbon.newProject.connect(self.on_new_project)
        self.ribbon.openProject.connect(self.on_open_project)
        self.ribbon.saveProject.connect(self.on_save_project)
        self.ribbon.undoAction.connect(lambda: self.log("Undo not yet implemented"))
        self.ribbon.redoAction.connect(lambda: self.log("Redo not yet implemented"))
        
        # Ribbon Toolbar Signals - Geometry
        self.ribbon.addRectangle.connect(lambda: self.property_panel.show_geometry_creator("rectangle"))
        self.ribbon.addDisk.connect(lambda: self.property_panel.show_geometry_creator("disk"))
        self.ribbon.addPolygon.connect(lambda: self.property_panel.show_geometry_creator("polygon"))
        self.ribbon.addBox.connect(lambda: self.property_panel.show_geometry_creator("box"))
        self.ribbon.addSphere.connect(lambda: self.property_panel.show_geometry_creator("sphere"))
        self.ribbon.addCylinder.connect(lambda: self.property_panel.show_geometry_creator("cylinder"))
        self.ribbon.addBooleanOp.connect(self.property_panel.show_boolean_creator)
        self.ribbon.buildGeometry.connect(self.on_build_geometry)
        self.ribbon.generateMesh.connect(self.on_generate_mesh)
        self.ribbon.computeStudy.connect(self.on_solve)
        self.ribbon.addSurfacePlot.connect(lambda: self.add_plot("Surface"))
        self.ribbon.addArrowPlot.connect(lambda: self.add_plot("Arrow"))
        self.ribbon.addPointProbe.connect(lambda: self.add_probe("Point Probe"))
        self.ribbon.addLineProbe.connect(lambda: self.add_probe("Line Probe"))
        

    def log(self, msg: str):
        self.console.log(msg)

    def _on_project_state_changed(self):
        self.model_builder.rebuild(self.project)
        self.property_panel.set_state(self.project)
        self.setWindowTitle(f"ELEMENTA - {self.project.project_name}")

    def _on_mesh_changed(self):
        if self.project.mesh:
            self.canvas.show_mesh(self.project.mesh)
            self.log(f"Mesh updated: {self.project.mesh.nvertices} vertices.")
            
            # Trigger boundary list updates if any BC node is currently active
            self.property_panel.update_boundary_selection(self.project.active_panel_context)

    def _on_results_changed(self):
        if self.project.results:
            self.log("Results updated.")
            
            # If there are plots, select and plot the first one
            if self.project.plots:
                self.on_plot_request(self.project.plots[0])
            else:
                # Auto-create a default surface plot from the first scalar result field
                from ..physics.registry import get_physics
                for phys_name in self.project.selected_physics:
                    desc = get_physics(phys_name)
                    if desc:
                        for rf in desc.result_fields:
                            if rf.field_type == "scalar" and rf.key in self.project.results:
                                spec = {"type": "Surface", "name": rf.label, "cmap": "viridis", "expr": rf.label}
                                self.project.add_plot(spec)
                                self.on_plot_request(spec)
                                return

    def add_plot(self, plot_type: str):
        count = sum(1 for p in self.project.plots if p.get("type") == plot_type) + 1
        name = f"{plot_type} {count}"
        spec = {"type": plot_type, "name": name, "cmap": "viridis"}
        self.project.add_plot(spec)
        # Navigate the property panel to the new plot's settings
        new_index = len(self.project.plots) - 1
        self.property_panel.show_plot_settings(new_index)
        # Render the plot on the canvas if results are available
        if self.project.results:
            self.on_plot_request(spec)
        self.log(f"Added {name}")

    def add_probe(self, probe_type: str):
        count = sum(1 for p in self.project.probes if p.get("type") == probe_type) + 1
        name = f"{probe_type} {count}"
        spec = {"type": probe_type, "name": name}
        self.project.probes.append(spec)
        # Rebuild tree
        self.model_builder.rebuild(self.project)
        new_index = len(self.project.probes) - 1
        # Select it
        from PyQt6.QtCore import Qt
        for i in range(self.model_builder.model.rowCount()):
            root = self.model_builder.model.item(i)
            # Find Results -> Probes -> new probe
            # But the simplest way is to select via active_panel_context which happens on click.
            # For now, just navigate the property panel directly:
            self.property_panel.show_probe_settings(new_index)
        self.log(f"Added {name}")

    def delete_probe(self, idx: int):
        if 0 <= idx < len(self.project.probes):
            del self.project.probes[idx]
            self.model_builder.rebuild(self.project)
            self.property_panel.show_page(None)

    def on_model_selection_changed(self, current: QModelIndex, previous: QModelIndex):
        if not current.isValid(): return
        item = self.model_builder.model.itemFromIndex(current)
        key = item.data(Qt.ItemDataRole.UserRole)
        self.project.active_panel_context = key or ""
        
        # Update ribbon toolbar based on selection
        self.ribbon.update_for_context(key or "", self.project.space_dim)
        
        is_plot = key and key.startswith("plot_")
        is_probe = key and key.startswith("probe_")
        is_domain_node = key and (key.startswith("mat_") or key.startswith("physfeat_"))

        # Clear domain highlights silently if moving to a plot/probe, otherwise trigger redraw
        if not is_domain_node and getattr(self, '_last_was_domain_node', False):
            if is_plot or is_probe:
                self.canvas._selected_domains = set()
            else:
                self.canvas.set_selected_domains([])
        self._last_was_domain_node = is_domain_node

        if is_plot:
            try:
                idx = int(key.split("_")[1])
                self.property_panel.show_plot_settings(idx)
                if 0 <= idx < len(self.project.plots):
                    spec = self.project.plots[idx]
                    self.on_plot_request(spec)
                    self.tabs.setCurrentWidget(self.canvas)
            except Exception as e:
                import traceback
                self.log(f"Error plotting result: {e}")
                traceback.print_exc()
        elif is_probe:
            try:
                idx = int(key.split("_")[1])
                self.property_panel.show_probe_settings(idx)
                if 0 <= idx < len(self.project.probes):
                    spec = self.project.probes[idx]
                    self.on_probe_request(spec)
                    self.tabs.setCurrentWidget(self.canvas)
            except Exception as e:
                self.log(f"Error plotting probe: {e}")
        else:
            self.property_panel.show_page(key)

        # Visualization triggers
        if key == "geometry" or (key and key.startswith("geom_")):
            self.on_build_geometry()
            self.tabs.setCurrentWidget(self.canvas)
        elif key == "mesh" and self.project.mesh:
            self.canvas.show_mesh(self.project.mesh)
            self.tabs.setCurrentWidget(self.canvas)
        elif key and key.startswith("bc_"):
            bc_name = key.split("_", 1)[1]
            bc_item = next((b for b in self.project.bc_items if b.name == bc_name), None)
            if bc_item:
                self.canvas.set_selected_boundaries(bc_item.boundaries)
            if self.project.mesh:
                self.tabs.setCurrentWidget(self.canvas)
        elif key and key.startswith("mat_"):
            mat_name = key.split("_", 1)[1]
            mat = next((m for m in self.project.materials_list if m.name == mat_name), None)
            if mat:
                self.canvas.set_selected_domains(mat.domains)
            if self.project.mesh:
                self.tabs.setCurrentWidget(self.canvas)
        elif key and key.startswith("physfeat_"):
            feat_name = key.split("_", 1)[1]
            feat = next((f for f in self.project.physics_features if f.name == feat_name), None)
            if feat:
                self.canvas.set_selected_domains(feat.domains)
            if self.project.mesh:
                self.tabs.setCurrentWidget(self.canvas)
        elif key == "results" and self.project.plots and self.project.results:
            # Show the first available plot when clicking the Results node
            self.on_plot_request(self.project.plots[0])
        elif is_plot:
            pass # Plot rendering already handled above
        else:
            self.canvas.set_selected_domains([])
            
    def on_domain_selected(self, name: str, is_ctrl: bool):
        ctx = self.project.active_panel_context
        if ctx.startswith("mat_"):
            mat_name = ctx.split("_", 1)[1]
            mat = next((m for m in self.project.materials_list if m.name == mat_name), None)
            if mat:
                if not is_ctrl:
                    mat.domains.clear()
                if name in mat.domains:
                    mat.domains.remove(name)
                else:
                    mat.domains.append(name)
                # Refresh property panel to update list selection UI
                self.property_panel.update_domain_selection(ctx)
                self.canvas.set_selected_domains(mat.domains)
        elif ctx.startswith("physfeat_"):
            feat_name = ctx.split("_", 1)[1]
            feat = next((f for f in self.project.physics_features if f.name == feat_name), None)
            if feat:
                if not is_ctrl:
                    feat.domains.clear()
                if name in feat.domains:
                    feat.domains.remove(name)
                else:
                    feat.domains.append(name)
                # Refresh property panel to update list selection UI
                self.property_panel.update_domain_selection(ctx)
                self.canvas.set_selected_domains(feat.domains)

    def on_boundary_selected(self, name: str, is_ctrl: bool):
        ctx = self.project.active_panel_context
        if ctx.startswith("bc_"):
            bc_name = ctx.split("_", 1)[1]
            bc_item = next((b for b in self.project.bc_items if b.name == bc_name), None)
            if bc_item:
                if not is_ctrl:
                    bc_item.boundaries.clear()
                if name in bc_item.boundaries:
                    bc_item.boundaries.remove(name)
                else:
                    bc_item.boundaries.append(name)
                # Refresh property panel to update list selection UI
                self.property_panel.update_boundary_selection(ctx)
                self.canvas.set_selected_boundaries(set(bc_item.boundaries))
                return

        if not is_ctrl:
            self.project.selected_boundaries.clear()
        
        if name in self.project.selected_boundaries:
            self.project.selected_boundaries.remove(name)
        else:
            self.project.selected_boundaries.add(name)
        
        self.canvas.set_selected_boundaries(self.project.selected_boundaries)
        self.log(f"Selection updated: {self.project.selected_boundaries or 'empty'}")
        
        # Sync the property panel if a boundary condition page is active
        self.property_panel.update_boundary_selection(self.project.active_panel_context)

    def on_plot_request(self, spec: dict):
        if self.project.mesh is None or not self.project.results:
            QMessageBox.warning(self, "Plot Error", "No results available. Please run a study first.")
            return
        
        from ..physics.registry import get_physics

        # Look up the result field matching the plot's expression
        expr = spec.get('expr', '')
        result_data = None
        field_type = None
        unit = ''

        # Handle 'norm(key)' request from Point Probe
        is_norm_request = False
        target_key = None
        if expr.startswith("norm(") and expr.endswith(")"):
            is_norm_request = True
            target_key = expr[5:-1]

        for phys_name in self.project.selected_physics:
            desc = get_physics(phys_name)
            if desc:
                for rf in desc.result_fields:
                    if (not is_norm_request and rf.label == expr) or (is_norm_request and rf.key == target_key):
                        result_data = self.project.results.get(rf.key)
                        field_type = rf.field_type
                        unit = rf.unit
                        break
                if result_data is not None:
                    break

        # If it was a norm request, the unit is preserved but we recalculate the vector into a scalar array
        if is_norm_request and result_data is not None and field_type == 'vector':
            import numpy as np
            if isinstance(result_data, list):
                # Apply norm to every timestep/sweep step
                # Vectors in skfem/Elementa are usually (dim, N)
                norm_data = []
                for step_data in result_data:
                    norm_data.append(np.sqrt(np.sum(step_data**2, axis=0)))
                result_data = norm_data
            else:
                result_data = np.sqrt(np.sum(result_data**2, axis=0))
            field_type = 'scalar'

        # Fallback: if no match found, pick first scalar for Surface, first vector for Arrow
        if result_data is None:
            for phys_name in self.project.selected_physics:
                desc = get_physics(phys_name)
                if desc:
                    for rf in desc.result_fields:
                        want = "vector" if spec['type'] == "Arrow" else "scalar"
                        if rf.field_type == want:
                            result_data = self.project.results.get(rf.key)
                            field_type = rf.field_type
                            unit = rf.unit
                            break
                    if result_data is not None:
                        break

        # Handle time-dependent results (stored as lists)
        time_vals = self.project.results.get('time_vals', self.project.results.get('times', None))
        is_sweep = self.project.param_sweep_config.get("enabled", False)
        
        if isinstance(result_data, list) and (time_vals is not None or is_sweep):
            spec = dict(spec)  # copy to avoid mutating the original
            
            # Calculate global limits for consistent colorbar across all dimensions
            try:
                import numpy as np
                if field_type == "scalar":
                    flat_d = []
                    # Could be list of lists (sweep + time) or just list
                    for d1 in result_data:
                        if isinstance(d1, list):
                            flat_d.extend(d1)
                        else:
                            flat_d.append(d1)
                    cmin = float(min(np.min(d) for d in flat_d))
                    cmax = float(max(np.max(d) for d in flat_d))
                    spec['clim'] = (cmin, cmax)
                elif field_type == "vector":
                    flat_d = []
                    for d1 in result_data:
                        if isinstance(d1, list):
                            flat_d.extend(d1)
                        else:
                            flat_d.append(d1)
                    cmin = float(min(np.min(np.sqrt(sum(comp**2 for comp in d))) for d in flat_d))
                    cmax = float(max(np.max(np.sqrt(sum(comp**2 for comp in d))) for d in flat_d))
                    spec['clim'] = (cmin, cmax)
            except Exception as e:
                pass

            p_idx = self.project.current_sweep_index if is_sweep else -1
            t_idx = self.project.current_time_index if time_vals is not None else -1
            
            # Extract parametric slice if sweeping
            if is_sweep:
                if p_idx < 0 or p_idx >= len(result_data):
                    p_idx = len(result_data) - 1
                result_data = result_data[p_idx]
                
            # Extract time slice if time-dependent
            if isinstance(result_data, list) and time_vals is not None:
                if t_idx < 0 or t_idx >= len(result_data):
                    t_idx = len(result_data) - 1
                result_data = result_data[t_idx]

            # Add time/sweep info to the plot title
            if is_sweep and time_vals is not None:
                pname = self.project.param_sweep_config.get("parameter", "p")
                p_times = self.project.results.get('sweep_vals', [])
                pval = p_times[p_idx] if p_idx < len(p_times) else p_idx
                t_val = time_vals[t_idx] if t_idx < len(time_vals) else t_idx
                spec['name'] = f"{spec.get('name', '')} ({pname}={pval:.4g}, t={t_val:.4g} s)"
            elif is_sweep:
                pname = self.project.param_sweep_config.get("parameter", "p")
                p_times = self.project.results.get('sweep_vals', [])
                pval = p_times[p_idx] if p_idx < len(p_times) else p_idx
                spec['name'] = f"{spec.get('name', '')} ({pname}={pval:.4g})"
            else:
                t_val = time_vals[t_idx] if t_idx < len(time_vals) else time_vals[-1]
                spec['name'] = f"{spec.get('name', '')} (t={t_val:.4g} s)"
                
        # Pick the correct mesh and basis for parametric sweeps
        if is_sweep and 'meshes' in self.project.results:
            p_idx = self.project.current_sweep_index
            if p_idx < 0 or p_idx >= len(self.project.results['meshes']):
                p_idx = len(self.project.results['meshes']) - 1
            render_mesh = self.project.results['meshes'][p_idx]
            render_basis = self.project.results['bases'][p_idx]
        else:
            render_mesh = self.project.mesh
            render_basis = self.project.basis
            
        try:
            self.canvas.plot_results(spec, render_mesh, render_basis,
                                    result_data, field_type, unit)
            self.tabs.setCurrentWidget(self.canvas)
        except Exception as e:
            self.log(f"Error plotting data: {e}")

    def on_probe_request(self, spec: dict, evaluate: bool = True):
        # Always draw the probe location/line over whatever is currently on the canvas
        self.canvas.draw_probe(spec)
        
        if not evaluate:
            return
            
        if not self.project.results or not self.project.basis:
            self.log("No results available to probe.")
            return
            
        # Get result data based on time/sweep index
        time_vals = self.project.results.get('time_vals', self.project.results.get('times', None))
        sweep_cfg = self.project.param_sweep_config
        is_sweep = sweep_cfg.get("enabled", False)
        
        p_idx = self.project.current_sweep_index if is_sweep else -1
        t_idx = self.project.current_time_index if time_vals is not None else -1
        
        # Pick the correct mesh and basis for parametric sweeps
        if is_sweep and 'meshes' in self.project.results:
            if p_idx < 0 or p_idx >= len(self.project.results['meshes']):
                p_idx = len(self.project.results['meshes']) - 1
            render_mesh = self.project.results['meshes'][p_idx]
            render_basis = self.project.results['bases'][p_idx]
        else:
            render_mesh = self.project.mesh
            render_basis = self.project.basis
            
        expr = spec.get('expr', '')
        
        # Look up field type and key from physics registry
        from ..physics.registry import get_physics
        field_type = "scalar"
        field_key = None
        unit = ""
        for phys_name in self.project.selected_physics:
            desc = get_physics(phys_name)
            if desc:
                for rf in desc.result_fields:
                    if expr.startswith(rf.label) or expr.startswith(rf.key):
                        field_key = rf.key
                        field_type = rf.field_type
                        unit = rf.unit
                        break
                if field_key: break

        if not field_key or field_key not in self.project.results:
            self.log(f"Could not find result data for expression: {expr}")
            spec['probe_val'] = "N/A"
            self._update_probe_gui(spec)
            return
            
        result_data = self.project.results[field_key]
        
        if isinstance(result_data, list):
            if is_sweep:
                if p_idx < 0 or p_idx >= len(result_data):
                    p_idx = len(result_data) - 1
                result_data = result_data[p_idx]
                
            if isinstance(result_data, list): # time dependent
                if t_idx < 0 or t_idx >= len(result_data):
                    t_idx = len(result_data) - 1
                result_data = result_data[t_idx]

        import numpy as np
        
        # Precalculate scalar data for interpolation (same as surface plots)
        if field_type == "vector" and result_data is not None:
            if self.project.space_dim == 3:
                data_to_interp = np.sqrt(result_data[0]**2 + result_data[1]**2 + result_data[2]**2)
            else:
                data_to_interp = np.sqrt(result_data[0]**2 + result_data[1]**2)
        else:
            data_to_interp = result_data

        if spec['type'] == 'Point Probe':
            coord = (spec.get('coord_x', 0.0), spec.get('coord_y', 0.0))
            if self.project.space_dim == 3:
                coord = (coord[0], coord[1], spec.get('coord_z', 0.0))
                
            try:
                coord_arr = np.array(coord)[:, None]
                val = render_basis.interpolator(data_to_interp)(coord_arr)[0]
                spec['probe_val'] = f"{val:.4g} {unit}".strip()
            except Exception as e:
                import traceback
                traceback.print_exc()
                spec['probe_val'] = f"Error"
                
            self._update_probe_gui(spec)
            
        elif spec['type'] == 'Line Probe':
            num_pts = spec.get('num_pts', 100)
            x0, y0 = spec.get('start_x', -0.5), spec.get('start_y', -0.5)
            x1, y1 = spec.get('end_x', 0.5), spec.get('end_y', 0.5)
            
            x_vals = np.linspace(x0, x1, num_pts)
            y_vals = np.linspace(y0, y1, num_pts)
            
            if self.project.space_dim == 3:
                z0, z1 = spec.get('start_z', -0.5), spec.get('end_z', 0.5)
                z_vals = np.linspace(z0, z1, num_pts)
                coords = np.vstack((x_vals, y_vals, z_vals))
            else:
                coords = np.vstack((x_vals, y_vals))
                
            try:
                interp = render_basis.interpolator(data_to_interp)
                vals = interp(coords)
                
                spec['probe_val'] = f"Array({len(vals)} pts)"
                
                # Create a 1D Plot window
                from .plot_window import Plot1DWindow
                dist = np.linspace(0, np.sqrt((x1-x0)**2 + (y1-y0)**2 + (0 if self.project.space_dim == 2 else (z1-z0)**2)), num_pts)
                win = Plot1DWindow(dist, vals, parent=self)
                win.setWindowTitle(f"Line Probe: {spec['name']}")
                win.set_labels("Arc Length [m]", f"{expr} [{unit}]" if unit else expr)
                win.show()
                win.raise_()
                win.activateWindow()
                # Store reference to prevent garbage collection
                self._plot_windows.append(win)
                
            except Exception as e:
                import traceback
                traceback.print_exc()
                spec['probe_val'] = f"Error"
                
            self._update_probe_gui(spec)
            
    def _update_probe_gui(self, spec):
        try:
            idx = self.project.probes.index(spec)
            self.project.probes[idx] = spec
            ctx = self.project.active_panel_context
            if ctx == f"probe_{idx}":
                self.property_panel.show_probe_settings(idx)
        except ValueError:
            pass

    def _build_cad_model(self):
        from ..core.cad_builder import CADBuilder
        try:
            self.log("Building CAD model...")
            self._cad = CADBuilder.build_model(self.project)
            return True
        except Exception as e:
            QMessageBox.critical(self, "CAD Error", str(e))
            return False

    def on_build_geometry(self):
        try:
            if not self._build_cad_model(): return
            self.canvas.show_geometry(gmsh, self.project.space_dim)
            self.log("Geometry build complete and previewed.")
        except Exception as e:
             QMessageBox.critical(self, "Parameter Error", f"Error evaluating expressions:\n{e}")

    def on_generate_mesh(self):
        try:
            if not self._build_cad_model(): return
            mesh_size = getattr(self.project, 'mesh_size', None)
            self._cad.generate_mesh(dim=self.project.space_dim, mesh_size=mesh_size)
            basename = os.path.join(self.project._temp_dir, "temp_mesh")
            self._cad.export(basename)
            msh_path = basename + ".msh"
            self.project.msh_path = msh_path
            mesh = Mesh.load(msh_path)
            
            self.project.set_mesh(mesh)
            self.project.selected_boundaries.clear()
            self.log(f"Mesh generated with {mesh.nvertices} vertices and {mesh.nelements} elements.")
        except Exception as e:
            QMessageBox.critical(self, "Meshing Error", f"Failed to generate mesh:\n{e}")
        finally:
            if gmsh.isInitialized(): gmsh.clear()

        try:
            self.property_panel.update_boundary_selection(self.project.active_panel_context)
        except RuntimeError:
            pass

    def on_solve(self):
        if not self.project.mesh:
            QMessageBox.warning(self, "Solve Error", "Please generate a mesh first.")
            return
            
        import copy
        from ..core.evaluator import ParameterEvaluator
        from ..physics.base import PhysicsState
        from ..physics.registry import get_physics
        import numpy as np
        
        sweep_cfg = self.project.param_sweep_config
        is_sweep = sweep_cfg.get("enabled", False)
        
        if is_sweep:
            # Main-thread Parametric Sweep Implementation (since gmsh is not thread-safe)
            param_name = sweep_cfg.get("parameter", "")
            try:
                start, end, step = float(sweep_cfg["start"]), float(sweep_cfg["end"]), float(sweep_cfg["step"])
            except:
                QMessageBox.critical(self, "Sweep Error", "Invalid sweep parameters.")
                return
                
            if step == 0:
                QMessageBox.warning(self, "Sweep Error", "Sweep step cannot be zero.")
                return
                
            steps = int(abs((end - start) / step)) + 1
            vals = [start + i*step for i in range(steps)]
            
            self.progress_dialog = QProgressDialog("Running Parametric Sweep...", "Abort", 0, len(vals), self)
            self.progress_dialog.setWindowTitle("Computing Sweep")
            self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
            self.progress_dialog.setMinimumDuration(0)
            
            sweep_results = {}
            for k in ['T', 'q', 'phi', 'E']:
                sweep_results[k] = []
            sweep_results['meshes'] = []
            sweep_results['bases'] = []
            time_vals = None
            
            final_basis = None
            
            # Backup original param
            orig_params = copy.deepcopy(self.project.parameters)
            
            for i, val in enumerate(vals):
                if self.progress_dialog.wasCanceled():
                    self.log("Sweep aborted.")
                    break
                    
                self.progress_dialog.setLabelText(f"Sweep step {i+1}/{len(vals)}: {param_name}={val:.4g}")
                self.progress_dialog.setValue(i)
                QApplication.processEvents() # Keep UI responsive
                
                # Update param & rebuild
                self.project.parameters[param_name] = str(val)
                self.on_build_geometry()
                self.on_generate_mesh()
                
                # Evaluate new BCs
                try:
                    eval_params = ParameterEvaluator.resolve_parameters(self.project.parameters)
                    bc_eval = []
                    for item in self.project.bc_items:
                        eval_item = copy.deepcopy(item)
                        for k, v in eval_item.properties.items():
                            eval_item.properties[k] = ParameterEvaluator.evaluate_expression(v, eval_params)
                        bc_eval.append(eval_item)
                except Exception as e:
                    self.log(f"Evaluate error: {e}")
                    continue
                    
                # Solve synchronously
                state = PhysicsState(
                    mesh=self.project.mesh, 
                    bc_items=bc_eval, 
                    physics_config=self.project.physics_config,
                    materials=self.project.materials_list,
                    physics_features=self.project.physics_features,
                    study_type=self.project.selected_study,
                    time_config=self.project.time_config,
                )
                
                for phys_name in self.project.selected_physics:
                    desc = get_physics(phys_name)
                    if desc:
                        state = desc.assemble_and_solve(state)
                        
                # Accumulate
                if state.results:
                    for k in ['T', 'q', 'phi', 'E']:
                        if k in state.results:
                            sweep_results[k].append(state.results[k])
                    
                    if 'times' in state.results and time_vals is None:
                        time_vals = state.results['times']
                        
                    sweep_results['meshes'].append(state.mesh)
                    sweep_results['bases'].append(state.basis)
                    final_basis = state.basis
                    
            # Restore params
            self.project.parameters = orig_params
            
            # Rebuild one last time for correct visual state
            self.on_build_geometry()
            self.on_generate_mesh()
            
            # Clean up empty arrays
            sweep_results = {k: v for k, v in sweep_results.items() if v}
            sweep_results['sweep_vals'] = vals
            if time_vals is not None:
                sweep_results['time_vals'] = time_vals
            self.project.set_results(final_basis, sweep_results)
            self.progress_dialog.setValue(len(vals))
            self.log("Parametric Sweep complete.")
            return

        # --- Normal Async Single Solve ---
        try:
            eval_params = ParameterEvaluator.resolve_parameters(self.project.parameters)
            # Evaluate properties for all boundary condition items
            bc_eval = []
            for item in self.project.bc_items:
                eval_item = copy.deepcopy(item)
                for k, v in eval_item.properties.items():
                    eval_item.properties[k] = ParameterEvaluator.evaluate_expression(v, eval_params)
                bc_eval.append(eval_item)
        except Exception as e:
            QMessageBox.critical(self, "Parameter Error", f"Error evaluating expressions:\n{e}")
            return
        
        model_state = PhysicsState(
            mesh=self.project.mesh, 
            bc_items=bc_eval, 
            physics_config=self.project.physics_config,
            materials=self.project.materials_list,
            physics_features=self.project.physics_features,
            study_type=self.project.selected_study,
            time_config=self.project.time_config,
        )
        
        # Pass sweep config to allow thread to know it's not sweeping
        model_state.physics_config["__sweep_config__"] = sweep_cfg
        
        self.progress_dialog = QProgressDialog("Initializing solver...", "Abort", 0, 100, self)
        self.progress_dialog.setWindowTitle("Computing")
        self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self.progress_dialog.setMinimumDuration(0)
        self.progress_dialog.setValue(0)

        self.solver_thread = SolverThread(model_state, self.project.selected_physics, self)
        self.solver_thread.progress.connect(self.progress_dialog.setValue)
        self.solver_thread.status.connect(self.progress_dialog.setLabelText)
        self.progress_dialog.canceled.connect(self.solver_thread.abort)
        
        self.solver_thread.finished_solve.connect(self._on_solve_finished)
        self.solver_thread.error.connect(self._on_solve_error)
        
        self.solver_thread.start()

    def _on_solve_finished(self, final_state):
        self.progress_dialog.setValue(100)
        self.project.set_results(final_state.basis, final_state.results)
        self.status_label.setText("Ready")
        self.log("Solve complete.")

    def _on_solve_error(self, err_msg):
        if hasattr(self, 'progress_dialog'):
            self.progress_dialog.cancel()
        if "aborted" in err_msg.lower():
            self.log("Solve aborted.")
            self.status_label.setText("Ready")
        else:
            QMessageBox.critical(self, "Solver Error", err_msg)
            self.status_label.setText("Ready")
            
    def add_geometry_node_to_tree(self, name, kind):
        # Handled by signal
        pass

    def add_boolean_node_to_tree(self, name, kind):
        # Handled by signal
        pass

    def delete_geometry_item(self, name):
        self.project.remove_geometry_item(name)
        self.log(f"Deleted geometry item: {name}")

    def add_blank_material(self):
        from ..core.project_state import Material
        mat = Material(f"Material {len(self.project.materials_list) + 1}", {"relative_permittivity": "1.0"}, ["All"])
        self.project.add_material(mat)
        self.log(f"Added {mat.name}")

    def delete_material(self, name):
        self.project.remove_material(name)
        self.log(f"Deleted material: {name}")

    def add_physics_feature(self, kind: str = "charge_density"):
        """Add a physics feature using metadata from the registry."""
        from ..core.project_state import PhysicsFeature
        from ..physics.registry import get_physics
        # Find the FeatureType definition from the active physics
        for phys_name in self.project.selected_physics:
            desc = get_physics(phys_name)
            if desc:
                for ft in desc.feature_types:
                    if ft.kind == kind:
                        feat = PhysicsFeature(
                            kind=ft.kind,
                            name=f"{ft.label} {len(self.project.physics_features) + 1}",
                            properties=dict(ft.default_props),
                            domains=list(ft.default_domains),
                        )
                        self.project.add_physics_feature(feat)
                        self.log(f"Added {feat.name}")
                        return
        # Fallback for backwards compatibility
        feat = PhysicsFeature(kind, f"{kind} {len(self.project.physics_features) + 1}", {"value": "0.0"}, ["All"])
        self.project.add_physics_feature(feat)
        self.log(f"Added {feat.name}")

    def delete_physics_feature(self, name):
        self.project.remove_physics_feature(name)
        self.log(f"Deleted physics feature: {name}")

    def add_boundary_condition(self, kind: str):
        """Add a boundary condition using metadata from the registry."""
        from ..core.project_state import BoundaryConditionItem
        from ..physics.registry import get_physics
        for phys_name in self.project.selected_physics:
            desc = get_physics(phys_name)
            if desc and hasattr(desc, 'bc_types'):
                for bct in desc.bc_types:
                    if bct.kind == kind:
                        kind_count = sum(1 for b in self.project.bc_items if b.kind == kind)
                        bc = BoundaryConditionItem(
                            kind=bct.kind,
                            name=f"{bct.label} {kind_count + 1}",
                            properties=dict(bct.default_props),
                            boundaries=[]
                        )
                        self.project.add_boundary_condition(bc)
                        self.log(f"Added {bc.name}")
                        return
        # Fallback
        kind_count = sum(1 for b in self.project.bc_items if b.kind == kind)
        bc = BoundaryConditionItem(kind=kind, name=f"{kind} {kind_count + 1}", properties={}, boundaries=[])
        self.project.add_boundary_condition(bc)
        self.log(f"Added {bc.name}")

    def delete_boundary_condition(self, name):
        self.project.remove_boundary_condition(name)
        self.log(f"Deleted boundary condition: {name}")

    def on_new_project(self):
        wiz = NewProjectWizard(self)
        if wiz.exec():
            spec = wiz.build_spec()
            self.project.reset()
            self.project.space_dim = spec.space_dim
            self.project.selected_physics = spec.physics
            self.project.selected_study = spec.study
            self.project.project_name = spec.name
            # Rebuild physics_config from registry defaults for the selected physics
            self.project.physics_config = self.project._build_default_physics_config()
            
            # Update ribbon toolbar based on new space_dim
            self.ribbon.update_for_context("", self.project.space_dim)
            
            self.canvas.clear()
            self.log(f"New {spec.space_dim}D project created: {spec.name}")

    def on_save_project(self):
        if not self.project.project_path:
            self.on_save_as_project()
        else:
            self._save_project_to_path(self.project.project_path)

    def on_save_as_project(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save Elementa Project", "", "Elementa Project (*.elem)")
        if path:
            self._save_project_to_path(path)

    def _save_project_to_path(self, path: str):
        from ..core.exceptions import ProjectSaveError
        try:
            self.project.save_project(path)
            self.log(f"Project saved to {path}")
            self.proj_mgr.add_recent(path)
        except ProjectSaveError as e:
            QMessageBox.critical(self, "Save Error", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"An unexpected error occurred while saving:\n{e}")

    def on_open_project(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open Elementa Project", "", "Elementa Project (*.elem)")
        if path:
            self._load_project(path)

    def _load_project(self, path: str):
        from ..core.exceptions import ProjectLoadError
        try:
            self.project.load_project(path)
            self.canvas.clear()
            self.log(f"Project loaded from {path}")
            self.proj_mgr.add_recent(path)
            # Update ribbon for loaded project dimensionality
            self.ribbon.update_for_context("", self.project.space_dim)
        except ProjectLoadError as e:
            QMessageBox.critical(self, "Load Error", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Load Error", f"An unexpected error occurred while loading:\n{e}")

    def show_welcome(self):
        dlg = WelcomeWindow(self.proj_mgr, self)
        choice = dlg.exec_and_get_choice()
        if choice == "new":
            self.on_new_project()
        elif choice == "open":
            self.on_open_project()
        elif isinstance(choice, str) and os.path.exists(choice):
            self._load_project(choice)

    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'Exit', 'Are you sure you want to exit?',
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            if hasattr(self, 'solver_thread') and self.solver_thread.isRunning():
                self.solver_thread.abort()
                self.solver_thread.wait(1000)
                
            if gmsh.isInitialized():
                gmsh.finalize()
            self.project.cleanup()
            event.accept()
        else:
            event.ignore()

