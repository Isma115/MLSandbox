import logging
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QStackedWidget, QTextEdit, QLabel, QSplitter,
    QPushButton, QButtonGroup, QListWidgetItem
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction

# Import components from our separated modules
from views.home import HomeView
from views.model_page import ModelView
from views.settings import SettingsView
from views.resources_view import ResourcesView
from core.logger import setup_logging
from core.styles import MODERN_STYLE

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
        self.btn_modelos_dropdown = QPushButton("Modelos ▼")
        self.btn_modelos_dropdown.setCursor(Qt.PointingHandCursor)
        self.btn_modelos_dropdown.setProperty("is_dropdown", "true")
        self.btn_modelos_dropdown.clicked.connect(self.toggle_modelos)
        sidebar_layout.addWidget(self.btn_modelos_dropdown)

        self.modelos_container = QWidget()
        modelos_layout = QVBoxLayout(self.modelos_container)
        modelos_layout.setContentsMargins(0, 0, 0, 0)
        modelos_layout.setSpacing(2)

        self.btn_crear = QPushButton("Crear modelo")
        self.btn_crear.setCheckable(True)
        self.btn_crear.setProperty("is_sub", "true")
        self.btn_crear.setCursor(Qt.PointingHandCursor)
        self.btn_crear.clicked.connect(self.on_crear_modelo)
        self.btn_group.addButton(self.btn_crear)
        modelos_layout.addWidget(self.btn_crear)

        self.btn_cargar = QPushButton("Cargar modelo")
        self.btn_cargar.setCheckable(True)
        self.btn_cargar.setProperty("is_sub", "true")
        self.btn_cargar.setCursor(Qt.PointingHandCursor)
        self.btn_cargar.clicked.connect(self.on_cargar_modelo)
        self.btn_group.addButton(self.btn_cargar)
        modelos_layout.addWidget(self.btn_cargar)

        modelos_layout.addSpacing(5)
        lbl_memoria = QLabel("En memoria:")
        lbl_memoria.setStyleSheet("color: #d4d4d4; font-size: 11px; padding-left: 40px; margin-bottom: 5px;")
        modelos_layout.addWidget(lbl_memoria)

        self.lista_modelos = QListWidget()
        self.lista_modelos.currentItemChanged.connect(self.on_memory_model_selected)
        modelos_layout.addWidget(self.lista_modelos)

        sidebar_layout.addWidget(self.modelos_container)

        sidebar_layout.addStretch()

        self.btn_recursos = QPushButton("Recursos")
        self.btn_recursos.setCheckable(True)
        self.btn_recursos.setCursor(Qt.PointingHandCursor)
        self.btn_recursos.clicked.connect(lambda: self.change_workspace(2))
        self.btn_group.addButton(self.btn_recursos)
        sidebar_layout.addWidget(self.btn_recursos)

        self.btn_ajustes = QPushButton("Ajustes")
        self.btn_ajustes.setCheckable(True)
        self.btn_ajustes.setCursor(Qt.PointingHandCursor)
        self.btn_ajustes.clicked.connect(lambda: self.change_workspace(3))
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
        
        self.resources_view = ResourcesView()
        self.workspace.addWidget(self.resources_view)
        
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

    def toggle_modelos(self):
        """Alternar visibilidad del contenedor de modelos."""
        is_visible = self.modelos_container.isVisible()
        self.modelos_container.setVisible(not is_visible)
        if is_visible:
            self.btn_modelos_dropdown.setText("Modelos ►")
        else:
            self.btn_modelos_dropdown.setText("Modelos ▼")

    def change_workspace(self, index):
        """Changes the active widget in the workspace based on sidebar selection."""
        self.workspace.setCurrentIndex(index)
        nombres = {0: "Home", 1: "Modelo", 2: "Recursos", 3: "Ajustes"}
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
