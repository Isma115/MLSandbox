from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PySide6.QtCore import Qt, Signal
from core.styles import apply_stylesheet

class HomeView(QWidget):
    crear_clicked = Signal()
    cargar_clicked = Signal()

    def __init__(self):
        super().__init__()
        self.setObjectName("HomeView")
        apply_stylesheet(self, "home_view.qss")
        
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignCenter)
        main_layout.setSpacing(28)
        
        title_label = QLabel("ML Sandbox")
        title_label.setObjectName("HomeTitle")
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        buttons_layout = QHBoxLayout()
        buttons_layout.setAlignment(Qt.AlignCenter)
        buttons_layout.setSpacing(60)
        
        self.btn_crear = QPushButton("+")
        self.btn_crear.setObjectName("HomeCreateButton")
        self.btn_crear.setFixedSize(220, 220)
        self.btn_crear.setCursor(Qt.PointingHandCursor)
        self.btn_crear.clicked.connect(self.crear_clicked.emit)
        buttons_layout.addWidget(self.btn_crear)
        
        self.btn_cargar = QPushButton("CARGAR")
        self.btn_cargar.setObjectName("HomeLoadButton")
        self.btn_cargar.setFixedSize(220, 220)
        self.btn_cargar.setCursor(Qt.PointingHandCursor)
        self.btn_cargar.clicked.connect(self.cargar_clicked.emit)
        buttons_layout.addWidget(self.btn_cargar)
        
        main_layout.addLayout(buttons_layout)
