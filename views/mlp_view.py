from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt
from core.styles import apply_stylesheet

class MLPView(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("MLPView")
        apply_stylesheet(self, "mlp_view.qss")
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        title = QLabel("Arquitectura: Perceptrón Multicapa (MLP)")
        title.setObjectName("MLPTitle")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        description = QLabel(
            "Capas de Entrada: Dinámico según dataset\n"
            "Capas Ocultas: N Layers\n"
            "Capas de Salida: M Clases\n"
            "Función de Activación: ReLU / Sigmoid"
        )
        description.setObjectName("MLPDescription")
        description.setAlignment(Qt.AlignCenter)
        layout.addWidget(description)
