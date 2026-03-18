from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtWidgets import QToolBar, QWidget, QHBoxLayout, QLabel
from .icon_manager import get_icon


class RibbonToolbar(QToolBar):
    """Static ribbon toolbar with grouped buttons for all categories."""
    
    # Signals for toolbar actions
    # File actions
    newProject = pyqtSignal()
    openProject = pyqtSignal()
    saveProject = pyqtSignal()
    undoAction = pyqtSignal()
    redoAction = pyqtSignal()
    
    # Geometry actions
    addRectangle = pyqtSignal()
    addDisk = pyqtSignal()
    addPolygon = pyqtSignal()
    addBox = pyqtSignal()
    addSphere = pyqtSignal()
    addCylinder = pyqtSignal()
    addBooleanOp = pyqtSignal()
    buildGeometry = pyqtSignal()
    generateMesh = pyqtSignal()
    addPhysics = pyqtSignal()
    computeStudy = pyqtSignal()
    addSurfacePlot = pyqtSignal()
    addArrowPlot = pyqtSignal()
    addPointProbe = pyqtSignal()
    addLineProbe = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__("Ribbon", parent)
        self.setMovable(False)
        # Small icon-only style like COMSOL
        self.setIconSize(QSize(20, 20))
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        
        # Store references to 3D-only actions
        self.actions_3d = []
        self.actions_2d = []
        
        self._create_all_actions()
        self._setup_stylesheet()
        
    def _create_all_actions(self):
        """Create all toolbar actions organized in groups."""
        
        # === FILE GROUP ===
        act = QAction(get_icon("newmodel.png"), "New", self)
        act.setToolTip("New Project")
        act.triggered.connect(self.newProject.emit)
        self.addAction(act)
        
        act = QAction(get_icon("openfile.png"), "Open", self)
        act.setToolTip("Open Project")
        act.triggered.connect(self.openProject.emit)
        self.addAction(act)
        
        act = QAction(get_icon("save.png"), "Save", self)
        act.setToolTip("Save Project")
        act.triggered.connect(self.saveProject.emit)
        self.addAction(act)
        
        act = QAction(QIcon.fromTheme("edit-undo"), "Undo", self)
        act.setToolTip("Undo")
        act.triggered.connect(self.undoAction.emit)
        self.addAction(act)
        
        act = QAction(QIcon.fromTheme("edit-redo"), "Redo", self)
        act.setToolTip("Redo")
        act.triggered.connect(self.redoAction.emit)
        self.addAction(act)
        
        self.addSeparator()
        
        # === GEOMETRY GROUP ===
        # 2D Primitives
        act = QAction(get_icon("rectangle.png"), "Rectangle", self)
        act.setToolTip("Add Rectangle (2D)")
        act.triggered.connect(self.addRectangle.emit)
        self.addAction(act)
        self.actions_2d.append(act)
        
        act = QAction(get_icon("disk.png"), "Disk", self)
        act.setToolTip("Add Disk/Circle (2D)")
        act.triggered.connect(self.addDisk.emit)
        self.addAction(act)
        self.actions_2d.append(act)
        
        act = QAction(get_icon("polygon.png"), "Polygon", self)
        act.setToolTip("Add Polygon (2D)")
        act.triggered.connect(self.addPolygon.emit)
        self.addAction(act)
        self.actions_2d.append(act)
        
        # 3D Primitives
        act = QAction(get_icon("box.png"), "Box", self)
        act.setToolTip("Add Box (3D)")
        act.triggered.connect(self.addBox.emit)
        self.addAction(act)
        self.actions_3d.append(act)
        
        act = QAction(get_icon("sphere.png"), "Sphere", self)
        act.setToolTip("Add Sphere (3D)")
        act.triggered.connect(self.addSphere.emit)
        self.addAction(act)
        self.actions_3d.append(act)
        
        act = QAction(get_icon("cylinder.png"), "Cylinder", self)
        act.setToolTip("Add Cylinder (3D)")
        act.triggered.connect(self.addCylinder.emit)
        self.addAction(act)
        self.actions_3d.append(act)
        
        # Boolean operations
        act = QAction(get_icon("boolean.png"), "Boolean", self)
        act.setToolTip("Boolean Operation (Union/Difference/Intersection)")
        act.triggered.connect(self.addBooleanOp.emit)
        self.addAction(act)
        
        # Build geometry
        act = QAction(get_icon("geometry.png"), "Build", self)
        act.setToolTip("Build All Geometry")
        act.triggered.connect(self.buildGeometry.emit)
        self.addAction(act)
        
        self.addSeparator()
        
        # === MESH GROUP ===
        act = QAction(get_icon("mesh.png"), "Generate", self)
        act.setToolTip("Generate Mesh")
        act.triggered.connect(self.generateMesh.emit)
        self.addAction(act)
        
        self.addSeparator()
        
        # === PHYSICS GROUP ===
        act = QAction(get_icon("physics.png"), "Physics", self)
        act.setToolTip("Add Physics Interface")
        act.triggered.connect(self.addPhysics.emit)
        self.addAction(act)
        
        self.addSeparator()
        
        # === STUDY GROUP ===
        act = QAction(get_icon("solve.png"), "Compute", self)
        act.setToolTip("Compute Study")
        act.triggered.connect(self.computeStudy.emit)
        self.addAction(act)
        
        self.addSeparator()
        
        # === RESULTS GROUP ===
        act = QAction(get_icon("plot_surface.png"), "Surface", self)
        act.setToolTip("Add Surface Plot")
        act.triggered.connect(self.addSurfacePlot.emit)
        self.addAction(act)
        
        act = QAction(get_icon("plot_arrow.png"), "Arrow", self)
        act.setToolTip("Add Arrow Plot")
        act.triggered.connect(self.addArrowPlot.emit)
        self.addAction(act)

        act = QAction(get_icon("probe_point.png"), "Point Probe", self)
        act.setToolTip("Add Point Probe")
        act.triggered.connect(self.addPointProbe.emit)
        self.addAction(act)
        
        act = QAction(get_icon("probe_line.png"), "Line Probe", self)
        act.setToolTip("Add Line Probe")
        act.triggered.connect(self.addLineProbe.emit)
        self.addAction(act)
        
    def _setup_stylesheet(self):
        """Apply COMSOL-like styling to the ribbon."""
        self.setStyleSheet("""
            QToolBar {
                background-color: #f7f7f7;
                border-bottom: 1px solid #d0d0d0;
                spacing: 1px;
                padding: 2px 4px;
            }
            QToolButton {
                background-color: transparent;
                border: 1px solid transparent;
                border-radius: 2px;
                padding: 3px;
                margin: 0px;
            }
            QToolButton:hover {
                background-color: #e5f1fb;
                border: 1px solid #0078d7;
            }
            QToolButton:pressed {
                background-color: #cce4f7;
                border: 1px solid #005a9e;
            }
            QToolButton:checked {
                background-color: #cce8ff;
                border: 1px solid #0078d7;
            }
        """)
        
    def update_for_context(self, node_key: str, space_dim: int = 2):
        """
        Update toolbar state based on selected node and dimensionality.
        Shows/hides 2D vs 3D primitives based on space_dim.
        """
        # Show/hide primitives based on dimensionality
        if space_dim == 2:
            # In 2D mode: show 2D primitives, hide 3D primitives
            for act in self.actions_2d:
                act.setVisible(True)
            for act in self.actions_3d:
                act.setVisible(False)
        else:
            # In 3D mode: hide 2D primitives, show 3D primitives
            for act in self.actions_2d:
                act.setVisible(False)
            for act in self.actions_3d:
                act.setVisible(True)
