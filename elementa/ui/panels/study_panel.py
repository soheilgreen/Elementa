from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QGroupBox, QFormLayout, QPushButton,
    QDoubleSpinBox, QCheckBox, QComboBox
)
from PyQt6.QtCore import Qt


class StudyPanel(QWidget):
    def __init__(self, project, owner, parent=None):
        super().__init__(parent)
        self.project = project
        self.owner = owner
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        title = QLabel("Study")
        title.setStyleSheet("font-size: 16px; font-weight: bold; padding: 4px;")
        self.layout.addWidget(title)
        
        group = QGroupBox("Study Settings")
        glayout = QFormLayout(group)
        glayout.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        glayout.setFormAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        
        glayout.addRow("Study Type:", QLabel(self.project.selected_study))
        self.layout.addWidget(group)

        # Time-dependent settings (only shown when study type is "Time Dependent")
        if self.project.selected_study == "Time Dependent":
            time_group = QGroupBox("Time Stepping")
            time_layout = QFormLayout(time_group)
            time_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

            tc = self.project.time_config

            self.spin_t_start = QDoubleSpinBox()
            self.spin_t_start.setRange(0.0, 1e12)
            self.spin_t_start.setDecimals(4)
            self.spin_t_start.setValue(tc.get("t_start", 0.0))
            self.spin_t_start.setSuffix(" s")
            self.spin_t_start.valueChanged.connect(self._on_time_changed)

            self.spin_t_end = QDoubleSpinBox()
            self.spin_t_end.setRange(0.0, 1e12)
            self.spin_t_end.setDecimals(4)
            self.spin_t_end.setValue(tc.get("t_end", 1.0))
            self.spin_t_end.setSuffix(" s")
            self.spin_t_end.valueChanged.connect(self._on_time_changed)

            self.spin_dt = QDoubleSpinBox()
            self.spin_dt.setRange(1e-8, 1e12)
            self.spin_dt.setDecimals(6)
            self.spin_dt.setValue(tc.get("dt", 0.1))
            self.spin_dt.setSuffix(" s")
            self.spin_dt.valueChanged.connect(self._on_time_changed)

            time_layout.addRow("Start Time:", self.spin_t_start)
            time_layout.addRow("End Time:", self.spin_t_end)
            time_layout.addRow("Time Step (\u0394t):", self.spin_dt)

            self.layout.addWidget(time_group)

        # Parametric Sweep Settings
        sweep_group = QGroupBox("Parametric Sweep")
        sweep_layout = QFormLayout(sweep_group)
        sweep_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        sc = self.project.param_sweep_config
        self.chk_sweep_enabled = QCheckBox("Enable Parametric Sweep")
        self.chk_sweep_enabled.setChecked(sc.get("enabled", False))
        self.chk_sweep_enabled.toggled.connect(self._on_sweep_changed)
        
        self.combo_sweep_param = QComboBox()
        params = list(self.project.parameters.keys())
        if params:
            self.combo_sweep_param.addItems(params)
            current_p = sc.get("parameter", "")
            if current_p in params:
                self.combo_sweep_param.setCurrentText(current_p)
        else:
            self.combo_sweep_param.addItem("-- No parameters defined --")
            self.combo_sweep_param.setEnabled(False)
            self.chk_sweep_enabled.setEnabled(False)
        self.combo_sweep_param.currentTextChanged.connect(self._on_sweep_changed)
        
        self.spin_sweep_start = QDoubleSpinBox()
        self.spin_sweep_start.setRange(-1e12, 1e12)
        self.spin_sweep_start.setValue(sc.get("start", 0.0))
        self.spin_sweep_start.valueChanged.connect(self._on_sweep_changed)
        
        self.spin_sweep_end = QDoubleSpinBox()
        self.spin_sweep_end.setRange(-1e12, 1e12)
        self.spin_sweep_end.setValue(sc.get("end", 1.0))
        self.spin_sweep_end.valueChanged.connect(self._on_sweep_changed)
        
        self.spin_sweep_step = QDoubleSpinBox()
        self.spin_sweep_step.setRange(1e-6, 1e12)
        self.spin_sweep_step.setValue(sc.get("step", 0.1))
        self.spin_sweep_step.valueChanged.connect(self._on_sweep_changed)
        
        sweep_layout.addRow("", self.chk_sweep_enabled)
        sweep_layout.addRow("Parameter:", self.combo_sweep_param)
        sweep_layout.addRow("Start:", self.spin_sweep_start)
        sweep_layout.addRow("End:", self.spin_sweep_end)
        sweep_layout.addRow("Step:", self.spin_sweep_step)
        
        # Disable inputs if sweep is disabled or no params
        def _update_sweep_ui_state():
            has_params = bool(params)
            sweep_on = self.chk_sweep_enabled.isChecked()
            self.combo_sweep_param.setEnabled(sweep_on and has_params)
            
            inputs_enabled = sweep_on and has_params
            self.spin_sweep_start.setEnabled(inputs_enabled)
            self.spin_sweep_end.setEnabled(inputs_enabled)
            self.spin_sweep_step.setEnabled(inputs_enabled)
        
        self.chk_sweep_enabled.toggled.connect(_update_sweep_ui_state)
        _update_sweep_ui_state()
        self.layout.addWidget(sweep_group)

        btn_compute = QPushButton("Compute")
        btn_compute.clicked.connect(self.owner.on_solve)
        self.layout.addWidget(btn_compute)
        
        self.layout.addStretch(1)

    def _on_time_changed(self):
        """Persist time settings back to project state."""
        self.project.time_config["t_start"] = self.spin_t_start.value()
        self.project.time_config["t_end"] = self.spin_t_end.value()
        self.project.time_config["dt"] = self.spin_dt.value()

    def _on_sweep_changed(self):
        """Persist parametric sweep settings back to project state."""
        self.project.param_sweep_config["enabled"] = self.chk_sweep_enabled.isChecked()
        self.project.param_sweep_config["parameter"] = self.combo_sweep_param.currentText()
        self.project.param_sweep_config["start"] = self.spin_sweep_start.value()
        self.project.param_sweep_config["end"] = self.spin_sweep_end.value()
        self.project.param_sweep_config["step"] = self.spin_sweep_step.value()
