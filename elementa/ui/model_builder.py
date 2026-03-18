from PyQt6.QtCore import Qt
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QIcon
from PyQt6.QtWidgets import QTreeView, QMenu
from .icon_manager import get_icon

class ModelBuilder(QTreeView):
    def __init__(self, owner):
        super().__init__()
        self.owner = owner
        self.model = QStandardItemModel()
        self.setModel(self.model)
        self.setHeaderHidden(True)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._on_context)
        self.setDragDropMode(QTreeView.DragDropMode.NoDragDrop)
        self.setStyleSheet("""
            QTreeView {
                font-size: 13px;
                outline: none;
            }
            QTreeView::item {
                padding: 4px;
            }
            QTreeView::item:selected {
                background-color: #005a9e;
                color: white;
            }
        """)

    def rebuild(self, project):
        self.model.clear()
        root = self.model.invisibleRootItem()

        comp_name = project.project_name
        
        root_item = self._create_item(comp_name, "root", get_icon("Elementa.png"))
        root.appendRow(root_item)
        
        # Global Definitions placeholder
        defs_group = self._create_item("Global Definitions", "defs", get_icon("definitions.png")) # Changed to materials since we lack global definition specific icon
        root_item.appendRow(defs_group)
        
        param_item = self._create_item("Parameters", "parameters", get_icon("definitions.png"))
        defs_group.appendRow(param_item)
             
        # Component 1 (or whatever name)
        comp_group = self._create_item("Component 1", "comp", get_icon("Elementa.png"))
        root_item.appendRow(comp_group)
        
        # Geometry Base
        geom_group = self._create_item("Geometry", "geometry", get_icon("geometry.png"))
        comp_group.appendRow(geom_group)
        for gi in project.geometry_items:
            # Primitive visual mappings
            ico = get_icon("geometry.png")
            if gi.kind == "rectangle": ico = get_icon("rectangle.png")
            elif gi.kind == "disk": ico = get_icon("disk.png")
            elif gi.kind == "polygon": ico = get_icon("polygon.png")
            elif gi.kind == "box": ico = get_icon("box.png")
            elif gi.kind == "sphere": ico = get_icon("sphere.png")
            elif gi.kind == "cylinder": ico = get_icon("cylinder.png")
            geom_group.appendRow(self._create_item(f"{gi.name} ({gi.kind})", f"geom_{gi.name}", ico))
        for bo in project.boolean_operations:
            geom_group.appendRow(self._create_item(f"{bo.name} ({bo.kind})", f"geom_{bo.name}", get_icon("boolean.png")))
            
        # Materials
        mat_group = self._create_item("Materials", "materials", get_icon("materials.png"))
        comp_group.appendRow(mat_group)
        for mat in project.materials_list:
            mat_group.appendRow(self._create_item(mat.name, f"mat_{mat.name}", get_icon("materials.png")))
            
        
        # Mesh
        mesh_group = self._create_item("Mesh", "mesh", get_icon("mesh.png"))
        comp_group.appendRow(mesh_group)
        
        # Physics — data-driven from the registry
        phys_group = self._create_item("Physics", "phys", get_icon("physics.png"))
        comp_group.appendRow(phys_group)

        from ..physics.registry import get_physics
        for p in project.selected_physics:
            desc = get_physics(p)
            if desc:
                label = f"{desc.name} ({desc.abbreviation})"
                phys_item = self._create_item(label, f"phys_{desc.abbreviation}", get_icon(desc.icon))
                phys_group.appendRow(phys_item)

                # Render individual boundary condition items
                for bc in project.bc_items:
                    phys_item.appendRow(self._create_item(bc.name, f"bc_{bc.name}", get_icon(desc.icon)))

                # Add feature sub-items that match this physics' feature types
                known_kinds = {ft.kind for ft in desc.feature_types}
                for feat in project.physics_features:
                    if feat.kind in known_kinds:
                        phys_item.appendRow(self._create_item(feat.name, f"physfeat_{feat.name}", get_icon(desc.icon)))
            else:
                # Fallback for unregistered physics names
                phys_item = self._create_item(f"{p}", "physics_generic", get_icon("physics.png"))
                phys_group.appendRow(phys_item)
            
                
        # Study
        study_group = self._create_item("Study", "study", get_icon("study.png"))
        root_item.appendRow(study_group)
        study_step = self._create_item(project.selected_study, "study", get_icon("study.png"))
        study_group.appendRow(study_step)
        
        # Results
        res_group = self._create_item("Results", "results", get_icon("results.png"))
        root_item.appendRow(res_group)
        
        # Plots
        plots_group = self._create_item("Plots", "plots", get_icon("plot.png"))
        res_group.appendRow(plots_group)

        for i, plot in enumerate(project.plots):
             if plot.get("type") == 'Surface':
                 plot_ico = get_icon("plot_surface.png")
             elif plot.get("type") == 'Arrow':
                 plot_ico = get_icon("plot_arrow.png")

             plot_item = self._create_item(plot.get("name", f"Plot {i+1}"), f"plot_{i}", plot_ico)
             plots_group.appendRow(plot_item)

        # Probes
        probes_group = self._create_item("Probes", "probes", get_icon("probe.png"))
        res_group.appendRow(probes_group)
        
        for i, probe in enumerate(project.probes):
             if probe.get("type") == 'Point Probe':
                 probe_ico = get_icon("probe_point.png")
             elif probe.get("type") == 'Line Probe':
                 probe_ico = get_icon("probe_line.png")

             probe_item = self._create_item(probe.get("name", f"Probe {i+1}"), f"probe_{i}", probe_ico)
             probes_group.appendRow(probe_item)

        self.expandAll()

    def _create_item(self, text: str, key: str, icon: QIcon = None):
        item = QStandardItem(text)
        if icon: item.setIcon(icon)
        item.setData(key, Qt.ItemDataRole.UserRole)
        item.setEditable(False)
        return item

    def update_item_text(self, key: str, new_text: str):
        """Find an item by its internal key and update its display text without rebuilding the entire tree."""
        def _search(item):
            if item.data(Qt.ItemDataRole.UserRole) == key:
                item.setText(new_text)
                return True
            for row in range(item.rowCount()):
                if _search(item.child(row)):
                    return True
            return False
            
        root = self.model.invisibleRootItem()
        for i in range(root.rowCount()):
            if _search(root.child(i)):
                break

    def _on_context(self, pos):
        idx = self.indexAt(pos)
        if not idx.isValid(): return
        item = self.model.itemFromIndex(idx)
        key = item.data(Qt.ItemDataRole.UserRole)
        menu = QMenu(self)

        if key == "geometry":
            add_prim_menu = menu.addMenu("Add Primitive")
            
            # 2D Primitives - Only show if 2D
            if self.owner.project.space_dim == 2:
                add_prim_menu.addAction("Rectangle").triggered.connect(lambda: self.owner.property_panel.show_geometry_creator("rectangle"))
                add_prim_menu.addAction("Disk").triggered.connect(lambda: self.owner.property_panel.show_geometry_creator("disk"))
                add_prim_menu.addAction("Polygon").triggered.connect(lambda: self.owner.property_panel.show_geometry_creator("polygon"))
            
            # 3D Primitives - Only show if 3D
            if self.owner.project.space_dim == 3:
                add_prim_menu.addSeparator()
                add_prim_menu.addAction("Box").triggered.connect(lambda: self.owner.property_panel.show_geometry_creator("box"))
                add_prim_menu.addAction("Sphere").triggered.connect(lambda: self.owner.property_panel.show_geometry_creator("sphere"))
                add_prim_menu.addAction("Cylinder").triggered.connect(lambda: self.owner.property_panel.show_geometry_creator("cylinder"))
            
            menu.addAction("Boolean Operation").triggered.connect(self.owner.property_panel.show_boolean_creator)

        if key and key.startswith("geom_"):
            name = key.split("_", 1)[1]
            menu.addAction("Delete").triggered.connect(lambda: getattr(self.owner, 'delete_geometry_item', lambda x: None)(name))

        if key == "materials":
            menu.addAction("Add Blank Material").triggered.connect(self.owner.add_blank_material)

        if key and key.startswith("mat_"):
            name = key.split("_", 1)[1]
            menu.addAction("Delete").triggered.connect(lambda: self.owner.delete_material(name))

        # Context menu for any registered physics node
        if key and key.startswith("phys_"):
            abbr = key.split("_", 1)[1]
            from ..physics.registry import PHYSICS_REGISTRY
            for desc in PHYSICS_REGISTRY.values():
                if desc.abbreviation == abbr:
                    # Boundary conditions sub-menu
                    menu.addSeparator()
                    bc_menu = menu.addMenu("Add Boundary Condition")
                    if hasattr(desc, "bc_types") and desc.bc_types:
                        for bct in desc.bc_types:
                            bc_menu.addAction(bct.label).triggered.connect(
                                lambda checked=False, k=bct.kind: self.owner.add_boundary_condition(k)
                            )
                            
                    # Physics Features
                    menu.addSeparator()
                    for ft in desc.feature_types:
                        menu.addAction(f"Add {ft.label}").triggered.connect(
                            lambda checked=False, k=ft.kind: self.owner.add_physics_feature(k)
                        )

        if key and key.startswith("physfeat_"):
            name = key.split("_", 1)[1]
            menu.addAction("Delete").triggered.connect(lambda: self.owner.delete_physics_feature(name))

        if key and key.startswith("bc_"):
            name = key.split("_", 1)[1]
            menu.addAction("Delete").triggered.connect(lambda: self.owner.delete_boundary_condition(name))

        if key == "mesh":
            menu.addAction("Build All").triggered.connect(self.owner.on_generate_mesh)

        if key == "study":
            menu.addAction("Compute").triggered.connect(self.owner.on_solve)

        if key == "results":
            add_plot_menu = menu.addMenu("Add Plot")
            add_plot_menu.addAction("Surface Plot").triggered.connect(lambda: self.owner.add_plot("Surface"))
            add_plot_menu.addAction("Arrow Plot").triggered.connect(lambda: self.owner.add_plot("Arrow"))

            add_probe_menu = menu.addMenu("Add Probe")
            add_probe_menu.addAction("Point Probe").triggered.connect(lambda: self.owner.add_probe("Point Probe"))
            add_probe_menu.addAction("Line Probe").triggered.connect(lambda: self.owner.add_probe("Line Probe"))

        if key == "plots":
            add_plot_menu = menu.addMenu("Add Plot")
            add_plot_menu.addAction("Surface Plot").triggered.connect(lambda: self.owner.add_plot("Surface"))
            add_plot_menu.addAction("Arrow Plot").triggered.connect(lambda: self.owner.add_plot("Arrow"))
        
        if key == "probes":
            add_probe_menu = menu.addMenu("Add Probe")
            add_probe_menu.addAction("Point Probe").triggered.connect(lambda: self.owner.add_probe("Point Probe"))
            add_probe_menu.addAction("Line Probe").triggered.connect(lambda: self.owner.add_probe("Line Probe"))
        
        if key and key.startswith("probe_"):
            name = key.split("_", 1)[1]
            menu.addAction("Delete").triggered.connect(lambda: self.owner.delete_probe(int(name)))

        if menu.actions():
            menu.exec(self.viewport().mapToGlobal(pos))

