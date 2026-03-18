from PyQt6.QtWidgets import (
    QWizard, QWizardPage, QVBoxLayout, QRadioButton, QGroupBox, QListWidget, QListWidgetItem,
    QComboBox, QFormLayout, QLineEdit, QTableWidget, QPushButton, QFileDialog, QHBoxLayout
)
from PyQt6.QtCore import Qt
from dataclasses import dataclass, field
from typing import List, Dict


@dataclass
class NewProjectSpec:
    name: str = "MyProject"
    #location: str = ""
    space_dim: int = 2
    physics: List[str] = field(default_factory=list)
    study: str = "Stationary"


class NewProjectWizard(QWizard):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("New Project Wizard")
        
        self.page1 = self._create_page1()
        self.page2 = self._create_page2()
        self.page3 = self._create_page3()
        self.page4 = self._create_page4()

        self.addPage(self.page1)
        self.addPage(self.page2)
        self.addPage(self.page3)
        self.addPage(self.page4)

        # Connect physics selection changes to update study types
        self.page3.physics_list.itemSelectionChanged.connect(self._update_study_types)

    def _create_page1(self):
        page = QWizardPage()
        page.setTitle("New Project")
        layout = QFormLayout(page)
        page.name_edit = QLineEdit("MyProject1")
        
        #loc_layout = QHBoxLayout()
        #page.loc_edit = QLineEdit()
        #btn_browse = QPushButton("...")
        #btn_browse.clicked.connect(lambda: self._browse_location(page))
        #loc_layout.addWidget(page.loc_edit)
        #loc_layout.addWidget(btn_browse)

        layout.addRow("Project Name:", page.name_edit)
        #layout.addRow("Save Location:", loc_layout)
        return page
    
    def _create_page2(self):
        page = QWizardPage()
        page.setTitle("Select Space Dimension")
        layout = QVBoxLayout(page)
        group = QGroupBox("Dimensionality")
        group_layout = QVBoxLayout(group)
        page.radio_2d = QRadioButton("2D")
        page.radio_3d = QRadioButton("3D")
        page.radio_2d.setChecked(True)
        group_layout.addWidget(page.radio_2d)
        group_layout.addWidget(page.radio_3d)
        layout.addWidget(group)
        return page

    def _create_page3(self):
        page = QWizardPage()
        page.setTitle("Select Physics")
        layout = QVBoxLayout(page)
        group = QGroupBox("Available Physics Interfaces")
        gl = QVBoxLayout(group)
        page.physics_list = QListWidget()
        page.physics_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)

        # Populate from the physics registry
        from ..physics.registry import get_all_physics_names
        for i, name in enumerate(get_all_physics_names()):
            item = QListWidgetItem(name)
            if i == 0:
                item.setSelected(True)
            page.physics_list.addItem(item)

        gl.addWidget(page.physics_list)
        layout.addWidget(group)
        return page

    def _create_page4(self):
        page = QWizardPage()
        page.setTitle("Select Study Type")
        layout = QVBoxLayout(page)
        group = QGroupBox("Compatible Study Types")
        gl = QVBoxLayout(group)
        page.study_combo = QComboBox()
        # Initially populate based on default selection
        page.study_combo.addItems(["Stationary"])
        gl.addWidget(page.study_combo)
        layout.addWidget(group)
        return page


    def _update_study_types(self):
        """Update study type combo box based on selected physics."""
        from ..physics.registry import get_compatible_study_types
        selected = [item.text() for item in self.page3.physics_list.selectedItems()]
        compatible = get_compatible_study_types(selected)

        current = self.page4.study_combo.currentText()
        self.page4.study_combo.clear()
        self.page4.study_combo.addItems(compatible)

        # Try to preserve the previous selection
        idx = self.page4.study_combo.findText(current)
        if idx >= 0:
            self.page4.study_combo.setCurrentIndex(idx)

    def _browse_location(self, page):
        path, _ = QFileDialog.getSaveFileName(page, "Select Project File", "", "Elementa Project (*.elem)")
        if path:
            page.loc_edit.setText(path)

    def build_spec(self) -> NewProjectSpec:
        return NewProjectSpec(
            name=self.page1.name_edit.text(),
            #location=self.page1.loc_edit.text(),
            space_dim=2 if self.page2.radio_2d.isChecked() else 3,
            physics=[item.text() for item in self.page3.physics_list.selectedItems()],
            study=self.page4.study_combo.currentText()
        )
