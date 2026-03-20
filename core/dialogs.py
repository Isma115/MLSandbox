from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QComboBox, QPushButton, QHBoxLayout
from PySide6.QtCore import Qt

class ModelTypeDialog(QDialog):
    def __init__(self, parent=None, title="Selección de Modelo"):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedSize(380, 160)
        self.setStyleSheet("""
            QDialog { background-color: #1e1e2e; color: #cdd6f4; }
            QLabel { color: #cdd6f4; font-size: 14px; margin-bottom: 10px; }
            QComboBox { background-color: #313244; color: #cdd6f4; border: 1px solid #45475a; border-radius: 4px; padding: 6px; font-size: 13px; }
            QComboBox::drop-down { border: 0px; }
            QComboBox QAbstractItemView { background-color: #313244; color: #cdd6f4; selection-background-color: #45475a; }
            QPushButton { background-color: #89b4fa; color: #11111b; font-weight: bold; border-radius: 6px; padding: 8px 15px; }
            QPushButton:hover { background-color: #b4befe; }
            QPushButton#btnCancel { background-color: #f38ba8; }
            QPushButton#btnCancel:hover { background-color: #fba2bc; }
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
