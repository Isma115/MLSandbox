from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QStackedWidget
)
from PySide6.QtCore import Qt

# Importar las vistas extraídas
from views.regression_view import RegressionView
from views.mlp_view import MLPView
from views.cnn_view import CNNView
from views.transformer_view import TransformerView

class ModelView(QWidget):
    def __init__(self):
        super().__init__()
        
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignTop)
        
        title_label = QLabel("<h1 style='color:#d4d4d4; margin-top:20px;'>Configuración del Modelo</h1>")
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # The selector was removed. The architecture is now automatically shown 
        # based on the memory list selection in the sidebar.
        main_layout.addSpacing(10)
        
        # StackedWidget para el panel de modelo cargado
        self.stack_arch = QStackedWidget()
        
        self.stack_arch.addWidget(RegressionView())
        self.stack_arch.addWidget(MLPView())
        self.stack_arch.addWidget(CNNView())
        self.stack_arch.addWidget(TransformerView())
        
        main_layout.addWidget(self.stack_arch)
        
    def set_active_architecture(self, index: int):
        """Muestra el panel correspondiente según la arquitectura instanciada."""
        self.stack_arch.setCurrentIndex(index)
