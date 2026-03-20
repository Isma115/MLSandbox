from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QComboBox, QPushButton, QHBoxLayout
from PySide6.QtCore import Qt

class ModelTypeDialog(QDialog):
    def __init__(self, parent=None, title="Selección de Modelo"):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedSize(380, 160)
        self.setStyleSheet("""
            QDialog { background-color: #1a1a1a; color: #e0e0e0; }
            QLabel { color: #e0e0e0; font-size: 14px; margin-bottom: 10px; }
            QComboBox { background-color: #1a1a1a; color: #e0e0e0; border: 1px solid #333333; border-radius: 0px; padding: 6px; font-size: 13px; }
            QComboBox::drop-down { border: 0px; }
            QComboBox QAbstractItemView { background-color: #1a1a1a; color: #e0e0e0; selection-background-color: #333333; }
            QPushButton { background-color: #404040; color: #e0e0e0; font-weight: bold; border-radius: 0px; padding: 8px 15px; }
            QPushButton:hover { background-color: #555555; }
            QPushButton#btnCancel { background-color: #5a2a2a; }
            QPushButton#btnCancel:hover { background-color: #7a3a3a; }
        """)
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        
        lbl = QLabel("¿Qué tipo de modelo de IA deseas emplear?")
        layout.addWidget(lbl)
        
        self.combo = QComboBox()
        self.combo.addItems([
            "Regresión",
            "Red Neuronal Densa (MLP)", 
            "Red Convolucional (CNN)", 
            "Transformer"
        ])
        layout.addWidget(self.combo)
        
        layout.addSpacing(15)
        
        btn_layout = QHBoxLayout()
        btn_ok = QPushButton("Aceptar")
        self.btn_cancel = QPushButton("Cancelar")
        self.btn_cancel.setObjectName("btnCancel")
        
        btn_ok.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(btn_ok)
        
        layout.addLayout(btn_layout)

    def get_selected_model(self):
        """Devuelve el texto del modelo seleccionado y su índice."""
        return self.combo.currentText(), self.combo.currentIndex()
