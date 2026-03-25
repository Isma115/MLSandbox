from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt
from core.styles import apply_stylesheet

class SettingsView(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("SettingsView")
        apply_stylesheet(self, "settings_view.qss")
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        
        title = QLabel("Ajustes")
        title.setObjectName("SettingsTitle")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel("Configuración general de la aplicación.")
        subtitle.setObjectName("SettingsSubtitle")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)
