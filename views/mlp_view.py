from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt

class MLPView(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        label = QLabel(
            "<h3 style='color:#a6e3a1;'>Arquitectura: Perceptrón Multicapa (MLP)</h3><br>"
            "<p style='color:#bac2de; font-size:15px; text-align:center;'>"
            "Capas de Entrada: Dinámico según dataset<br>"
            "Capas Ocultas: N Layers<br>"
            "Capas de Salida: M Clases<br>"
            "Función de Activación: ReLU / Sigmoid"
            "</p>"
        )
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
