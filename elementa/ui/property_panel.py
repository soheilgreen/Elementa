from __future__ import annotations
from typing import Dict, List, Optional, Set, Any

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLineEdit, QGroupBox,
    QPushButton, QComboBox, QTableWidget, QTableWidgetItem, QHBoxLayout,
    QScrollArea, QMessageBox, QListWidget, QListWidgetItem, QLabel,
    QDoubleSpinBox, QCheckBox, QFrame, QSlider
)

from ..core.project_state import ProjectState, GeometryItem, BooleanOperationItem


class PropertyPanel(QScrollArea):
    """
    Dynamic property panel that rebuilds its content based on selected node.
    """
    selectionChanged = pyqtSignal(set)  # Emits selected boundary names
    domainSelectionChanged = pyqtSignal(list)  # Emits selected domain names
    
    def __init__(self, project: ProjectState, owner):
        super().__init__()
        self.project = project
        self.owner = owner
        self.current_node_key = None
        self.current_plot_index = None
        
        # Main content widget
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(8, 8, 8, 8)
        self.content_layout.setSpacing(8)
        
        self.setWidget(self.content_widget)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self._apply_stylesheet()
        
        # Show default content
        self._show_empty_state()
        
    def _apply_stylesheet(self):
        """Apply COMSOL-like styling."""
        self.setStyleSheet("""
            QScrollArea {
                background-color: #f5f5f5;
                border: none;
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #c0c0c0;
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 8px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 2px 6px;
                background-color: #e0e0e0;
                border-radius: 3px;
            }
            QLabel {
                color: #333;
            }
            QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {
                padding: 4px;
                border: 1px solid #c0c0c0;
                border-radius: 3px;
                background-color: white;
            }
   QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {
                border: 1px solid #0078d7;
            }
            QPushButton {
                padding: 6px 12px;
                background-color: #0078d7;
                color: white;
                border: none;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #005a9e;
            }
            QPushButton:pressed {
                background-color: #004578;
            }
        """)
        
    def _clear_content(self):
        """Clear all content from the panel."""
        while self.content_layout.count():
            child = self.content_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        # Null out widget references so they aren't used after deletion
        self.active_boundary_list = None
                
    def _show_empty_state(self):
        """Show message when no node is selected."""
        self._clear_content()
        label = QLabel("Select an item in the Model Builder to view its settings.")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("color: #888; font-style: italic; padding: 20px;")
        self.content_layout.addWidget(label)
        self.content_layout.addStretch(1)
        
    def _create_section(self, title: str) -> tuple[QGroupBox, QFormLayout]:
        """Create a collapsible section with form layout."""
        group = QGroupBox(title)
        layout = QFormLayout()
        layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.setFormAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        layout.setSpacing(8)
        group.setLayout(layout)
        return group, layout
        
    def show_page(self, key: Optional[str]):
        """Main entry point to show settings for a given node key."""
        if key == self.current_node_key:
            return  # Already showing this page
            
        self.current_node_key = key
        
        if not key:
            self._show_empty_state()
        elif key == "parameters":
            from .panels.parameters_panel import ParametersPanel
            self._set_panel_widget(ParametersPanel(self.project, self.owner))
        elif key == "geometry":
            self._build_geometry_page()
        elif key.startswith("geom_"):
            self._build_geometry_item_page(key)
        elif key == "mesh":
            from .panels.mesh_panel import MeshPanel
            self._set_panel_widget(MeshPanel(self.project, self.owner))
        elif key in ["physics", "phys"] or (key and key.startswith("phys_")):
            from .panels.physics_panel import PhysicsPanel
            self._set_panel_widget(PhysicsPanel(self.project, self.owner))
        elif key and key.startswith("bc_"):
            self._build_bc_item_page(key)
        elif key == "study":
            from .panels.study_panel import StudyPanel
            self._set_panel_widget(StudyPanel(self.project, self.owner))
        elif key == "results":
            self._build_results_page()
        elif key == "materials":
            self._build_materials_page()
        elif key.startswith("mat_"):
            self._build_material_item_page(key)
        elif key.startswith("physfeat_"):
            self._build_physics_feature_page(key)
        elif key == "probes":
            self._show_empty_state() # Could be a list of probes but empty state is fine
        elif key.startswith("probe_"):
            self.show_probe_settings(int(key.split("_")[1]))
        else:
            self._show_empty_state()
            
    def _set_panel_widget(self, widget: QWidget):
        self._clear_content()
        self.content_layout.addWidget(widget)
            
    # ==================== NODE-SPECIFIC PAGE BUILDERS ====================
    

        
    def _build_geometry_page(self):
        """Build the Geometry node page."""
        self._clear_content()
        
        title = QLabel("Geometry")
        title.setStyleSheet("font-size: 16px; font-weight: bold; padding: 4px;")
        self.content_layout.addWidget(title)
        
        info = QLabel("Use the ribbon toolbar or right-click to add geometry primitives.")
        info.setStyleSheet("color: #666; font-style: italic; padding: 8px;")
        info.setWordWrap(True)
        self.content_layout.addWidget(info)
        self.content_layout.addStretch(1)
        
    def _build_geometry_item_page(self, key: str):
        """Build page for a specific geometry item."""
        self._clear_content()
        
        # Extract item name
        name = key.split("_", 1)[1]
        
        # Find the item
        item = None
        for gi in self.project.geometry_items:
            if gi.name == name:
                item = gi
                break
        if not item:
            for bo in self.project.boolean_operations:
                if bo.name == name:
                    item = bo
                    break
                    
        if not item:
            self._show_empty_state()
            return
            
        # Title
        title = QLabel(f"{item.name} ({item.kind})")
        title.setStyleSheet("font-size: 16px; font-weight: bold; padding: 4px;")
        self.content_layout.addWidget(title)
        
        # Editable name
        name_group, name_layout = self._create_section("Object")
        name_edit = QLineEdit(item.name)
        name_layout.addRow("Name:", name_edit)
        
        def on_name_changed(new_name):
            new_name = new_name.strip()
            if not new_name or new_name == item.name:
                return
            item.name = new_name
            title.setText(f"{item.name} ({item.kind})")
            self.current_node_key = f"geom_{new_name}"
            self.owner.model_builder.rebuild(self.project)
            
        name_edit.editingFinished.connect(lambda: on_name_changed(name_edit.text()))
        self.content_layout.addWidget(name_group)
        
        # Show parameters based on type
        if isinstance(item, GeometryItem):
            self._build_primitive_form(item)
        elif isinstance(item, BooleanOperationItem):
            self._build_boolean_form(item)
            
        self.content_layout.addStretch(1)
        
    def _build_primitive_form(self, item: GeometryItem):
        """Build form for geometry primitive."""
        group, layout = self._create_section("Shape and Size")
        
        params = item.params
        
        def make_param_handler(param_key, edit):
            def handler(text):
                item.params[param_key] = text
            return handler
        
        param_defs = []
        if item.kind == "rectangle":
            param_defs = [("Width (dx) [m]:", "dx", "1.0"), ("Height (dy) [m]:", "dy", "1.0"),
                          ("Center X (cx) [m]:", "cx", "0.0"), ("Center Y (cy) [m]:", "cy", "0.0")]
        elif item.kind == "disk":
            param_defs = [("Radius X (rx) [m]:", "rx", "0.5"), ("Radius Y (ry) [m]:", "ry", "0.5"),
                          ("Center X (cx) [m]:", "cx", "0.0"), ("Center Y (cy) [m]:", "cy", "0.0")]
        elif item.kind == "polygon":
            param_defs = [("Points [m]:", "points", "[(0,0), (1,0), (0.5,0.8)]")]
        elif item.kind == "box":
            param_defs = [("Width (dx) [m]:", "dx", "1.0"), ("Depth (dy) [m]:", "dy", "1.0"),
                          ("Height (dz) [m]:", "dz", "1.0"), ("Center X (cx) [m]:", "cx", "0.0"),
                          ("Center Y (cy) [m]:", "cy", "0.0"), ("Center Z (cz) [m]:", "cz", "0.0")]
        elif item.kind == "sphere":
            param_defs = [("Radius (r) [m]:", "r", "0.5"), ("Center X (cx) [m]:", "cx", "0.0"),
                          ("Center Y (cy) [m]:", "cy", "0.0"), ("Center Z (cz) [m]:", "cz", "0.0")]
        elif item.kind == "cylinder":
            param_defs = [("Radius (r) [m]:", "r", "0.2"), ("Height (h) [m]:", "h", "1.0"),
                          ("Base Center X (cx) [m]:", "cx", "0.0"), ("Base Center Y (cy) [m]:", "cy", "0.0"),
                          ("Base Center Z (cz) [m]:", "cz", "0.0")]
        
        for label, pkey, default in param_defs:
            edit = QLineEdit(params.get(pkey, default))
            edit.textChanged.connect(make_param_handler(pkey, edit))
            layout.addRow(label, edit)
            
        self.content_layout.addWidget(group)
        
    def _build_boolean_form(self, item: BooleanOperationItem):
        """Build form for boolean operation."""
        group, layout = self._create_section("Boolean Operation")
        
        layout.addRow("Operation:", QLabel(item.kind.capitalize()))
        layout.addRow("Input Objects:", QLabel(", ".join(item.inputs)))
        
        self.content_layout.addWidget(group)
        

        
    def _build_bc_item_page(self, key: str):
        self._clear_content()
        name = key.split("_", 1)[1]
        bc = next((b for b in self.project.bc_items if b.name == name), None)
        if not bc:
            self._show_empty_state()
            return
            
        title = QLabel(f"Boundary Condition: {bc.name}")
        title.setStyleSheet("font-size: 16px; font-weight: bold; padding: 4px;")
        self.content_layout.addWidget(title)
        
        # Name Section
        name_group, name_layout = self._create_section("Name")
        name_edit = QLineEdit(bc.name)
        name_layout.addRow("Name:", name_edit)
        
        def on_bc_name_changed(new_name):
            new_name = new_name.strip()
            if not new_name or new_name == bc.name:
                return
            bc.name = new_name
            title.setText(f"Boundary Condition: {bc.name}")
            self.current_node_key = f"bc_{new_name}"
            self.owner.model_builder.rebuild(self.project)
            
        name_edit.editingFinished.connect(lambda: on_bc_name_changed(name_edit.text()))
        self.content_layout.addWidget(name_group)

        # Properties
        from ..physics.registry import get_physics
        bc_type = None
        for phys_name in self.project.selected_physics:
            desc = get_physics(phys_name)
            if desc and hasattr(desc, 'bc_types'):
                for bct in desc.bc_types:
                    if bct.kind == bc.kind:
                        bc_type = bct
                        break
                if bc_type:
                    break

        if bc_type and bc_type.default_props:
            prop_group, prop_layout = self._create_section("Properties")
            for prop_key, default_val in bc_type.default_props.items():
                val_edit = QLineEdit(bc.properties.get(prop_key, default_val))
                label_text = bc_type.prop_labels.get(prop_key, prop_key)
                prop_layout.addRow(f"{label_text}:", val_edit)
                
                def make_bc_updater(key, edit):
                    def update_bc():
                        bc.properties[key] = edit.text()
                    return update_bc
                    
                val_edit.textChanged.connect(make_bc_updater(prop_key, val_edit))
                
            self.content_layout.addWidget(prop_group)

        # Boundary Assignment List (Multiselect)
        dom_group, dom_layout = self._create_section("Boundary Assignment")
        self.bc_list = QListWidget()
        self.bc_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self.bc_list.setStyleSheet(
            "QListWidget::item:selected { background-color: #0078D7; color: white; }"
            "QListWidget::item:selected:!active { background-color: #0078D7; color: white; }"
        )
        self.active_boundary_list = self.bc_list
        
        if self.project.mesh and hasattr(self.project.mesh, 'boundaries'):
            # Collect boundaries already exclusively owned by OTHER bc nodes
            claimed_by_others = set()
            for other_bc in self.project.bc_items:
                if other_bc is not bc:
                    claimed_by_others.update(other_bc.boundaries)
                    
            for bname in self.project.mesh.boundaries.keys():
                item = QListWidgetItem(bname)
                item.setData(Qt.ItemDataRole.UserRole, bname) # Save original to track renames
                
                if bname in claimed_by_others:
                    # Item is locked out by another BC
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsSelectable & ~Qt.ItemFlag.ItemIsEnabled & ~Qt.ItemFlag.ItemIsEditable)
                    item.setForeground(Qt.GlobalColor.gray)
                else:
                    item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)

                self.bc_list.addItem(item)
                if bname in bc.boundaries:
                    item.setSelected(True)
                    
        def on_bc_item_changed(item):
            new_name = item.text()
            old_name = item.data(Qt.ItemDataRole.UserRole)
            if old_name and old_name != new_name:
                if not new_name.strip() or new_name in self.project.mesh.boundaries:
                    item.setText(old_name)  # rollback duplicate or empty
                    return
                # Safely rename in mesh
                if old_name in self.project.mesh.boundaries:
                    self.project.mesh.boundaries[new_name] = self.project.mesh.boundaries.pop(old_name)
                # Track in all bc objects
                for other_bc in self.project.bc_items:
                    if old_name in other_bc.boundaries:
                        other_bc.boundaries.remove(old_name)
                        other_bc.boundaries.append(new_name)
                # Track current selection
                if old_name in self.project.selected_boundaries:
                    self.project.selected_boundaries.remove(old_name)
                    self.project.selected_boundaries.add(new_name)
                # Resave tracking pointer
                item.setData(Qt.ItemDataRole.UserRole, new_name)
                self.owner.log(f"Renamed boundary '{old_name}' to '{new_name}'")

        self.bc_list.itemChanged.connect(on_bc_item_changed)
                    
        def update_bc_boundaries():
            selected_names = [item.text() for item in self.bc_list.selectedItems()]
            bc.boundaries = selected_names
            
            # Since items are locked/unselectable if claimed, we no longer need explicit override stripping here
                            
            self.selectionChanged.emit(set(bc.boundaries))
            
        self.bc_list.itemSelectionChanged.connect(update_bc_boundaries)
        dom_layout.addRow(self.bc_list)
        self.content_layout.addWidget(dom_group)
        
        self.content_layout.addStretch(1)

        if self.project.mesh:
            self.selectionChanged.emit(set(bc.boundaries))
        
        # Emit current selection to update canvas highlighting
        if self.project.selected_boundaries:
            self.selectionChanged.emit(self.project.selected_boundaries)
        

        
    def _build_results_page(self):
        """Build the Results page."""
        self._clear_content()
        
        title = QLabel("Results")
        title.setStyleSheet("font-size: 16px; font-weight: bold; padding: 4px;")
        self.content_layout.addWidget(title)
        
        info = QLabel("Use the ribbon toolbar or right-click to add plots.")
        info.setStyleSheet("color: #666; font-style: italic; padding: 8px;")
        info.setWordWrap(True)
        self.content_layout.addWidget(info)
        self.content_layout.addStretch(1)
        
    def _build_materials_page(self):
        self._clear_content()
        title = QLabel("Materials")
        title.setStyleSheet("font-size: 16px; font-weight: bold; padding: 4px;")
        self.content_layout.addWidget(title)
        info = QLabel("Use the right-click menu in the Model Builder to add materials to the project.")
        info.setStyleSheet("color: #666; font-style: italic; padding: 8px;")
        self.content_layout.addWidget(info)
        self.content_layout.addStretch(1)

    def _build_material_item_page(self, key: str):
        self._clear_content()
        name = key.split("_", 1)[1]
        mat = next((m for m in self.project.materials_list if m.name == name), None)
        if not mat:
            self._show_empty_state()
            return
            
        title = QLabel(f"Material: {mat.name}")
        title.setStyleSheet("font-size: 16px; font-weight: bold; padding: 4px;")
        self.content_layout.addWidget(title)
        
        # Editable name
        name_group, name_layout = self._create_section("Name")
        name_edit = QLineEdit(mat.name)
        name_layout.addRow("Name:", name_edit)
        
        def on_mat_name_changed(new_name):
            new_name = new_name.strip()
            if not new_name or new_name == mat.name:
                return
            mat.name = new_name
            title.setText(f"Material: {mat.name}")
            self.current_node_key = f"mat_{new_name}"
            self.owner.model_builder.rebuild(self.project)
            
        name_edit.editingFinished.connect(lambda: on_mat_name_changed(name_edit.text()))
        self.content_layout.addWidget(name_group)
        
        # Collect all unique domain properties from registered physics
        from ..physics.registry import PHYSICS_REGISTRY
        all_props = {}
        for desc in PHYSICS_REGISTRY.values():
            for dp in desc.domain_properties:
                if dp.key not in all_props:
                    all_props[dp.key] = dp
        
        # Sort properties by label for consistent display
        sorted_props = sorted(all_props.values(), key=lambda p: p.label)
        key_list = [dp.key for dp in sorted_props]

        # Library Selection
        lib_group, lib_layout = self._create_section("Load from Library")
        from ..core.material_library import get_library_material_names, get_material_properties
        
        lib_combo = QComboBox()
        lib_combo.addItems(["-- Select Material --"] + get_library_material_names())
        lib_layout.addRow("Library:", lib_combo)
        
        btn_load = QPushButton("Load Properties")
        def load_from_lib():
            sel = lib_combo.currentText()
            if sel != "-- Select Material --":
                props = get_material_properties(sel)
                mat.properties.update(props)
                # Update table cells in-place
                table.blockSignals(True)
                for r, k in enumerate(key_list):
                    table.item(r, 1).setText(str(mat.properties.get(k, "0.0")))
                table.blockSignals(False)
        btn_load.clicked.connect(load_from_lib)
        lib_layout.addRow("", btn_load)
        self.content_layout.addWidget(lib_group)
        
        # Properties Table
        group, layout = self._create_section("Material Properties")
        
        from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView
        table = QTableWidget(len(sorted_props), 3)
        table.setHorizontalHeaderLabels(["Property", "Value", "Unit"])
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setStretchLastSection(True)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        table.setAlternatingRowColors(True)
        
        # Helper to set rows
        def set_row(r, prop_name, key, default_val, unit):
            item_name = QTableWidgetItem(prop_name)
            item_name.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            table.setItem(r, 0, item_name)
            
            item_val = QTableWidgetItem(str(mat.properties.get(key, default_val)))
            table.setItem(r, 1, item_val)
            
            item_unit = QTableWidgetItem(unit)
            item_unit.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            table.setItem(r, 2, item_unit)
            
        for r, dp in enumerate(sorted_props):
            set_row(r, dp.label, dp.key, dp.default, dp.unit)
        
        def update_mat_from_table(row, col):
            if col == 1: # Value changed
                mat.properties[key_list[row]] = table.item(row, col).text()
                
        table.cellChanged.connect(update_mat_from_table)
        table.setMinimumHeight(150)
        layout.addRow(table)
        self.content_layout.addWidget(group)
        
        # Domain Assignment
        dom_group, dom_layout = self._create_section("Domain Assignment")
        dom_list = QListWidget()
        dom_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        dom_list.setStyleSheet(
            "QListWidget::item:selected { background-color: #0078D7; color: white; }"
            "QListWidget::item:selected:!active { background-color: #0078D7; color: white; }"
        )
        self.active_domain_list = dom_list
        
        # Populate domains (Mocked subdomains, 'All' fallback)
        domains_available = ["All"]
        if self.project.mesh and hasattr(self.project.mesh, 'subdomains') and self.project.mesh.subdomains:
            domains_available = list(self.project.mesh.subdomains.keys())
            
        for dom_name in domains_available:
            item = QListWidgetItem(dom_name)
            dom_list.addItem(item)
            if dom_name in mat.domains:
                item.setSelected(True)
                
        def update_domains():
            mat.domains = [item.text() for item in dom_list.selectedItems()]
            self.domainSelectionChanged.emit(mat.domains)
            
        dom_list.itemSelectionChanged.connect(update_domains)
        dom_layout.addRow(dom_list)
        self.content_layout.addWidget(dom_group)
        
        self.content_layout.addStretch(1)
        
    def _build_physics_feature_page(self, key: str):
        self._clear_content()
        name = key.split("_", 1)[1]
        feat = next((f for f in self.project.physics_features if f.name == name), None)
        if not feat:
            self._show_empty_state()
            return
            
        title = QLabel(f"Physics Feature: {feat.name}")
        title.setStyleSheet("font-size: 16px; font-weight: bold; padding: 4px;")
        self.content_layout.addWidget(title)
        
        group, layout = self._create_section("Properties")

        # Data-driven: look up the FeatureType from the registry
        from ..physics.registry import get_physics
        feat_type = None
        for phys_name in self.project.selected_physics:
            desc = get_physics(phys_name)
            if desc:
                for ft in desc.feature_types:
                    if ft.kind == feat.kind:
                        feat_type = ft
                        break
                if feat_type:
                    break

        # Build a row for each property in the feature
        for prop_key in feat.properties:
            val_edit = QLineEdit(feat.properties.get(prop_key, "0.0"))
            # Use prop_labels from registry if available, otherwise fallback
            if feat_type and prop_key in feat_type.prop_labels:
                display_label = feat_type.prop_labels[prop_key]
            elif feat_type:
                display_label = f"{feat_type.label} ({prop_key})"
            else:
                display_label = prop_key
            layout.addRow(f"{display_label}:", val_edit)

            def make_updater(k, edit):
                def update_feat():
                    feat.properties[k] = edit.text()
                return update_feat

            val_edit.textChanged.connect(make_updater(prop_key, val_edit))
            
        self.content_layout.addWidget(group)
        
        # Domain Assignment
        dom_group, dom_layout = self._create_section("Domain Assignment")
        dom_list = QListWidget()
        dom_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        dom_list.setStyleSheet(
            "QListWidget::item:selected { background-color: #0078D7; color: white; }"
            "QListWidget::item:selected:!active { background-color: #0078D7; color: white; }"
        )
        self.active_domain_list = dom_list
        
        domains_available = ["All"]
        if self.project.mesh and hasattr(self.project.mesh, 'subdomains') and self.project.mesh.subdomains:
            domains_available = list(self.project.mesh.subdomains.keys())
            
        for dom_name in domains_available:
            item = QListWidgetItem(dom_name)
            dom_list.addItem(item)
            if dom_name in feat.domains:
                item.setSelected(True)
                
        def update_feat_domains():
            feat.domains = [item.text() for item in dom_list.selectedItems()]
            self.domainSelectionChanged.emit(feat.domains)
            
        dom_list.itemSelectionChanged.connect(update_feat_domains)
        dom_layout.addRow(dom_list)
        self.content_layout.addWidget(dom_group)
        
        self.content_layout.addStretch(1)
        
    def update_domain_selection(self, context_key: str):
        """Update domain list selection without rebuilding the whole panel UI."""
        if not hasattr(self, 'active_domain_list') or not self.active_domain_list:
            return
        # Guard against deleted C++ object
        try:
            from PyQt6 import sip
            if sip.isdeleted(self.active_domain_list):
                return
        except (ImportError, TypeError):
            pass
        
        # Get domains from model
        domains = []
        if context_key and context_key.startswith("mat_"):
            mat_name = context_key.split("_", 1)[1]
            mat = next((m for m in self.project.materials_list if m.name == mat_name), None)
            if mat: domains = mat.domains
        elif context_key.startswith("physfeat_"):
            feat_name = context_key.split("_", 1)[1]
            feat = next((f for f in self.project.physics_features if f.name == feat_name), None)
            if feat: domains = feat.domains
        
        elif context_key.startswith("bc_"):
            bc_name = context_key.split("_", 1)[1]
            bc_item = next((b for b in self.project.bc_items if b.name == bc_name), None)
            if bc_item: domains = bc_item.boundaries # we use the same list var for both boundaries/domains update here
        
        # Update UI silently
        try:
            self.active_domain_list.blockSignals(True)
            for i in range(self.active_domain_list.count()):
                item = self.active_domain_list.item(i)
                item.setSelected(item.text() in domains)
            self.active_domain_list.blockSignals(False)
        except RuntimeError:
            pass
            
            
    def update_boundary_selection(self, context_key: str):
        """Update boundary list selection without rebuilding the whole panel UI."""
        if not hasattr(self, 'active_boundary_list') or not self.active_boundary_list:
            return
        try:
            from PyQt6 import sip
            if sip.isdeleted(self.active_boundary_list):
                return
        except (ImportError, TypeError):
            pass
            
        boundaries = []
        if context_key and context_key.startswith("bc_"):
            bc_name = context_key.split("_", 1)[1]
            bc_item = next((b for b in self.project.bc_items if b.name == bc_name), None)
            if bc_item: boundaries = bc_item.boundaries
            
        try:
            self.active_boundary_list.blockSignals(True)
            for i in range(self.active_boundary_list.count()):
                item = self.active_boundary_list.item(i)
                item.setSelected(item.text() in boundaries)
            self.active_boundary_list.blockSignals(False)
        except RuntimeError:
            pass
        
    # ==================== PLOT SETTINGS ====================
    
    def show_plot_settings(self, index: int):
        """Show settings for a specific plot."""
        if 0 <= index < len(self.project.plots):
            self.current_plot_index = index
            self.current_node_key = f"__plot_{index}"  # Mark as plot so show_page won't skip
            spec = self.project.plots[index]
            
            self._clear_content()
            
            # Title
            title = QLabel(f"Plot: {spec['name']}")
            title.setStyleSheet("font-size: 16px; font-weight: bold; padding: 4px;")
            self.content_layout.addWidget(title)
            
            # Plot settings
            group, layout = self._create_section("Plot Settings")
            
            self.plot_name = QLineEdit(spec['name'])
            self.plot_name.textChanged.connect(self._update_plot_settings)
            layout.addRow("Name:", self.plot_name)
            
            layout.addRow("Type:", QLabel(spec['type']))
            
            if spec['type'] == 'Surface':
                self.plot_expr = QComboBox()
                self.plot_expr.blockSignals(True)
                # Populate from registry result fields
                from ..physics.registry import get_physics as _get_phys
                expr_items = []
                for pn in self.project.selected_physics:
                    d = _get_phys(pn)
                    if d:
                        for rf in d.result_fields:
                            expr_items.append(rf.label)
                if not expr_items:
                    expr_items = ["V (Potential)"]
                self.plot_expr.addItems(expr_items)
                self.plot_expr.setCurrentText(spec.get('expr', expr_items[0]))
                self.plot_expr.blockSignals(False)
                self.plot_expr.currentTextChanged.connect(self._update_plot_settings)
                layout.addRow("Expression:", self.plot_expr)
                
                self.plot_cmap = QComboBox()
                self.plot_cmap.blockSignals(True)
                self.plot_cmap.addItems(["viridis", "plasma", "inferno", "magma", "cividis", "jet", "rainbow"])
                self.plot_cmap.setCurrentText(spec.get('cmap', 'viridis'))
                self.plot_cmap.blockSignals(False)
                self.plot_cmap.currentTextChanged.connect(self._update_plot_settings)
                layout.addRow("Colormap:", self.plot_cmap)
                
                self.plot_opacity = QDoubleSpinBox()
                self.plot_opacity.setRange(0.0, 1.0)
                self.plot_opacity.setSingleStep(0.1)
                self.plot_opacity.setValue(spec.get('opacity', 1.0))
                self.plot_opacity.valueChanged.connect(self._update_plot_settings)
                layout.addRow("Opacity:", self.plot_opacity)
                
                self.plot_show_edges = QCheckBox("Show Mesh Edges")
                self.plot_show_edges.setChecked(spec.get('show_edges', False))
                self.plot_show_edges.toggled.connect(self._update_plot_settings)
                layout.addRow("", self.plot_show_edges)
                
            elif spec['type'] == 'Arrow':
                self.plot_expr = QComboBox()
                self.plot_expr.blockSignals(True)
                # Populate vector fields from registry
                from ..physics.registry import get_physics as _get_phys2
                vec_items = []
                for pn in self.project.selected_physics:
                    d = _get_phys2(pn)
                    if d:
                        for rf in d.result_fields:
                            if rf.field_type == "vector":
                                vec_items.append(rf.label)
                if not vec_items:
                    vec_items = ["Vector Field"]
                self.plot_expr.addItems(vec_items)
                self.plot_expr.setCurrentText(spec.get('expr', vec_items[0]))
                self.plot_expr.blockSignals(False)
                self.plot_expr.currentTextChanged.connect(self._update_plot_settings)
                layout.addRow("Expression:", self.plot_expr)

            self.content_layout.addWidget(group)

            self._add_nav_sliders()
            self.content_layout.addStretch(1)
    
    def _update_plot_settings(self, *args):
        """Update plot settings in project."""
        if self.current_plot_index is not None and 0 <= self.current_plot_index < len(self.project.plots):
            spec = self.project.plots[self.current_plot_index]
            spec['name'] = self.plot_name.text()
            if spec['type'] == 'Surface':
                spec['expr'] = self.plot_expr.currentText() if hasattr(self, 'plot_expr') else spec.get('expr', 'V (Potential)')
                spec['cmap'] = self.plot_cmap.currentText() if hasattr(self, 'plot_cmap') else spec.get('cmap', 'viridis')
                spec['opacity'] = self.plot_opacity.value() if hasattr(self, 'plot_opacity') else spec.get('opacity', 1.0)
                spec['show_edges'] = self.plot_show_edges.isChecked() if hasattr(self, 'plot_show_edges') else spec.get('show_edges', False)
            elif spec['type'] == 'Arrow':
                spec['expr'] = self.plot_expr.currentText() if hasattr(self, 'plot_expr') else spec.get('expr', 'es.E (Electric Field)')
                
            self.project.update_plot(self.current_plot_index, spec)
            
            # Update the name in the Model Builder tree
            if hasattr(self.owner, 'model_builder') and hasattr(self.owner.model_builder, 'update_item_text'):
                if self.current_node_key:
                    mb_key = self.current_node_key[2:] if self.current_node_key.startswith("__") else self.current_node_key
                    self.owner.model_builder.update_item_text(mb_key, spec['name'])
            
            # Immediately refresh the canvas so changes are visible
            if hasattr(self.owner, 'on_plot_request'):
                self.owner.on_plot_request(spec)

    # ==================== PROBE SETTINGS ====================
    def show_probe_settings(self, index: int):
        if 0 <= index < len(self.project.probes):
            self.current_plot_index = index # Reuse property just for selection state sync
            self.current_node_key = f"__probe_{index}"
            spec = self.project.probes[index]
            
            self._clear_content()
            
            title = QLabel(f"Probe: {spec['name']}")
            title.setStyleSheet("font-size: 16px; font-weight: bold; padding: 4px;")
            self.content_layout.addWidget(title)
            
            group, layout = self._create_section("Probe Settings")
            
            self.probe_name = QLineEdit(spec['name'])
            self.probe_name.textChanged.connect(self._update_probe_settings)
            layout.addRow("Name:", self.probe_name)
            layout.addRow("Type:", QLabel(spec['type']))
            
            self.probe_expr = QComboBox()
            self.probe_expr.blockSignals(True)
            from ..physics.registry import get_physics as _get_phys3
            expr_items = []
            for pn in self.project.selected_physics:
                d = _get_phys3(pn)
                if d:
                    for rf in d.result_fields:
                        expr_items.append(rf.label)
            if not expr_items:
                expr_items = ["V (Potential)"]
            self.probe_expr.addItems(expr_items)
            self.probe_expr.setCurrentText(spec.get('expr', expr_items[0]))
            self.probe_expr.blockSignals(False)
            self.probe_expr.currentTextChanged.connect(self._update_probe_settings)
            layout.addRow("Expression:", self.probe_expr)

            if spec['type'] == 'Point Probe':
                self.probe_x = QDoubleSpinBox(); self.probe_x.setRange(-1e6, 1e6); self.probe_x.setSingleStep(0.1)
                self.probe_x.setValue(spec.get('coord_x', 0.0)); self.probe_x.valueChanged.connect(self._update_probe_settings)
                layout.addRow("X Coordinate [m]:", self.probe_x)

                self.probe_y = QDoubleSpinBox(); self.probe_y.setRange(-1e6, 1e6); self.probe_y.setSingleStep(0.1)
                self.probe_y.setValue(spec.get('coord_y', 0.0)); self.probe_y.valueChanged.connect(self._update_probe_settings)
                layout.addRow("Y Coordinate [m]:", self.probe_y)
                
                if self.project.space_dim == 3:
                    self.probe_z = QDoubleSpinBox(); self.probe_z.setRange(-1e6, 1e6); self.probe_z.setSingleStep(0.1)
                    self.probe_z.setValue(spec.get('coord_z', 0.0)); self.probe_z.valueChanged.connect(self._update_probe_settings)
                    layout.addRow("Z Coordinate [m]:", self.probe_z)

                self.probe_result_lbl = QLabel(f"Result: {spec.get('probe_val', 'N/A')}")
                self.probe_result_lbl.setStyleSheet("font-weight: bold; color: #005a9e; padding-top: 5px;")
                layout.addRow("", self.probe_result_lbl)

            elif spec['type'] == 'Line Probe':
                self.probe_x0 = QDoubleSpinBox(); self.probe_x0.setRange(-1e6, 1e6); self.probe_x0.setSingleStep(0.1)
                self.probe_x0.setValue(spec.get('start_x', -0.5)); self.probe_x0.valueChanged.connect(self._update_probe_settings)
                layout.addRow("Start X [m]:", self.probe_x0)

                self.probe_y0 = QDoubleSpinBox(); self.probe_y0.setRange(-1e6, 1e6); self.probe_y0.setSingleStep(0.1)
                self.probe_y0.setValue(spec.get('start_y', -0.5)); self.probe_y0.valueChanged.connect(self._update_probe_settings)
                layout.addRow("Start Y [m]:", self.probe_y0)

                self.probe_x1 = QDoubleSpinBox(); self.probe_x1.setRange(-1e6, 1e6); self.probe_x1.setSingleStep(0.1)
                self.probe_x1.setValue(spec.get('end_x', 0.5)); self.probe_x1.valueChanged.connect(self._update_probe_settings)
                layout.addRow("End X [m]:", self.probe_x1)

                self.probe_y1 = QDoubleSpinBox(); self.probe_y1.setRange(-1e6, 1e6); self.probe_y1.setSingleStep(0.1)
                self.probe_y1.setValue(spec.get('end_y', 0.5)); self.probe_y1.valueChanged.connect(self._update_probe_settings)
                layout.addRow("End Y [m]:", self.probe_y1)

                if self.project.space_dim == 3:
                    self.probe_z0 = QDoubleSpinBox(); self.probe_z0.setRange(-1e6, 1e6); self.probe_z0.setSingleStep(0.1)
                    self.probe_z0.setValue(spec.get('start_z', -0.5)); self.probe_z0.valueChanged.connect(self._update_probe_settings)
                    layout.addRow("Start Z [m]:", self.probe_z0)

                    self.probe_z1 = QDoubleSpinBox(); self.probe_z1.setRange(-1e6, 1e6); self.probe_z1.setSingleStep(0.1)
                    self.probe_z1.setValue(spec.get('end_z', 0.5)); self.probe_z1.valueChanged.connect(self._update_probe_settings)
                    layout.addRow("End Z [m]:", self.probe_z1)
                    
                self.probe_num_pts = QDoubleSpinBox(); self.probe_num_pts.setRange(2, 10000); self.probe_num_pts.setDecimals(0)
                self.probe_num_pts.setValue(spec.get('num_pts', 100)); self.probe_num_pts.valueChanged.connect(self._update_probe_settings)
                layout.addRow("Nuumber of points:", self.probe_num_pts)

            btn_compute_probe = QPushButton("Evaluate Probe")
            btn_compute_probe.clicked.connect(lambda: getattr(self.owner, 'on_probe_request', lambda x: None)(self.project.probes[self.current_plot_index]))
            layout.addRow("", btn_compute_probe)
            
            self.content_layout.addWidget(group)
            self._add_nav_sliders()
            self.content_layout.addStretch(1)
            
            # Apply defaults to spec if new
            self._update_probe_settings()

    def _update_probe_settings(self, *args):
        if self.current_plot_index is not None and 0 <= self.current_plot_index < len(self.project.probes):
            spec = self.project.probes[self.current_plot_index]
            spec['name'] = self.probe_name.text()
            spec['expr'] = self.probe_expr.currentText()
            
            if spec['type'] == 'Point Probe':
                if hasattr(self, 'probe_x'): spec['coord_x'] = self.probe_x.value()
                if hasattr(self, 'probe_y'): spec['coord_y'] = self.probe_y.value()
                if hasattr(self, 'probe_z'): spec['coord_z'] = self.probe_z.value()
            elif spec['type'] == 'Line Probe':
                if hasattr(self, 'probe_x0'): spec['start_x'] = self.probe_x0.value()
                if hasattr(self, 'probe_y0'): spec['start_y'] = self.probe_y0.value()
                if hasattr(self, 'probe_z0'): spec['start_z'] = self.probe_z0.value()
                if hasattr(self, 'probe_x1'): spec['end_x'] = self.probe_x1.value()
                if hasattr(self, 'probe_y1'): spec['end_y'] = self.probe_y1.value()
                if hasattr(self, 'probe_z1'): spec['end_z'] = self.probe_z1.value()
                if hasattr(self, 'probe_num_pts'): spec['num_pts'] = int(self.probe_num_pts.value())
            
            # Use 'on_probe_request' to render immediately if desired (draws line but doesn't solve)
            if hasattr(self.owner, 'on_probe_request'):
                self.owner.on_probe_request(spec, evaluate=False)
                
            # Update the name in the Model Builder tree
            if hasattr(self.owner, 'model_builder') and hasattr(self.owner.model_builder, 'update_item_text'):
                if self.current_node_key:
                    mb_key = self.current_node_key[2:] if self.current_node_key.startswith("__") else self.current_node_key
                    self.owner.model_builder.update_item_text(mb_key, spec['name'])

    def _add_nav_sliders(self):
        """Helper to append independent Time and Sweep sliders to the current layout."""
        time_vals = self.project.results.get('time_vals', self.project.results.get('times', None)) if self.project.results else None
        sweep_vals = self.project.results.get('sweep_vals', None) if self.project.results else None
        is_sweep = self.project.param_sweep_config.get("enabled", False)
        
        # --- Parametric Sweep Navigator ---
        if is_sweep and sweep_vals and len(sweep_vals) > 1:
            nav_group = QGroupBox("Sweep Navigator")
            nav_layout = QVBoxLayout(nav_group)

            self.sweep_slider = QSlider(Qt.Orientation.Horizontal)
            self.sweep_slider.setMinimum(0)
            self.sweep_slider.setMaximum(len(sweep_vals) - 1)
            
            idx = self.project.current_sweep_index
            if idx < 0 or idx >= len(sweep_vals):
                idx = len(sweep_vals) - 1
            self.sweep_slider.setValue(idx)

            pname = self.project.param_sweep_config.get("parameter", "p")
            self.sweep_nav_label = QLabel(f"{pname} = {sweep_vals[idx]:.4g}  (step {idx + 1}/{len(sweep_vals)})")
            self.sweep_nav_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.sweep_nav_label.setStyleSheet("font-weight: bold; font-size: 13px; padding: 4px;")

            self._nav_sweep_vals = sweep_vals
            self.sweep_slider.valueChanged.connect(self._on_sweep_slider_changed)

            nav_layout.addWidget(self.sweep_nav_label)
            nav_layout.addWidget(self.sweep_slider)

            btn_layout = QHBoxLayout()
            btn_prev = QPushButton("\u25C0 Previous")
            btn_next = QPushButton("Next \u25B6")
            btn_prev.clicked.connect(lambda: self.sweep_slider.setValue(max(0, self.sweep_slider.value() - 1)))
            btn_next.clicked.connect(lambda: self.sweep_slider.setValue(min(len(sweep_vals) - 1, self.sweep_slider.value() + 1)))
            btn_layout.addWidget(btn_prev)
            btn_layout.addWidget(btn_next)
            nav_layout.addLayout(btn_layout)

            self.content_layout.addWidget(nav_group)

        # --- Time Step Navigator ---
        if time_vals and len(time_vals) > 1:
            nav_group = QGroupBox("Time Step Navigator")
            nav_layout = QVBoxLayout(nav_group)

            self.time_slider = QSlider(Qt.Orientation.Horizontal)
            self.time_slider.setMinimum(0)
            self.time_slider.setMaximum(len(time_vals) - 1)
            
            idx = self.project.current_time_index
            if idx < 0 or idx >= len(time_vals):
                idx = len(time_vals) - 1
            self.time_slider.setValue(idx)

            self.time_nav_label = QLabel(f"t = {time_vals[idx]:.4g} s  (step {idx + 1}/{len(time_vals)})")
            self.time_nav_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.time_nav_label.setStyleSheet("font-weight: bold; font-size: 13px; padding: 4px;")

            self._nav_times = time_vals
            self.time_slider.valueChanged.connect(self._on_time_slider_changed)

            nav_layout.addWidget(self.time_nav_label)
            nav_layout.addWidget(self.time_slider)

            btn_layout = QHBoxLayout()
            btn_prev = QPushButton("\u25C0 Previous")
            btn_next = QPushButton("Next \u25B6")
            btn_prev.clicked.connect(lambda: self.time_slider.setValue(max(0, self.time_slider.value() - 1)))
            btn_next.clicked.connect(lambda: self.time_slider.setValue(min(len(time_vals) - 1, self.time_slider.value() + 1)))
            btn_layout.addWidget(btn_prev)
            btn_layout.addWidget(btn_next)
            nav_layout.addLayout(btn_layout)

            self.content_layout.addWidget(nav_group)

    def _on_time_slider_changed(self, value):
        """Update current time index and refresh the active plot."""
        self.project.current_time_index = value
        times = getattr(self, '_nav_times', [])
        if 0 <= value < len(times):
            t_val = times[value]
            self.time_nav_label.setText(f"t = {t_val:.4g} s  (step {value + 1}/{len(times)})")

        # Refresh the currently shown plot/probe
        if self.project.results:
            if getattr(self, 'current_plot_index', None) is not None:
                if self.current_node_key.startswith("__plot_"):
                    idx = self.current_plot_index
                    if 0 <= idx < len(self.project.plots):
                        self.owner.on_plot_request(self.project.plots[idx])
                elif self.current_node_key.startswith("__probe_"):
                    idx = self.current_plot_index
                    if 0 <= idx < len(self.project.probes):
                        self.owner.on_probe_request(self.project.probes[idx], evaluate=False)

    def _on_sweep_slider_changed(self, value):
        """Update current sweep index and refresh the active plot/probe."""
        self.project.current_sweep_index = value
        sweep_vals = getattr(self, '_nav_sweep_vals', [])
        if 0 <= value < len(sweep_vals):
            p_val = sweep_vals[value]
            pname = self.project.param_sweep_config.get("parameter", "p")
            self.sweep_nav_label.setText(f"{pname} = {p_val:.4g}  (step {value + 1}/{len(sweep_vals)})")

        # Refresh the currently shown plot/probe
        if self.project.results:
            if getattr(self, 'current_plot_index', None) is not None:
                if self.current_node_key.startswith("__plot_"):
                    idx = self.current_plot_index
                    if 0 <= idx < len(self.project.plots):
                        self.owner.on_plot_request(self.project.plots[idx])
                elif self.current_node_key.startswith("__probe_"):
                    idx = self.current_plot_index
                    if 0 <= idx < len(self.project.probes):
                        self.owner.on_probe_request(self.project.probes[idx], evaluate=False)
            
    # ==================== GEOMETRY CREATORS ====================
    
    def show_geometry_creator(self, kind: str):
        """Show form to create a new geometry primitive."""
        self._clear_content()
        
        title = QLabel(f"Add {kind.capitalize()}")
        title.setStyleSheet("font-size: 16px; font-weight: bold; padding: 4px;")
        self.content_layout.addWidget(title)
        
        # Name section
        group1, layout1 = self._create_section("Object")
        
        prefix_map = {"rectangle": "r", "disk": "c", "polygon": "poly", "box": "b", "sphere": "sph", "cylinder": "cyl"}
        prefix = prefix_map.get(kind, "obj")
        count = sum(1 for item in self.project.geometry_items if item.name.startswith(prefix))
        
        self.new_geom_name = QLineEdit(f"{prefix}{count+1}")
        layout1.addRow("Name:", self.new_geom_name)
        
        self.content_layout.addWidget(group1)
        
        # Parameters section
        group2, layout2 = self._create_section("Dimensions")
        
        if kind == "rectangle":
            self.new_rect_dx = QLineEdit("1.0")
            self.new_rect_dy = QLineEdit("1.0")
            self.new_rect_cx = QLineEdit("0.0")
            self.new_rect_cy = QLineEdit("0.0")
            layout2.addRow("Width (dx) [m]:", self.new_rect_dx)
            layout2.addRow("Height (dy) [m]:", self.new_rect_dy)
            layout2.addRow("Center X (cx) [m]:", self.new_rect_cx)
            layout2.addRow("Center Y (cy) [m]:", self.new_rect_cy)
        elif kind == "disk":
            self.new_disk_rx = QLineEdit("0.5")
            self.new_disk_ry = QLineEdit("0.5")
            self.new_disk_cx = QLineEdit("0.0")
            self.new_disk_cy = QLineEdit("0.0")
            layout2.addRow("Radius X (rx) [m]:", self.new_disk_rx)
            layout2.addRow("Radius Y (ry) [m]:", self.new_disk_ry)
            layout2.addRow("Center X (cx) [m]:", self.new_disk_cx)
            layout2.addRow("Center Y (cy) [m]:", self.new_disk_cy)
        elif kind == "polygon":
            self.new_poly_pts = QLineEdit("[(0,0), (1,0), (0.5,0.8)]")
            layout2.addRow("Points [m]:", self.new_poly_pts)
        elif kind == "box":
            self.new_box_dx = QLineEdit("1.0")
            self.new_box_dy = QLineEdit("1.0")
            self.new_box_dz = QLineEdit("1.0")
            self.new_box_cx = QLineEdit("0.0")
            self.new_box_cy = QLineEdit("0.0")
            self.new_box_cz = QLineEdit("0.0")
            layout2.addRow("Width (dx) [m]:", self.new_box_dx)
            layout2.addRow("Depth (dy) [m]:", self.new_box_dy)
            layout2.addRow("Height (dz) [m]:", self.new_box_dz)
            layout2.addRow("Center X (cx) [m]:", self.new_box_cx)
            layout2.addRow("Center Y (cy) [m]:", self.new_box_cy)
            layout2.addRow("Center Z (cz) [m]:", self.new_box_cz)
        elif kind == "sphere":
            self.new_sphere_r = QLineEdit("0.5")
            self.new_sphere_cx = QLineEdit("0.0")
            self.new_sphere_cy = QLineEdit("0.0")
            self.new_sphere_cz = QLineEdit("0.0")
            layout2.addRow("Radius (r) [m]:", self.new_sphere_r)
            layout2.addRow("Center X (cx) [m]:", self.new_sphere_cx)
            layout2.addRow("Center Y (cy) [m]:", self.new_sphere_cy)
            layout2.addRow("Center Z (cz) [m]:", self.new_sphere_cz)
        elif kind == "cylinder":
            self.new_cyl_r = QLineEdit("0.2")
            self.new_cyl_h = QLineEdit("1.0")
            self.new_cyl_cx = QLineEdit("0.0")
            self.new_cyl_cy = QLineEdit("0.0")
            self.new_cyl_cz = QLineEdit("0.0")
            layout2.addRow("Radius (r) [m]:", self.new_cyl_r)
            layout2.addRow("Height (h) [m]:", self.new_cyl_h)
            layout2.addRow("Base Center X (cx) [m]:", self.new_cyl_cx)
            layout2.addRow("Base Center Y (cy) [m]:", self.new_cyl_cy)
            layout2.addRow("Base Center Z (cz) [m]:", self.new_cyl_cz)
            
        self.new_geom_kind = kind  # Store for later
        self.content_layout.addWidget(group2)
        
        # Add button
        btn_add = QPushButton(f"Create {kind.capitalize()}")
        btn_add.clicked.connect(self._on_add_primitive)
        self.content_layout.addWidget(btn_add)
        
        self.content_layout.addStretch(1)
        
    def show_boolean_creator(self):
        """Show form to create boolean operation."""
        self._clear_content()
        
        title = QLabel("Add Boolean Operation")
        title.setStyleSheet("font-size: 16px; font-weight: bold; padding: 4px;")
        self.content_layout.addWidget(title)
        
        # Operation section
        group1, layout1 = self._create_section("Operation")
        
        count = len(self.project.boolean_operations)
        self.bool_name = QLineEdit(f"bool{count+1}")
        layout1.addRow("Name:", self.bool_name)
        
        self.bool_kind = QComboBox()
        self.bool_kind.addItems(["union", "difference", "intersection"])
        layout1.addRow("Type:", self.bool_kind)
        
        self.content_layout.addWidget(group1)
        
        # Inputs section
        group2, layout2 = self._create_section("Input Objects")
        
        self.bool_inputs = QListWidget()
        self.bool_inputs.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self._refresh_bool_input_list()
        layout2.addRow(self.bool_inputs)
        
        self.content_layout.addWidget(group2)
        
        # Add button
        btn_add = QPushButton("Create Boolean Operation")
        btn_add.clicked.connect(self._on_add_boolean)
        self.content_layout.addWidget(btn_add)
        
        self.content_layout.addStretch(1)
        
    # ==================== HELPER METHODS ====================
    
    def set_state(self, project: ProjectState):
        """Called when project state changes."""
        self.project = project
        # Refresh current page if applicable
        if self.current_node_key:
            self.show_page(self.current_node_key)
            
        pass
        
    def _on_add_primitive(self):
        """Add the created primitive to the project."""
        name = self.new_geom_name.text().strip()
        if not name or any(g.name == name for g in self.project.geometry_items):
            QMessageBox.warning(self, "Input Error", "Name cannot be empty or a duplicate.")
            return
            
        kind = self.new_geom_kind
        params = {}
        
        if kind == "rectangle":
            params = {
                "dx": self.new_rect_dx.text(),
                "dy": self.new_rect_dy.text(),
                "cx": self.new_rect_cx.text(),
                "cy": self.new_rect_cy.text()
            }
        elif kind == "disk":
            params = {
                "rx": self.new_disk_rx.text(),
                "ry": self.new_disk_ry.text(),
                "cx": self.new_disk_cx.text(),
                "cy": self.new_disk_cy.text()
            }
        elif kind == "polygon":
            params = {"points": self.new_poly_pts.text()}
        elif kind == "box":
            params = {
                "dx": self.new_box_dx.text(),
                "dy": self.new_box_dy.text(),
                "dz": self.new_box_dz.text(),
                "cx": self.new_box_cx.text(),
                "cy": self.new_box_cy.text(),
                "cz": self.new_box_cz.text()
            }
        elif kind == "sphere":
            params = {
                "r": self.new_sphere_r.text(),
                "cx": self.new_sphere_cx.text(),
                "cy": self.new_sphere_cy.text(),
                "cz": self.new_sphere_cz.text()
            }
        elif kind == "cylinder":
            params = {
                "r": self.new_cyl_r.text(),
                "h": self.new_cyl_h.text(),
                "cx": self.new_cyl_cx.text(),
                "cy": self.new_cyl_cy.text(),
                "cz": self.new_cyl_cz.text()
            }
            
        item = GeometryItem(kind=kind, name=name, params=params)
        self.project.add_geometry_item(item)
        self.owner.log(f"Added {kind}: {name}")
        
    def _refresh_bool_input_list(self):
        """Refresh the boolean operation input list."""
        if hasattr(self, 'bool_inputs'):
            self.bool_inputs.clear()
            all_geom_names = [gi.name for gi in self.project.geometry_items] + \
                           [b.name for b in self.project.boolean_operations]
            self.bool_inputs.addItems(all_geom_names)
            
    def _on_add_boolean(self):
        """Add the created boolean operation to the project."""
        name = self.bool_name.text().strip()
        if not name or any(g.name == name for g in self.project.boolean_operations):
            QMessageBox.warning(self, "Input Error", "Name cannot be empty or a duplicate.")
            return
            
        selected_items = self.bool_inputs.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Input Error", "Select at least one input object.")
            return
            
        kind = self.bool_kind.currentText()
        inputs = [item.text() for item in selected_items]
        
        item = BooleanOperationItem(kind=kind, name=name, inputs=inputs)
        self.project.add_boolean_operation(item)
        self.owner.log(f"Added boolean operation: {name}")
