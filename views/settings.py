from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt

class SettingsView(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        
        label = QLabel("<h2 style='color:#89b4fa; margin-bottom:10px;'>Ajustes</h2><p style='color:#a6adc8;'>Configuración general de la aplicación.</p>")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
