from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt

class CNNView(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        label_cnn = QLabel(
            "<h3 style='color:#eba0ac;'>Arquitectura: Red Convolucional (CNN)</h3><br>"
            "<p style='color:#bac2de; font-size:15px; text-align:center;'>"
            "Filtros Conv2D: 32, 64, 128<br>"
            "Capas de Agrupación (Pooling): MaxPooling 2x2<br>"
            "Aplanado (Flatten)<br>"
            "Densa Final: Softmax / Clasificador"
            "</p>"
        )
        label_cnn.setAlignment(Qt.AlignCenter)
        layout.addWidget(label_cnn)
