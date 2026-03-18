from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QGroupBox, QFormLayout, QLineEdit, QPushButton
from PyQt6.QtCore import Qt

class MeshPanel(QWidget):
    def __init__(self, project, owner, parent=None):
        super().__init__(parent)
        self.project = project
        self.owner = owner
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        title = QLabel("Mesh")
        title.setStyleSheet("font-size: 16px; font-weight: bold; padding: 4px;")
        self.layout.addWidget(title)
        
        group = QGroupBox("Mesh Settings")
        glayout = QFormLayout(group)
        glayout.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        glayout.setFormAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        
        size_edit = QLineEdit(str(getattr(self.project, 'mesh_size', 0.1)))
        size_edit.textChanged.connect(lambda v: setattr(self.project, 'mesh_size', float(v) if v else 0.1))
        glayout.addRow("Element Size [m]:", size_edit)
        
        self.layout.addWidget(group)
        
        btn_build = QPushButton("Generate Mesh")
        btn_build.clicked.connect(self.owner.on_generate_mesh)
        self.layout.addWidget(btn_build)
        
        self.layout.addStretch(1)
