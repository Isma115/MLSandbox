import logging
import os
from dataclasses import dataclass
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QListWidget, QListWidgetItem, QFileDialog, QAbstractItemView, QFrame
)
from PySide6.QtCore import Qt
from core.styles import apply_stylesheet


@dataclass
class Resource:
    nombre: str
    tipo: str  # "archivo" o "carpeta"
    ruta: str
    extension: str = ""


class ResourcesView(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("ResourcesView")
        apply_stylesheet(self, "resources_view.qss")

        self.resources: list[Resource] = []

        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignTop)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(12)

        # ── Título ──────────────────────────────────────────────────────────
        title_label = QLabel("Gestión de Recursos")
        title_label.setObjectName("ResourcesTitle")
        main_layout.addWidget(title_label)

        separator = QFrame()
        separator.setObjectName("ResourcesSeparator")
        separator.setFrameShape(QFrame.HLine)
        main_layout.addWidget(separator)

        # ── Botones de importación ───────────────────────────────────────────
        import_layout = QHBoxLayout()
        import_layout.setSpacing(8)

        btn_importar_archivo = QPushButton("Importar Archivo")
        btn_importar_archivo.setObjectName("btnImportarArchivo")
        btn_importar_archivo.setProperty("variant", "primary")
        btn_importar_archivo.setCursor(Qt.PointingHandCursor)
        btn_importar_archivo.clicked.connect(self.importar_archivo)
        import_layout.addWidget(btn_importar_archivo)

        btn_importar_carpeta = QPushButton("Importar Carpeta")
        btn_importar_carpeta.setObjectName("btnImportarCarpeta")
        btn_importar_carpeta.setCursor(Qt.PointingHandCursor)
        btn_importar_carpeta.clicked.connect(self.importar_carpeta)
        import_layout.addWidget(btn_importar_carpeta)

        import_layout.addStretch()
        main_layout.addLayout(import_layout)

        # ── Etiqueta de la lista ────────────────────────────────────────────
        lbl_lista = QLabel("Recursos cargados en memoria:")
        lbl_lista.setObjectName("ResourcesHint")
        main_layout.addWidget(lbl_lista)

        # ── Lista de recursos ────────────────────────────────────────────────
        self.lista_recursos = QListWidget()
        self.lista_recursos.setObjectName("ResourcesList")
        self.lista_recursos.setSelectionMode(QAbstractItemView.SingleSelection)
        main_layout.addWidget(self.lista_recursos)

        # ── Botón eliminar ────────────────────────────────────────────────────
        actions_layout = QHBoxLayout()
        actions_layout.addStretch()

        btn_eliminar = QPushButton("Eliminar seleccionado")
        btn_eliminar.setObjectName("btnEliminar")
        btn_eliminar.setProperty("variant", "danger")
        btn_eliminar.setCursor(Qt.PointingHandCursor)
        btn_eliminar.clicked.connect(self.eliminar_recurso)
        actions_layout.addWidget(btn_eliminar)

        main_layout.addLayout(actions_layout)

    # ── Lógica ────────────────────────────────────────────────────────────────

    def importar_archivo(self):
        ruta, _ = QFileDialog.getOpenFileName(
            self,
            "Importar Archivo",
            "",
            "Todos los archivos (*);;CSV (*.csv);;Imagenes (*.png *.jpg *.jpeg *.bmp);;Modelos (*.pkl *.h5 *.pt *.pth);;Texto (*.txt *.json)"
        )
        if not ruta:
            return

        nombre = os.path.basename(ruta)
        extension = os.path.splitext(nombre)[1].lower()
        recurso = Resource(nombre=nombre, tipo="archivo", ruta=ruta, extension=extension)
        self._añadir_recurso(recurso)
        logging.info(f"Archivo importado: {nombre} ({ruta})")

    def importar_carpeta(self):
        ruta = QFileDialog.getExistingDirectory(
            self,
            "Importar Carpeta",
            ""
        )
        if not ruta:
            return

        nombre = os.path.basename(ruta) or ruta
        recurso = Resource(nombre=nombre, tipo="carpeta", ruta=ruta)
        self._añadir_recurso(recurso)
        logging.info(f"Carpeta importada: {nombre} ({ruta})")

    def _añadir_recurso(self, recurso: Resource):
        # Evitar duplicados por ruta
        for r in self.resources:
            if r.ruta == recurso.ruta:
                logging.warning(f"El recurso ya está cargado: {recurso.nombre}")
                return

        self.resources.append(recurso)

        tipo_tag = "[CARPETA]" if recurso.tipo == "carpeta" else f"[{recurso.extension.upper().lstrip('.') or 'ARCHIVO'}]"
        ruta_corta = recurso.ruta if len(recurso.ruta) <= 60 else "..." + recurso.ruta[-57:]

        item = QListWidgetItem(f"{tipo_tag}  {recurso.nombre}\n   {ruta_corta}")
        item.setData(Qt.UserRole, recurso.ruta)
        self.lista_recursos.addItem(item)

    def eliminar_recurso(self):
        items_sel = self.lista_recursos.selectedItems()
        if not items_sel:
            logging.warning("Ningún recurso seleccionado para eliminar.")
            return

        for item in items_sel:
            ruta = item.data(Qt.UserRole)
            self.resources = [r for r in self.resources if r.ruta != ruta]
            self.lista_recursos.takeItem(self.lista_recursos.row(item))
            logging.info(f"Recurso eliminado de memoria: {ruta}")
