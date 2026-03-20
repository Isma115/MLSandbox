from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt

class TransformerView(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        label_transformer = QLabel(
            "<h3 style='color:#d4d4d4;'>Arquitectura: Transformer</h3><br>"
            "<p style='color:#d4d4d4; font-size:15px; text-align:center;'>"
            "Mecanismos de Atención: Multi-Head Attention<br>"
            "Cabezas (Heads): 8<br>"
            "Bloques del Codificador / Decodificador: 6<br>"
            "Dimensión de Extracción (Embedding): 512"
            "</p>"
        )
        label_transformer.setAlignment(Qt.AlignCenter)
        layout.addWidget(label_transformer)
