from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PySide6.QtCore import Qt

class HomeView(QWidget):
    def __init__(self):
        super().__init__()
        
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignCenter)
        
        title_label = QLabel("<h1 style='color:#d4d4d4; margin-bottom:50px;'>ML Sandbox</h1>")
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # Contenedor horizontal para los botones
        buttons_layout = QHBoxLayout()
        buttons_layout.setAlignment(Qt.AlignCenter)
        buttons_layout.setSpacing(60)
        
        # Estilo para botones cuadrados grises con efecto al hacer hover (adaptados al UI general)
        btn_style_dark = """
        QPushButton {
            background-color: #404040;  /* Gris medio */
            color: #e0e0e0;             /* Texto claro */
            font-weight: normal;
            border-radius: 0px;
        }
        QPushButton:hover {
            background-color: #555555;  /* Gris más claro al hover */
        }
        QPushButton:pressed {
            background-color: #2a2a2a;
        }
        """
        
        # Botón izquierdo: Crear (+)
        self.btn_crear = QPushButton("+")
        self.btn_crear.setFixedSize(220, 220)
        self.btn_crear.setCursor(Qt.PointingHandCursor)
        # Re-usamos el estilo general pero haciéndole overide a la fuente del +
        crear_style = btn_style_dark + "\nQPushButton { font-size: 80px; }"
        self.btn_crear.setStyleSheet(crear_style)
        buttons_layout.addWidget(self.btn_crear)
        
        # Botón derecho: Cargar
        self.btn_cargar = QPushButton("CARGAR")
        self.btn_cargar.setFixedSize(220, 220)
        self.btn_cargar.setCursor(Qt.PointingHandCursor)
        # Re-usamos el estilo general sobreescribiendo el tamaño y peso de la fuente
        cargar_style = btn_style_dark + "\nQPushButton { font-size: 32px; font-weight: bold; font-family: 'Segoe UI', 'Helvetica Neue', sans-serif; }"
        self.btn_cargar.setStyleSheet(cargar_style)
        buttons_layout.addWidget(self.btn_cargar)
        
        main_layout.addLayout(buttons_layout)
