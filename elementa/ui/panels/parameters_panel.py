from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QGroupBox, QFormLayout, QTableWidget, QTableWidgetItem, QHBoxLayout, QPushButton
from PyQt6.QtCore import Qt

class ParametersPanel(QWidget):
    def __init__(self, project, owner, parent=None):
        super().__init__(parent)
        self.project = project
        self.owner = owner
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # Title
        title = QLabel("Parameters")
        title.setStyleSheet("font-size: 16px; font-weight: bold; padding: 4px;")
        self.layout.addWidget(title)
        
        # Parameters section
        group = QGroupBox("Parameters")
        glayout = QFormLayout(group)
        glayout.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        glayout.setFormAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        
        self.tbl_params = QTableWidget()
        self.tbl_params.setColumnCount(2)
        self.tbl_params.setHorizontalHeaderLabels(["Name", "Expression"])
        self.tbl_params.horizontalHeader().setStretchLastSection(True)
        self.tbl_params.itemChanged.connect(self._save_parameters_from_table)
        
        self._refresh_parameters()
        glayout.addRow(self.tbl_params)
        
        btn_layout = QHBoxLayout()
        btn_add = QPushButton("Add")
        btn_del = QPushButton("Remove")
        btn_add.clicked.connect(self._add_param)
        btn_del.clicked.connect(self._del_param)
        btn_layout.addWidget(btn_add)
        btn_layout.addWidget(btn_del)
        btn_layout.addStretch(1)
        
        glayout.addRow(btn_layout)
        self.layout.addWidget(group)
        self.layout.addStretch(1)

    def _refresh_parameters(self):
        self.tbl_params.blockSignals(True)
        self.tbl_params.setRowCount(0)
        for k, v in (self.project.parameters or {}).items():
            r = self.tbl_params.rowCount()
            self.tbl_params.insertRow(r)
            self.tbl_params.setItem(r, 0, QTableWidgetItem(str(k)))
            self.tbl_params.setItem(r, 1, QTableWidgetItem(str(v)))
        self.tbl_params.blockSignals(False)
        
    def _add_param(self):
        r = self.tbl_params.rowCount()
        self.tbl_params.insertRow(r)
        self.tbl_params.setItem(r, 0, QTableWidgetItem(f"p{r+1}"))
        self.tbl_params.setItem(r, 1, QTableWidgetItem("0.0"))
        
    def _del_param(self):
        r = self.tbl_params.currentRow()
        if r >= 0:
            name_item = self.tbl_params.item(r, 0)
            if name_item and self.project.parameters:
                self.project.parameters.pop(name_item.text(), None)
            self.tbl_params.removeRow(r)
            
    def _save_parameters_from_table(self, _=None):
        params = {}
        for r in range(self.tbl_params.rowCount()):
            n_item, v_item = self.tbl_params.item(r, 0), self.tbl_params.item(r, 1)
            if n_item and v_item and n_item.text():
                params[n_item.text().strip()] = v_item.text().strip()
        self.project.parameters = params
