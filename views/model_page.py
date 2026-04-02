from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QStackedWidget
)
from PySide6.QtCore import Qt
from core.styles import apply_stylesheet

# Importar las vistas extraídas
from views.regression_view import RegressionView
from views.kmeans_view import KMeansView
from views.mlp_view import MLPView
from views.cnn_view import CNNView
from views.transformer_view import TransformerView

class ModelView(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("ModelView")
        apply_stylesheet(self, "model_view.qss")

        self.architecture_names = {
            0: "Regresion",
            1: "MLP",
            2: "CNN",
            3: "Transformer",
            4: "K-Means",
        }

        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignTop)

        self.title_label = QLabel()
        self.title_label.setObjectName("ModelViewTitle")
        self.title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.title_label)
        self._update_title()
        
        # The selector was removed. The architecture is now automatically shown 
        # based on the memory list selection in the sidebar.
        main_layout.addSpacing(10)
        
        # StackedWidget para el panel de modelo cargado
        self.stack_arch = QStackedWidget()
        
        self.stack_arch.addWidget(RegressionView())
        self.stack_arch.addWidget(MLPView())
        self.stack_arch.addWidget(CNNView())
        self.stack_arch.addWidget(TransformerView())
        self.stack_arch.addWidget(KMeansView())
        
        # Envolver en un QScrollArea para las pantallas configurables
        from PySide6.QtWidgets import QScrollArea, QFrame
        self.scroll = QScrollArea()
        self.scroll.setObjectName("ModelScrollArea")
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setWidget(self.stack_arch)
        
        main_layout.addWidget(self.scroll)
        
    def set_active_architecture(self, index: int, is_new: bool = False):
        """Muestra el panel correspondiente según la arquitectura instanciada."""
        self.stack_arch.setCurrentIndex(index)
        self._update_title(index=index, is_new=is_new)

    def _update_title(self, index: int | None = None, is_new: bool = False):
        if is_new and index in self.architecture_names:
            title = f"Crear modelo ({self.architecture_names[index]})"
        else:
            title = "Configuración del Modelo"
        self.title_label.setText(title)

    def clear_active_model(self):
        view = self.stack_arch.currentWidget()
        if hasattr(view, "reset_view"):
            view.reset_view()
        self._update_title()
