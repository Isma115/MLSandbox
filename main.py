import sys
import logging
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QStackedWidget, QTextEdit, QLabel, QSplitter,
    QPushButton, QButtonGroup, QListWidgetItem
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QAction

# Import components from our separated modules
from views.home import HomeView
from views.model_page import ModelView
from views.settings import SettingsView
from core.logger import setup_logging

# Estilos basados en una paleta moderna, oscura y elegante (Catppuccin-inspired)
MODERN_STYLE = """
/* Ventana Principal */
QMainWindow {
    background-color: #1e1e2e;
}

/* Divisores (Splitters) */
QSplitter::handle {
    background-color: #313244;
    width: 1px;
    height: 1px;
}

/* Sidebar Container */
#SidebarWidget {
    background-color: #181825;
}

/* Botones Principales Sidebar */
#SidebarWidget QPushButton {
    text-align: left;
    padding: 12px 25px;
    background-color: transparent;
    color: #cdd6f4;
    border: none;
    border-left: 4px solid transparent;
    font-size: 14px;
    outline: none;
}
#SidebarWidget QPushButton:hover {
    background-color: #313244;
}
#SidebarWidget QPushButton:checked {
    color: #89b4fa;
    border-left: 4px solid #89b4fa;
    background-color: #313244;
    font-weight: bold;
}

/* Sub-botones Sidebar */
#SidebarWidget QPushButton[is_sub="true"] {
    padding: 10px 10px 10px 40px;
    font-size: 13px;
    color: #bac2de;
}
#SidebarWidget QPushButton[is_sub="true"]:hover {
    color: #cdd6f4;
    background-color: #313244;
}

/* Lista dinámica de modelos */
#SidebarWidget QListWidget {
    background-color: transparent;
    color: #89b4fa;
    border: none;
    outline: none;
    font-size: 13px;
    padding-left: 35px;
}
#SidebarWidget QListWidget::item {
    padding: 5px 0px;
}
#SidebarWidget QListWidget::item:hover {
    color: #b4befe;
}

/* Área de Trabajo */
QStackedWidget {
    background-color: #1e1e2e;
}

QLabel {
    color: #cdd6f4;
    font-size: 16px;
}

/* Consola */
QTextEdit {
    background-color: #11111b;
    color: #a6e3a1;
    border: none;
    padding: 15px;
    font-family: 'Courier New', monospace;
    font-size: 13px;
    selection-background-color: #45475a;
}

/* Scrollbars Verticales */
QScrollBar:vertical {
    border: none;
    background: #181825;
    width: 12px;
    margin: 0px;
}
QScrollBar::handle:vertical {
    background: #45475a;
    min-height: 25px;
    border-radius: 6px;
}
QScrollBar::handle:vertical:hover {
    background: #585b70;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    border: none;
    background: none;
}
"""

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ML Sandbox")
        self.resize(1100, 800)

        # Aplicar el estilo moderno a la aplicación
        self.setStyleSheet(MODERN_STYLE)

        # Main splitter (Horizontal: Sidebar + Right Panel)
        main_splitter = QSplitter(Qt.Horizontal)
        self.setCentralWidget(main_splitter)

        # 1. Sidebar to navigate between functionalities
        self.sidebar_widget = QWidget()
        self.sidebar_widget.setObjectName("SidebarWidget")
        sidebar_layout = QVBoxLayout(self.sidebar_widget)
        sidebar_layout.setAlignment(Qt.AlignTop)
        sidebar_layout.setContentsMargins(0, 15, 0, 15)
        sidebar_layout.setSpacing(2)

        self.btn_group = QButtonGroup(self)
        self.btn_group.setExclusive(True)

        self.btn_home = QPushButton("Home")
        self.btn_home.setCheckable(True)
        self.btn_home.setCursor(Qt.PointingHandCursor)
        self.btn_home.clicked.connect(lambda: self.change_workspace(0))
        self.btn_group.addButton(self.btn_home)
        sidebar_layout.addWidget(self.btn_home)

        sidebar_layout.addSpacing(15)
        lbl_modelo = QLabel("MODELOS")
        lbl_modelo.setStyleSheet("color: #6c7086; font-size: 11px; font-weight: bold; padding-left: 25px; margin-bottom: 5px;")
        sidebar_layout.addWidget(lbl_modelo)

        self.btn_crear = QPushButton("Crear modelo")
        self.btn_crear.setCheckable(True)
        self.btn_crear.setProperty("is_sub", "true")
        self.btn_crear.setCursor(Qt.PointingHandCursor)
        self.btn_crear.clicked.connect(self.on_crear_modelo)
        self.btn_group.addButton(self.btn_crear)
        sidebar_layout.addWidget(self.btn_crear)

        self.btn_cargar = QPushButton("Cargar modelo")
        self.btn_cargar.setCheckable(True)
        self.btn_cargar.setProperty("is_sub", "true")
        self.btn_cargar.setCursor(Qt.PointingHandCursor)
        self.btn_cargar.clicked.connect(self.on_cargar_modelo)
        self.btn_group.addButton(self.btn_cargar)
        sidebar_layout.addWidget(self.btn_cargar)

        sidebar_layout.addSpacing(5)
        lbl_memoria = QLabel("En memoria:")
        lbl_memoria.setStyleSheet("color: #6c7086; font-size: 11px; padding-left: 40px; margin-bottom: 5px;")
        sidebar_layout.addWidget(lbl_memoria)

        self.lista_modelos = QListWidget()
        self.lista_modelos.currentItemChanged.connect(self.on_memory_model_selected)
        sidebar_layout.addWidget(self.lista_modelos)

        sidebar_layout.addStretch()

        self.btn_ajustes = QPushButton("Ajustes")
        self.btn_ajustes.setCheckable(True)
        self.btn_ajustes.setCursor(Qt.PointingHandCursor)
        self.btn_ajustes.clicked.connect(lambda: self.change_workspace(2))
        self.btn_group.addButton(self.btn_ajustes)
        sidebar_layout.addWidget(self.btn_ajustes)

        main_splitter.addWidget(self.sidebar_widget)

        # Right side splitter (Vertical: Workspace on top + Console below)
        right_splitter = QSplitter(Qt.Vertical)
        main_splitter.addWidget(right_splitter)

        # 2. Workspace Area
        self.workspace = QStackedWidget()
        
        # Carga dinámica de vistas modulares
        self.home_view = HomeView()
        self.workspace.addWidget(self.home_view)

        self.model_view = ModelView()
        self.workspace.addWidget(self.model_view)
        
        self.settings_view = SettingsView()
        self.workspace.addWidget(self.settings_view)

        right_splitter.addWidget(self.workspace)

        # 3. Console Area for application logs
        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setVisible(False)
        right_splitter.addWidget(self.console)
        
        # Menu Bar
        menu_bar = self.menuBar()
        view_menu = menu_bar.addMenu("Ver")
        
        toggle_console_action = QAction("Mostrar/Ocultar Consola", self)
        toggle_console_action.setShortcut("Ctrl+`")
        toggle_console_action.triggered.connect(self.toggle_console)
        view_menu.addAction(toggle_console_action)

        # Adjust initial proportions of the splitters
        main_splitter.setSizes([240, 860])
        right_splitter.setSizes([700, 100])

        # Setup custom logging
        setup_logging(self.console)
        
        # Seleccionar la primera opción por defecto
        self.btn_home.setChecked(True)

    def toggle_console(self):
        """Alternar visibilidad de la consola."""
        self.console.setVisible(not self.console.isVisible())

    def change_workspace(self, index):
        """Changes the active widget in the workspace based on sidebar selection."""
        self.workspace.setCurrentIndex(index)
        nombres = {0: "Home", 1: "Modelo", 2: "Ajustes"}
        logging.info(f"Navegando a la sección: {nombres.get(index, 'Desconocida')}")

    def on_crear_modelo(self):
        from core.dialogs import ModelTypeDialog
        dialog = ModelTypeDialog(self, title="Crear nuevo modelo de IA")
        if dialog.exec():
            model_name, index = dialog.get_selected_model()
            item = QListWidgetItem(f"• {model_name} (Nuevo)")
            item.setData(Qt.UserRole, index)
            self.lista_modelos.addItem(item)
            self.lista_modelos.setCurrentItem(item)
            logging.info(f"Modelo creado y añadido a memoria: {model_name}")

    def on_cargar_modelo(self):
        from core.dialogs import ModelTypeDialog
        dialog = ModelTypeDialog(self, title="Cargar modelo existente")
        if dialog.exec():
            model_name, index = dialog.get_selected_model()
            item = QListWidgetItem(f"• {model_name} (Cargado)")
            item.setData(Qt.UserRole, index)
            self.lista_modelos.addItem(item)
            self.lista_modelos.setCurrentItem(item)
            logging.info(f"Modelo cargado y añadido a memoria: {model_name}")

    def on_memory_model_selected(self, current_item, previous_item):
        """Muestra el panel de arquitectura correcto basado en el tipo de modelo seleccionado en la lista."""
        if current_item:
            index = current_item.data(Qt.UserRole)
            if index is not None:
                self.model_view.set_active_architecture(index)
                if self.workspace.currentIndex() != 1:
                    self.change_workspace(1)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Intentar usar una fuente amigable/moderna globalmente
    font = app.font()
    font.setFamily("Helvetica Neue") # Común en macOS
    font.setPointSize(11)
    app.setFont(font)
    
    window = MainWindow()
    window.showMaximized()
    sys.exit(app.exec())
