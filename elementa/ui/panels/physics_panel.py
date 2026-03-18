from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QGroupBox, QLineEdit,
    QFormLayout, QComboBox
)
from PyQt6.QtCore import Qt


class PhysicsPanel(QWidget):
    """Generic physics settings panel that builds its form from the registry descriptor."""

    def __init__(self, project, owner, parent=None):
        super().__init__(parent)
        self.project = project
        self.owner = owner
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        from ...physics.registry import get_physics

        # Build a section for each selected physics
        for phys_name in self.project.selected_physics:
            desc = get_physics(phys_name)
            if not desc:
                info = QLabel(f"{phys_name} (not registered)")
                info.setStyleSheet("color: #c00; padding: 8px;")
                self.layout.addWidget(info)
                continue

            title = QLabel(desc.name)
            title.setStyleSheet("font-size: 16px; font-weight: bold; padding: 4px;")
            self.layout.addWidget(title)

            info = QLabel(f"{desc.name} physics is active.")
            info.setStyleSheet("color: #666; padding: 8px;")
            self.layout.addWidget(info)

            # Domain Properties section
            if desc.domain_properties:
                props_group = QGroupBox("Domain Properties")
                props_layout = QVBoxLayout(props_group)

                # Material vs Manual toggle
                source_combo = QComboBox()
                source_combo.addItems(["From Material", "User Defined"])
                use_mat = self.project.physics_config.get("use_material", True)
                source_combo.setCurrentIndex(0 if use_mat else 1)

                toggle_layout = QFormLayout()
                toggle_layout.addRow("Value Source:", source_combo)
                props_layout.addLayout(toggle_layout)

                # Build a form row for each domain property from the descriptor
                form_layout = QFormLayout()
                edits = []
                for dp in desc.domain_properties:
                    edit = QLineEdit(self.project.physics_config.get(dp.key, dp.default))
                    edits.append((dp.key, edit))
                    label_text = dp.label
                    if dp.unit:
                        label_text += f" [{dp.unit}]"
                    form_layout.addRow(f"{label_text}:", edit)

                props_layout.addLayout(form_layout)
                self.layout.addWidget(props_group)

                # Wire up toggle and edit signals
                def make_toggle_handler(combo, edit_list):
                    def handler(idx=None):
                        use = combo.currentIndex() == 0
                        self.project.physics_config["use_material"] = use
                        for _key, ed in edit_list:
                            ed.setEnabled(not use)
                    return handler

                def make_edit_handler(prop_key, edit_widget, combo):
                    def handler(text):
                        if combo.currentIndex() != 0:
                            self.project.physics_config[prop_key] = text
                    return handler

                handler = make_toggle_handler(source_combo, edits)
                source_combo.currentIndexChanged.connect(handler)
                handler()  # initial state

                for dp_key, edit_widget in edits:
                    edit_widget.textChanged.connect(make_edit_handler(dp_key, edit_widget, source_combo))

        self.layout.addStretch(1)
