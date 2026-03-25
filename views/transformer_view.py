from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt
from core.styles import apply_stylesheet

class TransformerView(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("TransformerView")
        apply_stylesheet(self, "transformer_view.qss")
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        title = QLabel("Arquitectura: Transformer")
        title.setObjectName("TransformerTitle")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        description = QLabel(
            "Mecanismos de Atención: Multi-Head Attention\n"
            "Cabezas (Heads): 8\n"
            "Bloques del Codificador / Decodificador: 6\n"
            "Dimensión de Extracción (Embedding): 512"
        )
        description.setObjectName("TransformerDescription")
        description.setAlignment(Qt.AlignCenter)
        layout.addWidget(description)
