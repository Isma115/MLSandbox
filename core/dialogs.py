from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QComboBox, QPushButton, QHBoxLayout,
    QLineEdit, QScrollArea, QWidget, QFormLayout
)
from PySide6.QtCore import Qt
from core.styles import apply_stylesheet

class ModelTypeDialog(QDialog):
    def __init__(self, parent=None, title="Selección de Modelo"):
        super().__init__(parent)
        self.setObjectName("ModelTypeDialog")
        self.setWindowTitle(title)
        self.setFixedSize(380, 160)
        apply_stylesheet(self, "dialogs.qss")
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(12)
        self.combo = QComboBox()
        self.combo.addItems([
            "Regresión",
            "Red Neuronal Densa (MLP)", 
            "Red Convolucional (CNN)", 
            "Transformer",
            "K-Means"
        ])
        layout.addWidget(self.combo)
        
        layout.addSpacing(15)
        
        btn_layout = QHBoxLayout()
        btn_ok = QPushButton("Aceptar")
        self.btn_cancel = QPushButton("Cancelar")
        self.btn_cancel.setProperty("variant", "danger")
        
        btn_ok.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(btn_ok)
        
        layout.addLayout(btn_layout)

    def get_selected_model(self):
        """Devuelve el texto del modelo seleccionado y su índice."""
        return self.combo.currentText(), self.combo.currentIndex()

class ManualInferenceDialog(QDialog):
    def __init__(self, features, parent=None, title="Inferencia Manual"):
        super().__init__(parent)
        self.setObjectName("ManualInferenceDialog")
        self.setWindowTitle(title)
        self.setMinimumWidth(400)
        self.setMaximumHeight(500)
        self.features = features
        apply_stylesheet(self, "dialogs.qss")
        
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)

        # Scroll area for features if there are many
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        self.form_layout = QFormLayout(scroll_content)
        
        self.inputs = {}
        for feature in features:
            line_edit = QLineEdit()
            line_edit.setPlaceholderText(feature)
            self.form_layout.addRow(QLabel(f"{feature}:"), line_edit)
            self.inputs[feature] = line_edit
            
        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setProperty("variant", "danger")
        btn_cancel.clicked.connect(self.reject)
        
        btn_ok = QPushButton("Inferir")
        btn_ok.clicked.connect(self.accept)
        
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_ok)
        main_layout.addLayout(btn_layout)
        
    def get_values(self):
        """Devuelve un diccionario con los valores de las características."""
        return {feature: self.inputs[feature].text().strip() for feature in self.features}
