from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QListWidget, QFrame
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon
from .project_manager import ProjectManager

class WelcomeWindow(QDialog):
    def __init__(self, proj_mgr: ProjectManager, parent=None):
        super().__init__(parent)
        self.proj_mgr = proj_mgr
        self._choice = None
        self.setWindowTitle("Welcome to Elementa")
        self.setMinimumSize(600, 400)

        layout = QHBoxLayout(self)
        
        # Left side (actions)
        left_layout = QVBoxLayout()
        title = QLabel("Elementa")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        
        from .icon_manager import get_icon
        btn_new = QPushButton(get_icon("newmodel.png"), " New Project")
        btn_open = QPushButton(get_icon("openfile.png"), " Open Project...")
        
        icon_size = int(btn_new.fontMetrics().height() * 1.2)
        btn_new.setIconSize(QSize(icon_size, icon_size))
        btn_open.setIconSize(QSize(icon_size, icon_size))

        btn_new.clicked.connect(self._on_new)
        btn_open.clicked.connect(self._on_open)
        
        left_layout.addWidget(title)
        left_layout.addSpacing(20)
        left_layout.addWidget(btn_new)
        left_layout.addWidget(btn_open)
        left_layout.addStretch()
        
        # Right side (recent projects)
        right_layout = QVBoxLayout()
        right_layout.addWidget(QLabel("Recent Projects:"))
        self.recent_list = QListWidget()
        self.recent_list.addItems(self.proj_mgr.recent_projects())
        self.recent_list.itemDoubleClicked.connect(self._on_recent_selected)
        right_layout.addWidget(self.recent_list)

        # Separator
        line = QFrame()
        line.setFrameShape(QFrame.Shape.VLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)

        layout.addLayout(left_layout, 1)
        layout.addWidget(line)
        layout.addLayout(right_layout, 2)
        
    def _on_new(self):
        self._choice = "new"
        self.accept()
        
    def _on_open(self):
        self._choice = "open"
        self.accept()
        
    def _on_recent_selected(self, item):
        self._choice = item.text()
        self.accept()

    def exec_and_get_choice(self):
        self.exec()
        return self._choice

