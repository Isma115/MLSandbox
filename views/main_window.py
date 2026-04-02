import logging
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QStackedWidget, QTextEdit, QLabel, QSplitter,
    QPushButton, QButtonGroup, QListWidgetItem, QDialog,
    QComboBox, QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction

# Import components from our separated modules
from views.home import HomeView
from views.model_page import ModelView
from views.settings import SettingsView
from views.resources_view import ResourcesView
from core.logger import setup_logging
from core.styles import apply_stylesheet
from core.components import CollapsibleBox

class MainWindow(QMainWindow):
    ROLE_ARCH = Qt.UserRole
    ROLE_BUNDLE = Qt.UserRole + 1
    ROLE_STORAGE = Qt.UserRole + 2
    ROLE_DELETE_TARGET = Qt.UserRole + 3

    def __init__(self):
        super().__init__()
        self.setObjectName("MainWindow")
        self.setWindowTitle("ML Sandbox")
        self.resize(1100, 800)

        apply_stylesheet(self, "app.qss", "main_window.qss")

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
        self.btn_modelos_dropdown = QPushButton("Modelos ►")
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
        lbl_memoria.setObjectName("SidebarMemoryLabel")
        modelos_layout.addWidget(lbl_memoria)

        self.lista_modelos = QListWidget()
        self.lista_modelos.currentItemChanged.connect(self.on_memory_model_selected)
        modelos_layout.addWidget(self.lista_modelos)

        self.btn_eliminar_modelo = QPushButton("Eliminar modelo")
        self.btn_eliminar_modelo.setProperty("is_sub", "true")
        self.btn_eliminar_modelo.setCursor(Qt.PointingHandCursor)
        self.btn_eliminar_modelo.clicked.connect(self.on_eliminar_modelo)
        modelos_layout.addWidget(self.btn_eliminar_modelo)

        sidebar_layout.addWidget(self.modelos_container)
        self._set_modelos_expanded(False)

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
        self.home_view.crear_clicked.connect(self.on_crear_modelo)
        self.home_view.cargar_clicked.connect(self.on_cargar_modelo)
        self.workspace.addWidget(self.home_view)

        self.model_view = ModelView()
        self.workspace.addWidget(self.model_view)
        for index in range(self.model_view.stack_arch.count()):
            view = self.model_view.stack_arch.widget(index)
            if hasattr(view, "bundle_changed"):
                view.bundle_changed.connect(self.on_active_view_bundle_changed)
        
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

        # --- Menu Archivo ---
        archivo_menu = menu_bar.addMenu("Archivo")

        guardar_action = QAction("Guardar modelo", self)
        guardar_action.setShortcut("Ctrl+S")
        guardar_action.triggered.connect(self.on_guardar_modelo)
        archivo_menu.addAction(guardar_action)

        # --- Menu Ver ---
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
        self._update_model_actions_state()

    def toggle_console(self):
        """Alternar visibilidad de la consola."""
        self.console.setVisible(not self.console.isVisible())

    def toggle_modelos(self):
        """Alternar visibilidad del contenedor de modelos."""
        self._set_modelos_expanded(not self.modelos_container.isVisible())

    def _set_modelos_expanded(self, expanded: bool):
        """Sincroniza el estado visual del desplegable de Modelos."""
        self.modelos_container.setVisible(expanded)
        self.btn_modelos_dropdown.setText("Modelos ▼" if expanded else "Modelos ►")

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
            self._set_model_item_data(item, index=index)
            self.lista_modelos.addItem(item)
            self.lista_modelos.setCurrentItem(item)
            self._update_model_actions_state()
            logging.info(f"Modelo creado y añadido a memoria: {model_name}")

    def on_cargar_modelo(self):
        import os
        import joblib
        
        ruta, _ = QFileDialog.getOpenFileName(
            self, "Cargar modelo existente", "",
            "Modelos soportados (*.pkl *.joblib);;Todos los archivos (*)"
        )
        if not ruta:
            return

        try:
            if ruta.endswith((".pkl", ".joblib")):
                bundle = joblib.load(ruta)
                model_obj = bundle.get("model")
                sandbox_model_type = bundle.get("sandbox_model_type")
                
                model_name = "Desconocido"
                index = -1
                
                from sklearn.cluster import KMeans
                from sklearn.linear_model import LinearRegression, Ridge, Lasso, ElasticNet
                from sklearn.neural_network import MLPClassifier, MLPRegressor
                if sandbox_model_type == "kmeans" or isinstance(model_obj, KMeans):
                    model_name = "K-Means"
                    index = 4
                elif sandbox_model_type == "mlp" or isinstance(model_obj, (MLPClassifier, MLPRegressor)):
                    model_name = "Red Neuronal Densa (MLP)"
                    index = 1
                elif sandbox_model_type == "regression" or isinstance(model_obj, (LinearRegression, Ridge, Lasso, ElasticNet)):
                    model_name = "Regresión"
                    index = 0
                
                if index == -1:
                    raise ValueError("Tipo de modelo no reconocido o no soportado para inferencia.")
                
                base_name = os.path.basename(ruta)
                item = QListWidgetItem(f"• {model_name} ({base_name})")
                self._set_model_item_data(
                    item,
                    index=index,
                    bundle=bundle,
                    storage_path=ruta,
                    delete_target=self._resolve_delete_target(ruta),
                )
                self.lista_modelos.addItem(item)
                self.lista_modelos.setCurrentItem(item)
                self._update_model_actions_state()
                logging.info(f"Modelo cargado y añadido a memoria: {model_name}")
            else:
                raise ValueError("Solo se soportan archivos .pkl o .joblib.")
                
        except Exception as exc:
            QMessageBox.critical(self, "Error al cargar", f"Fallo al cargar modelo:\n{exc}")
            logging.error(f"Error cargando modelo: {exc}")

    def on_memory_model_selected(self, current_item, previous_item):
        """Muestra el panel de arquitectura correcto basado en el tipo de modelo seleccionado en la lista."""
        if current_item:
            index = current_item.data(self.ROLE_ARCH)
            bundle = current_item.data(self.ROLE_BUNDLE)
            
            if index is not None:
                self.model_view.set_active_architecture(index, is_new=bundle is None)
                
                # Inyectar el bundle cargado a la vista correspondiente
                view = self.model_view.stack_arch.widget(index)
                if bundle is not None:
                    if hasattr(view, "load_bundle"):
                        view.load_bundle(bundle)
                else:
                    if hasattr(view, "reset_view"):
                        view.reset_view()
                        
                if self.workspace.currentIndex() != 1:
                    self.change_workspace(1)
        else:
            self.model_view.clear_active_model()
        self._update_model_actions_state()

    def on_guardar_modelo(self):
        """Guarda el modelo activo (o uno elegido de memoria) en una carpeta con todos sus recursos."""
        import os
        import json
        import joblib

        # Determinar qué bundle guardar
        bundle = None
        model_label = "modelo"
        target_item = None

        if self.workspace.currentIndex() == 1:
            # Estamos en la vista de modelo — obtener bundle del modelo activo
            current_item = self.lista_modelos.currentItem()
            if current_item is not None:
                arch_index = current_item.data(self.ROLE_ARCH)
                view = self.model_view.stack_arch.widget(arch_index)
                # Intentar obtener bundle desde la vista activa (tiene _bundle)
                if hasattr(view, "_bundle") and view._bundle is not None:
                    bundle = view._bundle
                    model_label = current_item.text().replace("• ", "").split(" (")[0]
                    target_item = current_item
                else:
                    # Puede haberse cargado desde archivo
                    bundle = current_item.data(self.ROLE_BUNDLE)
                    if bundle is not None:
                        model_label = current_item.text().replace("• ", "").split(" (")[0]
                        target_item = current_item

            if bundle is None:
                QMessageBox.warning(
                    self, "Sin modelo",
                    "El modelo activo aun no ha sido entrenado o no tiene datos para guardar."
                )
                return
        else:
            # No estamos en vista de modelo — pedir al usuario que elija
            n_items = self.lista_modelos.count()
            if n_items == 0:
                QMessageBox.information(
                    self, "Sin modelos",
                    "No hay ningun modelo cargado en memoria para guardar."
                )
                return

            # Construir dialogo de seleccion
            dialog = QDialog(self)
            dialog.setObjectName("SaveModelDialog")
            dialog.setWindowTitle("Guardar modelo")
            dialog.setFixedSize(360, 130)
            apply_stylesheet(dialog, "dialogs.qss")
            from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton
            dlg_layout = QVBoxLayout(dialog)
            dlg_layout.setSpacing(10)
            dlg_layout.addWidget(QLabel("Selecciona el modelo a guardar:"))
            combo = QComboBox()
            for i in range(n_items):
                combo.addItem(self.lista_modelos.item(i).text())
            # Preseleccionar el activo si existe
            cur = self.lista_modelos.currentRow()
            if cur >= 0:
                combo.setCurrentIndex(cur)
            dlg_layout.addWidget(combo)
            btn_row = QHBoxLayout()
            btn_row.addStretch()
            btn_cancel = QPushButton("Cancelar")
            btn_ok = QPushButton("Guardar")
            btn_cancel.setProperty("variant", "danger")
            btn_cancel.clicked.connect(dialog.reject)
            btn_ok.clicked.connect(dialog.accept)
            btn_row.addWidget(btn_cancel)
            btn_row.addWidget(btn_ok)
            dlg_layout.addLayout(btn_row)

            if not dialog.exec():
                return

            chosen_index = combo.currentIndex()
            chosen_item = self.lista_modelos.item(chosen_index)
            arch_index = chosen_item.data(self.ROLE_ARCH)
            view = self.model_view.stack_arch.widget(arch_index)

            if hasattr(view, "_bundle") and view._bundle is not None:
                bundle = view._bundle
            else:
                bundle = chosen_item.data(self.ROLE_BUNDLE)

            if bundle is None:
                QMessageBox.warning(
                    self, "Sin datos",
                    "El modelo seleccionado aun no ha sido entrenado o no tiene datos para guardar."
                )
                return

            model_label = chosen_item.text().replace("• ", "").split(" (")[0]
            target_item = chosen_item

        # Pedir carpeta de destino
        carpeta = QFileDialog.getExistingDirectory(
            self, "Selecciona carpeta donde guardar el modelo", ""
        )
        if not carpeta:
            return

        # Crear subcarpeta con nombre del modelo
        safe_name = model_label.lower().replace(" ", "_").replace("(", "").replace(")", "")
        dest = os.path.join(carpeta, safe_name)
        os.makedirs(dest, exist_ok=True)

        try:
            # 1. Guardar bundle (model + scaler + features + label_encoders)
            joblib.dump(bundle, os.path.join(dest, "model.pkl"))

            # 2. Guardar metadatos en JSON
            model_obj = bundle.get("model")
            meta = {
                "tipo": type(model_obj).__name__ if model_obj else "Desconocido",
                "features": bundle.get("features", []),
                "label_encoders": list(bundle.get("label_encoders", {}).keys()),
            }
            if hasattr(model_obj, "coef_"):
                try:
                    meta["coeficientes"] = model_obj.coef_.tolist()
                except Exception:
                    pass
            if hasattr(model_obj, "intercept_"):
                try:
                    meta["intercepto"] = float(model_obj.intercept_)
                except Exception:
                    pass
            if hasattr(model_obj, "cluster_centers_"):
                try:
                    meta["n_clusters"] = int(model_obj.n_clusters)
                    meta["centroides"] = model_obj.cluster_centers_.tolist()
                except Exception:
                    pass
            if "ignored_column" in bundle:
                meta["ignored_column"] = bundle.get("ignored_column")
            if bundle.get("task_type"):
                meta["task_type"] = bundle.get("task_type")
            training_config = bundle.get("training_config", {})
            if training_config:
                meta["training_config"] = training_config
            if hasattr(model_obj, "hidden_layer_sizes"):
                try:
                    meta["hidden_layer_sizes"] = list(model_obj.hidden_layer_sizes)
                except Exception:
                    pass

            with open(os.path.join(dest, "metadata.json"), "w", encoding="utf-8") as f:
                json.dump(meta, f, indent=4, ensure_ascii=False)

            # 3. README
            readme_lines = [
                f"Modelo: {model_label}",
                f"Tipo: {meta['tipo']}",
                f"Features: {', '.join(meta['features'])}",
                "",
                "Archivos:",
                "  model.pkl       - Bundle completo (modelo, scaler, encoders)",
                "  metadata.json   - Metadatos del modelo",
                "",
                "Para cargar el modelo en ML Sandbox usa 'Cargar modelo' y selecciona model.pkl.",
            ]
            with open(os.path.join(dest, "README.txt"), "w", encoding="utf-8") as f:
                f.write("\n".join(readme_lines))

            if target_item is not None:
                self._set_model_item_data(
                    target_item,
                    index=target_item.data(self.ROLE_ARCH),
                    bundle=bundle,
                    storage_path=dest,
                    delete_target=dest,
                )

            logging.info(f"Modelo '{model_label}' guardado en: {dest}")
            QMessageBox.information(
                self, "Guardado",
                f"Modelo guardado correctamente en:\n{dest}"
            )

        except Exception as exc:
            logging.error(f"Error al guardar modelo: {exc}")
            QMessageBox.critical(self, "Error al guardar", f"No se pudo guardar el modelo:\n{exc}")

    def on_active_view_bundle_changed(self, bundle: dict):
        current_item = self.lista_modelos.currentItem()
        if current_item is None:
            return
        self._set_model_item_data(
            current_item,
            index=current_item.data(self.ROLE_ARCH),
            bundle=bundle,
            storage_path=current_item.data(self.ROLE_STORAGE),
            delete_target=current_item.data(self.ROLE_DELETE_TARGET),
        )
        self._promote_item_to_memory_state(current_item)
        self._update_model_actions_state()

    def on_eliminar_modelo(self):
        current_item = self.lista_modelos.currentItem()
        if current_item is None:
            QMessageBox.information(self, "Sin seleccion", "Selecciona un modelo para eliminarlo.")
            return

        from core.dialogs import DeleteModelDialog

        model_name = self._extract_model_name(current_item)
        storage_path = current_item.data(self.ROLE_STORAGE)
        delete_target = current_item.data(self.ROLE_DELETE_TARGET)

        dialog = DeleteModelDialog(model_name, storage_path, parent=self)
        if not dialog.exec():
            return

        mode = dialog.selected_mode()
        if mode == "disk":
            try:
                self._delete_model_storage(delete_target or storage_path)
            except Exception as exc:
                QMessageBox.critical(self, "Error al eliminar", f"No se pudo borrar el modelo:\n{exc}")
                logging.error(f"Error eliminando modelo en disco: {exc}")
                return

        row = self.lista_modelos.row(current_item)
        removed_item = self.lista_modelos.takeItem(row)
        del removed_item

        if self.lista_modelos.count() > 0:
            self.lista_modelos.setCurrentRow(min(row, self.lista_modelos.count() - 1))
        else:
            self.lista_modelos.clearSelection()
            self.model_view.clear_active_model()
            if self.workspace.currentIndex() == 1:
                self.change_workspace(0)

        self._update_model_actions_state()
        logging.info(
            f"Modelo eliminado de memoria: {model_name}"
            + (" y disco." if mode == "disk" else ".")
        )

    def _set_model_item_data(self, item: QListWidgetItem, index: int, bundle=None, storage_path=None, delete_target=None):
        item.setData(self.ROLE_ARCH, index)
        item.setData(self.ROLE_BUNDLE, bundle)
        item.setData(self.ROLE_STORAGE, storage_path)
        item.setData(self.ROLE_DELETE_TARGET, delete_target)

    def _extract_model_name(self, item: QListWidgetItem) -> str:
        return item.text().replace("• ", "").split(" (")[0]

    def _promote_item_to_memory_state(self, item: QListWidgetItem):
        text = item.text()
        if "(Nuevo)" in text:
            item.setText(text.replace("(Nuevo)", "(Memoria)"))

    def _update_model_actions_state(self):
        has_models = self.lista_modelos.count() > 0
        self.btn_eliminar_modelo.setEnabled(has_models)

    def _resolve_delete_target(self, path: str | None) -> str | None:
        import os

        if not path:
            return None
        abs_path = os.path.abspath(path)
        if os.path.isfile(abs_path):
            parent = os.path.dirname(abs_path)
            basename = os.path.basename(abs_path).lower()
            if basename in {"model.pkl", "model.joblib"} and os.path.exists(os.path.join(parent, "metadata.json")):
                return parent
        return abs_path

    def _delete_model_storage(self, path: str | None):
        import os
        import shutil

        if not path:
            raise ValueError("El modelo no tiene una ruta guardada asociada.")
        abs_path = os.path.abspath(path)
        if not os.path.exists(abs_path):
            raise FileNotFoundError(f"La ruta asociada no existe: {abs_path}")
        if os.path.isdir(abs_path):
            shutil.rmtree(abs_path)
        else:
            os.remove(abs_path)
