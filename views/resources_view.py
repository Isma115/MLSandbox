import logging
import os
from dataclasses import dataclass, field
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QListWidget, QListWidgetItem, QFileDialog, QAbstractItemView, QFrame
)
from PySide6.QtCore import Qt


@dataclass
class Resource:
    nombre: str
    tipo: str  # "archivo" o "carpeta"
    ruta: str
    extension: str = ""


class ResourcesView(QWidget):
    def __init__(self):
        super().__init__()

        self.resources: list[Resource] = []

        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignTop)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(12)

        # ── Título ──────────────────────────────────────────────────────────
        title_label = QLabel("Gestión de Recursos")
        title_label.setStyleSheet(
            "color: #d4d4d4; font-size: 22px; font-weight: bold; padding-bottom: 6px;"
        )
        main_layout.addWidget(title_label)

        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("color: #333333;")
        main_layout.addWidget(separator)

        # ── Botones de importación ───────────────────────────────────────────
        import_layout = QHBoxLayout()
        import_layout.setSpacing(8)

        btn_importar_archivo = QPushButton("Importar Archivo")
        btn_importar_archivo.setObjectName("btnImportarArchivo")
        btn_importar_archivo.setCursor(Qt.PointingHandCursor)
        btn_importar_archivo.setStyleSheet(self._btn_style("#404040", "#555555", "#555555"))
        btn_importar_archivo.clicked.connect(self.importar_archivo)
        import_layout.addWidget(btn_importar_archivo)

        btn_importar_carpeta = QPushButton("Importar Carpeta")
        btn_importar_carpeta.setObjectName("btnImportarCarpeta")
        btn_importar_carpeta.setCursor(Qt.PointingHandCursor)
        btn_importar_carpeta.setStyleSheet(self._btn_style("#404040", "#555555", "#555555"))
        btn_importar_carpeta.clicked.connect(self.importar_carpeta)
        import_layout.addWidget(btn_importar_carpeta)

        import_layout.addStretch()
        main_layout.addLayout(import_layout)

        # ── Etiqueta de la lista ────────────────────────────────────────────
        lbl_lista = QLabel("Recursos cargados en memoria:")
        lbl_lista.setStyleSheet("color: #a0a0a0; font-size: 13px;")
        main_layout.addWidget(lbl_lista)

        # ── Lista de recursos ────────────────────────────────────────────────
        self.lista_recursos = QListWidget()
        self.lista_recursos.setSelectionMode(QAbstractItemView.SingleSelection)
        self.lista_recursos.setStyleSheet("""
            QListWidget {
                background-color: #1a1a1a;
                border: 1px solid #333333;
                color: #d4d4d4;
                font-size: 13px;
                padding: 6px;
                border-radius: 0px;
            }
            QListWidget::item {
                padding: 10px 8px;
                border-bottom: 1px solid #2a2a2a;
            }
            QListWidget::item:selected {
                background-color: #333333;
                color: #ffffff;
            }
            QListWidget::item:hover {
                background-color: #252525;
            }
        """)
        main_layout.addWidget(self.lista_recursos)

        # ── Botón eliminar ────────────────────────────────────────────────────
        actions_layout = QHBoxLayout()
        actions_layout.addStretch()

        btn_eliminar = QPushButton("Eliminar seleccionado")
        btn_eliminar.setObjectName("btnEliminar")
        btn_eliminar.setCursor(Qt.PointingHandCursor)
        btn_eliminar.setStyleSheet(self._btn_style("#5a2a2a", "#7a3a3a", "#7a3a3a"))
        btn_eliminar.clicked.connect(self.eliminar_recurso)
        actions_layout.addWidget(btn_eliminar)

        main_layout.addLayout(actions_layout)

    # ── Helpers de estilo ──────────────────────────────────────────────────────

    @staticmethod
    def _btn_style(bg: str, hover: str, border: str) -> str:
        return f"""
            QPushButton {{
                background-color: {bg};
                color: #d4d4d4;
                font-weight: bold;
                border: 1px solid {border};
                border-radius: 0px;
                padding: 9px 18px;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: {hover};
            }}
        """

    # ── Lógica ────────────────────────────────────────────────────────────────

    def importar_archivo(self):
        ruta, _ = QFileDialog.getOpenFileName(
            self,
            "Importar Archivo",
            "",
            "Todos los archivos (*);;CSV (*.csv);;Imágenes (*.png *.jpg *.jpeg *.bmp);;Modelos (*.pkl *.h5 *.pt *.pth);;Texto (*.txt *.json)"
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
