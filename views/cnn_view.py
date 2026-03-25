from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt
from core.styles import apply_stylesheet

class CNNView(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("CNNView")
        apply_stylesheet(self, "cnn_view.qss")
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        title = QLabel("Arquitectura: Red Convolucional (CNN)")
        title.setObjectName("CNNTitle")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        description = QLabel(
            "Filtros Conv2D: 32, 64, 128\n"
            "Capas de Agrupación (Pooling): MaxPooling 2x2\n"
            "Aplanado (Flatten)\n"
            "Densa Final: Softmax / Clasificador"
        )
        description.setObjectName("CNNDescription")
        description.setAlignment(Qt.AlignCenter)
        layout.addWidget(description)
