import numpy as np
from PyQt6.QtWidgets import QMainWindow, QVBoxLayout, QWidget
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

class Plot1DWindow(QMainWindow):
    """A floating window to display 1D line plots."""
    def __init__(self, x_data, y_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("1D Plot")
        self.resize(600, 400)
        
        main_widget = QWidget(self)
        layout = QVBoxLayout(main_widget)
        self.setCentralWidget(main_widget)
        
        self.fig = Figure(figsize=(6, 4), dpi=100)
        self.canvas = FigureCanvasQTAgg(self.fig)
        self.ax = self.fig.add_subplot(111)
        
        self.toolbar = NavigationToolbar(self.canvas, self)
        
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        
        # Plot data
        self.ax.plot(x_data, y_data, 'b-', linewidth=2)
        self.ax.grid(True)
        
        self.fig.tight_layout()
        
    def set_labels(self, xlabel: str, ylabel: str):
        self.ax.set_xlabel(xlabel)
        self.ax.set_ylabel(ylabel)
        self.fig.tight_layout()
        self.canvas.draw()
