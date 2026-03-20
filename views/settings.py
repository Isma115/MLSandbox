from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt

class SettingsView(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        
        label = QLabel("<h2 style='color:#d4d4d4; margin-bottom:10px;'>Ajustes</h2><p style='color:#d4d4d4;'>Configuración general de la aplicación.</p>")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
