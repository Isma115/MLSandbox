import json
import logging
import os

import joblib
import numpy as np
import pandas as pd
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from PySide6.QtCore import QEvent, QThread, Qt, Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QComboBox,
    QSpinBox,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QHeaderView,
)
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import LabelEncoder, StandardScaler

from core.components import CollapsibleBox
from core.styles import apply_stylesheet, set_dynamic_property

import matplotlib.pyplot as plt


class KMeansTrainingWorker(QThread):
    finished = Signal(object, dict)
    error = Signal(str)
    progress = Signal(int)

    def __init__(
        self,
        df: pd.DataFrame,
        ignored_col: str | None,
        n_clusters: int,
        init_method: str,
        n_init: int,
        max_iter: int,
    ):
        super().__init__()
        self.df = df
        self.ignored_col = ignored_col
        self.n_clusters = n_clusters
        self.init_method = init_method
        self.n_init = n_init
        self.max_iter = max_iter

    def run(self):
        try:
            self.progress.emit(10)
            X = self.df.copy()
            if self.ignored_col and self.ignored_col in X.columns:
                X = X.drop(columns=[self.ignored_col])

            if X.empty:
                self.error.emit("El dataset no contiene columnas disponibles para entrenar.")
                return

            if len(X) < self.n_clusters:
                self.error.emit("El numero de clusters no puede ser mayor que el numero de muestras.")
                return

            label_encoders = {}
            self.progress.emit(30)
            for col in X.columns:
                if X[col].dtype == "object" or str(X[col].dtype) in {"category", "string"}:
                    encoder = LabelEncoder()
                    X[col] = encoder.fit_transform(X[col].astype(str))
                    label_encoders[col] = encoder
                else:
                    X[col] = pd.to_numeric(X[col], errors="coerce")

            X = X.fillna(0)
            scaler = StandardScaler()
            self.progress.emit(55)
            X_scaled = scaler.fit_transform(X)

            model = KMeans(
                n_clusters=self.n_clusters,
                init=self.init_method,
                n_init=self.n_init,
                max_iter=self.max_iter,
                random_state=42,
            )
            labels = model.fit_predict(X_scaled)

            self.progress.emit(80)
            distances = model.transform(X_scaled)
            assigned_distances = distances[np.arange(len(labels)), labels]

            cluster_sizes = {}
            cluster_distance_reference = {}
            for cluster_id in range(self.n_clusters):
                cluster_distances = assigned_distances[labels == cluster_id]
                cluster_sizes[cluster_id] = int(cluster_distances.size)
                if cluster_distances.size:
                    ref = float(np.percentile(cluster_distances, 90))
                    if not np.isfinite(ref) or ref <= 0:
                        ref = float(np.max(cluster_distances)) if cluster_distances.size else 1.0
                    cluster_distance_reference[cluster_id] = max(ref, 1e-6)
                else:
                    cluster_distance_reference[cluster_id] = 1.0

            silhouette = None
            unique_labels = np.unique(labels)
            if self.n_clusters > 1 and unique_labels.size > 1 and len(X_scaled) > unique_labels.size:
                silhouette = float(silhouette_score(X_scaled, labels))

            if silhouette is None:
                quality_score = 0.55
            else:
                quality_score = float(np.clip((silhouette + 1.0) / 2.0, 0.05, 0.98))

            metrics = {
                "n_samples": int(len(X)),
                "n_features": int(X.shape[1]),
                "n_clusters": int(self.n_clusters),
                "inertia": float(model.inertia_),
                "silhouette": silhouette,
                "cluster_sizes": cluster_sizes,
                "quality_score": quality_score,
            }

            bundle = {
                "sandbox_model_type": "kmeans",
                "model": model,
                "scaler": scaler,
                "features": list(X.columns),
                "label_encoders": label_encoders,
                "ignored_column": self.ignored_col,
                "confidence_stats": {
                    "cluster_distance_reference": cluster_distance_reference,
                    "quality_score": quality_score,
                },
            }
            self.progress.emit(100)
            self.finished.emit(bundle, metrics)
        except Exception as exc:
            self.error.emit(str(exc))


class KMeansView(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("KMeansView")
        apply_stylesheet(self, "kmeans_view.qss")

        self._bundle = None
        self._df = None
        self._last_metrics = None

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(16)

        self.train_box = CollapsibleBox("1. Entrenamiento de Modelo")
        root.addWidget(self.train_box)

        row1 = QHBoxLayout()
        self.ds_input = QLineEdit()
        self.ds_input.setPlaceholderText("Cargar dataset...")
        self.ds_input.setReadOnly(True)
        btn_browse = QPushButton("Explorar")
        btn_browse.setCursor(Qt.PointingHandCursor)
        btn_browse.clicked.connect(self._browse_dataset)
        row1.addWidget(btn_browse)
        row1.addWidget(self.ds_input)
        self.train_box.add_layout(row1)

        row2 = QHBoxLayout()
        lbl_ignore = QLabel("Columna a ignorar:")
        lbl_ignore.setFixedWidth(170)
        self.combo_ignore = QComboBox()
        self.combo_ignore.setEnabled(False)
        row2.addWidget(lbl_ignore)
        row2.addWidget(self.combo_ignore)
        row2.addStretch()
        self.train_box.add_layout(row2)

        row3 = QHBoxLayout()

        lbl_clusters = QLabel("Clusters:")
        lbl_clusters.setFixedWidth(85)
        self.btn_clusters_info = self._create_info_button(
            "Informacion sobre numero de clusters",
            self._show_clusters_info,
        )
        self.spin_clusters = QSpinBox()
        self.spin_clusters.setRange(1, 100)
        self.spin_clusters.setValue(3)

        lbl_init = QLabel("Inicializacion:")
        lbl_init.setFixedWidth(105)
        self.btn_init_info = self._create_info_button(
            "Informacion sobre inicializacion",
            self._show_init_info,
        )
        self.combo_init = QComboBox()
        self.combo_init.addItems(["k-means++", "random"])

        lbl_n_init = QLabel("Reintentos:")
        lbl_n_init.setFixedWidth(90)
        self.spin_n_init = QSpinBox()
        self.spin_n_init.setRange(1, 100)
        self.spin_n_init.setValue(10)

        lbl_iter = QLabel("Max iter:")
        lbl_iter.setFixedWidth(75)
        self.btn_iter_info = self._create_info_button(
            "Informacion sobre iteraciones maximas",
            self._show_max_iter_info,
        )
        self.spin_max_iter = QSpinBox()
        self.spin_max_iter.setRange(10, 5000)
        self.spin_max_iter.setValue(300)
        self.spin_max_iter.setSingleStep(10)

        row3.addWidget(lbl_clusters)
        row3.addWidget(self.btn_clusters_info)
        row3.addWidget(self.spin_clusters)
        row3.addSpacing(18)
        row3.addWidget(lbl_init)
        row3.addWidget(self.btn_init_info)
        row3.addWidget(self.combo_init)
        row3.addSpacing(18)
        row3.addWidget(lbl_n_init)
        row3.addWidget(self.spin_n_init)
        row3.addSpacing(18)
        row3.addWidget(lbl_iter)
        row3.addWidget(self.btn_iter_info)
        row3.addWidget(self.spin_max_iter)
        row3.addStretch()
        self.train_box.add_layout(row3)

        actions_row = QHBoxLayout()
        self.btn_train = QPushButton("Entrenar")
        self.btn_train.setProperty("variant", "primary")
        self.btn_train.setCursor(Qt.PointingHandCursor)
        self.btn_train.clicked.connect(self._on_train)
        actions_row.addWidget(self.btn_train)
        actions_row.addStretch()
        self.train_box.add_layout(actions_row)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setTextVisible(False)
        self.train_box.add_widget(self.progress_bar)

        self.inf_box = CollapsibleBox("2. Inferencia y Pruebas")
        root.addWidget(self.inf_box)

        inf_layout = QVBoxLayout()
        inf_layout.setSpacing(8)

        row_inf = QHBoxLayout()
        self.inf_input = QLineEdit()
        self.inf_input.setPlaceholderText("Sin CSV...")
        self.inf_input.setReadOnly(True)
        btn_inf_browse = QPushButton("Explorar")
        btn_inf_browse.setCursor(Qt.PointingHandCursor)
        btn_inf_browse.clicked.connect(self._browse_inference)

        self.btn_infer = QPushButton("Inferir CSV")
        self.btn_infer.setCursor(Qt.PointingHandCursor)
        self.btn_infer.setEnabled(False)
        self.btn_infer.clicked.connect(self._on_infer)

        row_inf.addWidget(btn_inf_browse)
        row_inf.addWidget(self.btn_infer)
        row_inf.addWidget(self.inf_input)
        inf_layout.addLayout(row_inf)

        self.btn_infer_manual = QPushButton("Inferencia Manual")
        self.btn_infer_manual.setCursor(Qt.PointingHandCursor)
        self.btn_infer_manual.setEnabled(False)
        self.btn_infer_manual.clicked.connect(self._on_infer_manual)
        inf_layout.addWidget(self.btn_infer_manual)

        self.inf_table = QTableWidget(0, 3)
        self.inf_table.setObjectName("InferenceTable")
        self.inf_table.setHorizontalHeaderLabels(["Muestra", "Cluster", "% Seguridad"])
        self.inf_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.inf_table.setFixedHeight(160)
        inf_layout.addWidget(self.inf_table)

        self.inf_box.add_layout(inf_layout)

        self.datos_box = CollapsibleBox("3. Muestras de Datos")
        root.addWidget(self.datos_box)

        datos_layout = QVBoxLayout()
        datos_layout.setSpacing(8)

        row_datos_controls = QHBoxLayout()
        lbl_n = QLabel("Muestras:")
        lbl_n.setFixedWidth(65)
        self.spin_samples = QSpinBox()
        self.spin_samples.setRange(1, 10000)
        self.spin_samples.setValue(50)
        self.spin_samples.valueChanged.connect(self._populate_samples)

        lbl_search = QLabel("Buscar:")
        lbl_search.setFixedWidth(55)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Filtrar...")
        self.search_input.textChanged.connect(self._filter_samples)

        row_datos_controls.addWidget(lbl_n)
        row_datos_controls.addWidget(self.spin_samples)
        row_datos_controls.addSpacing(20)
        row_datos_controls.addWidget(lbl_search)
        row_datos_controls.addWidget(self.search_input)
        datos_layout.addLayout(row_datos_controls)

        self.samples_table = QTableWidget(0, 0)
        self.samples_table.setObjectName("SamplesTable")
        self.samples_table.setMinimumHeight(200)
        self.samples_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.samples_table.setEditTriggers(QTableWidget.NoEditTriggers)
        datos_layout.addWidget(self.samples_table)

        self.datos_box.add_layout(datos_layout)

        self.viz_box = CollapsibleBox("4. Visualizacion del Modelo")
        root.addWidget(self.viz_box)
        self._build_visualization_section()

        self.export_box = CollapsibleBox("5. Exportacion")
        root.addWidget(self.export_box)

        exp_layout = QHBoxLayout()
        self.combo_format = QComboBox()
        self.combo_format.addItems(["Pickle (.pkl)", "Joblib (.joblib)", "JSON (centroides)"])

        self.btn_export = QPushButton("Exportar")
        self.btn_export.setCursor(Qt.PointingHandCursor)
        self.btn_export.setEnabled(False)
        self.btn_export.clicked.connect(self._on_export)

        exp_layout.addWidget(self.combo_format)
        exp_layout.addSpacing(12)
        exp_layout.addWidget(self.btn_export)
        exp_layout.addStretch()
        self.export_box.add_layout(exp_layout)

        self.console_box = CollapsibleBox("6. Resultados")
        root.addWidget(self.console_box)

        self.output_log = QTextEdit()
        self.output_log.setReadOnly(True)
        self.output_log.setFixedHeight(150)
        self.console_box.add_widget(self.output_log)

        root.addStretch()

        self._install_training_guards()

        self.inf_box.collapse()
        self.datos_box.collapse()
        self.viz_box.collapse()
        self.export_box.collapse()
        self.console_box.expand()

    def _browse_dataset(self):
        examples_dir = os.path.join(os.path.dirname(__file__), "..", "examples")
        ruta, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar Dataset CSV",
            os.path.abspath(examples_dir),
            "CSV (*.csv);;Todos los archivos (*)",
        )
        if ruta:
            self._load_dataset(ruta)

    def _load_dataset(self, ruta: str):
        try:
            df = pd.read_csv(ruta)
        except Exception as exc:
            self._log(f"[Error] No se pudo leer el CSV: {exc}", color="#ff8aa5")
            return

        self._df = df
        self.ds_input.setText(ruta)
        self.combo_ignore.clear()
        self.combo_ignore.addItem("(Ninguna)")
        self.combo_ignore.addItems(list(df.columns))
        self.combo_ignore.setEnabled(True)

        rows, cols = df.shape
        self._log(
            f"[OK] Dataset cargado: {os.path.basename(ruta)} - {rows} filas, {cols} columnas.",
            color="#8ab1ff",
        )
        self._populate_samples()

    def _on_train(self):
        if self._df is None:
            self._show_missing_dataset_warning()
            return

        ignored_col = self.combo_ignore.currentText().strip()
        if ignored_col == "(Ninguna)":
            ignored_col = None

        n_clusters = self.spin_clusters.value()
        init_method = self.combo_init.currentText()
        n_init = self.spin_n_init.value()
        max_iter = self.spin_max_iter.value()

        available_features = len(self._df.columns) - (1 if ignored_col else 0)
        if available_features <= 0:
            self._log("[Error] Debe quedar al menos una columna para entrenar.", color="#ff8aa5")
            return

        self._log(
            "[Info] Iniciando entrenamiento - "
            f"clusters: {n_clusters} | init: {init_method} | n_init: {n_init} | max_iter: {max_iter}"
        )

        self.btn_train.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self._worker = KMeansTrainingWorker(
            self._df,
            ignored_col,
            n_clusters,
            init_method,
            n_init,
            max_iter,
        )
        self._worker.progress.connect(self.progress_bar.setValue)
        self._worker.finished.connect(self._on_training_done)
        self._worker.error.connect(self._on_training_error)
        self._worker.start()

    def _on_training_done(self, bundle: dict, metrics: dict):
        self._bundle = bundle
        self._last_metrics = metrics
        self.btn_train.setEnabled(True)
        self.btn_export.setEnabled(True)
        self.btn_infer.setEnabled(True)
        self.btn_infer_manual.setEnabled(True)
        self.btn_refresh_charts.setEnabled(True)
        self.progress_bar.setVisible(False)

        features = bundle.get("features", [])
        self._set_inference_headers(features)

        self._log("-" * 55)
        self._log(f"  Muestras procesadas       : {metrics['n_samples']}")
        self._log(f"  Features utilizadas      : {metrics['n_features']}")
        self._log(f"  Numero de clusters       : {metrics['n_clusters']}")
        self._log(f"  Inercia                  : {metrics['inertia']:.6f}")
        if metrics["silhouette"] is None:
            self._log("  Silhouette               : N/D")
        else:
            self._log(f"  Silhouette               : {metrics['silhouette']:.6f}")
        self._log(f"  Calidad base confianza   : {metrics['quality_score']:.2%}")
        for cluster_id, cluster_size in metrics["cluster_sizes"].items():
            self._log(f"  Cluster {cluster_id}               : {cluster_size} muestras")
        self._log("-" * 55)
        self._log("[OK] Modelo K-Means entrenado correctamente.", color="#8ab1ff")
        logging.info(
            "Modelo K-Means entrenado. "
            f"clusters={metrics['n_clusters']} | inertia={metrics['inertia']:.4f}"
        )
        self._populate_samples()
        self._refresh_charts()

    def _on_training_error(self, msg: str):
        self.btn_train.setEnabled(True)
        self.progress_bar.setVisible(False)
        self._log(f"[Error] {msg}", color="#ff8aa5")
        logging.error(f"Error en entrenamiento de K-Means: {msg}")

    def _on_export(self):
        if self._bundle is None:
            self._log("[Error] No hay ningun modelo entrenado para exportar.", color="#ff8aa5")
            return

        formato = self.combo_format.currentText()
        if "Pickle" in formato:
            ext = ".pkl"
            filtro = "Pickle (*.pkl);;Todos los archivos (*)"
        elif "Joblib" in formato:
            ext = ".joblib"
            filtro = "Joblib (*.joblib);;Todos los archivos (*)"
        else:
            ext = ".json"
            filtro = "JSON (*.json);;Todos los archivos (*)"

        ruta, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar Modelo",
            f"modelo_kmeans{ext}",
            filtro,
        )
        if not ruta:
            return

        try:
            if ext == ".json":
                model = self._bundle["model"]
                data = {
                    "tipo": type(model).__name__,
                    "features": self._bundle.get("features", []),
                    "ignored_column": self._bundle.get("ignored_column"),
                    "n_clusters": int(model.n_clusters),
                    "inertia": float(model.inertia_),
                    "centroides": model.cluster_centers_.tolist(),
                }
                with open(ruta, "w", encoding="utf-8") as file:
                    json.dump(data, file, indent=4, ensure_ascii=False)
            else:
                joblib.dump(self._bundle, ruta)

            self._log(f"[OK] Modelo exportado ({ext}): {ruta}", color="#8ab1ff")
            logging.info(f"Modelo K-Means exportado a: {ruta}")
        except Exception as exc:
            self._log(f"[Error] No se pudo guardar: {exc}", color="#ff8aa5")

    def _browse_inference(self):
        ruta, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar CSV para Inferencia",
            "",
            "CSV (*.csv);;Todos los archivos (*)",
        )
        if ruta:
            self.inf_input.setText(ruta)

    def _on_infer(self):
        if self._bundle is None:
            self._log("[Error] Primero entrena o carga un modelo.", color="#ff8aa5")
            return

        ruta = self.inf_input.text().strip()
        if not ruta or not os.path.isfile(ruta):
            self._log("[Error] Especifica un CSV de entrada valido.", color="#ff8aa5")
            return

        try:
            df_infer = pd.read_csv(ruta)
        except Exception as exc:
            self._log(f"[Error] No se pudo leer el CSV: {exc}", color="#ff8aa5")
            return

        features = self._bundle["features"]
        missing = [col for col in features if col not in df_infer.columns]
        if missing:
            self._log(f"[Error] Faltan columnas en el CSV: {missing}", color="#ff8aa5")
            return

        try:
            X_scaled = self._transform_features(df_infer[features].copy())
            labels = self._bundle["model"].predict(X_scaled)
            confidences = self._estimate_prediction_confidence(X_scaled, labels)
        except Exception as exc:
            self._log(f"[Error] Fallo durante la inferencia: {exc}", color="#ff8aa5")
            return

        self.inf_table.setRowCount(0)
        for i, (_, row_series) in enumerate(df_infer.iterrows()):
            if i >= 200:
                break
            row = self.inf_table.rowCount()
            self.inf_table.insertRow(row)
            for j, col_name in enumerate(features):
                item = QTableWidgetItem(str(row_series.get(col_name, "")))
                item.setTextAlignment(Qt.AlignCenter)
                self.inf_table.setItem(row, j, item)

            item_cluster = QTableWidgetItem(f"Cluster {int(labels[i])}")
            item_cluster.setTextAlignment(Qt.AlignCenter)
            self.inf_table.setItem(row, len(features), item_cluster)

            item_conf = QTableWidgetItem(self._format_confidence(confidences[i]))
            item_conf.setTextAlignment(Qt.AlignCenter)
            self.inf_table.setItem(row, len(features) + 1, item_conf)

        avg_conf = float(np.mean(confidences)) if len(confidences) else 0.0
        self._log(
            f"[OK] Inferencia completada: {len(labels)} asignaciones generadas. "
            f"Seguridad media: {self._format_confidence(avg_conf)}",
            color="#8ab1ff",
        )
        logging.info(f"Inferencia de K-Means completada: {len(labels)} muestras.")

    def _on_infer_manual(self):
        if self._bundle is None:
            self._log("[Error] Primero entrena o carga un modelo.", color="#ff8aa5")
            return

        from core.dialogs import ManualInferenceDialog

        features = self._bundle.get("features", [])
        dialog = ManualInferenceDialog(features, parent=self, title="Inferencia Manual K-Means")
        if dialog.exec():
            values_dict = dialog.get_values()
            try:
                df_infer = pd.DataFrame([values_dict])
                X_scaled = self._transform_features(df_infer.copy())
                label = int(self._bundle["model"].predict(X_scaled)[0])
                confidence = float(self._estimate_prediction_confidence(X_scaled, np.array([label]))[0])

                row = self.inf_table.rowCount()
                self.inf_table.insertRow(row)
                for i, col_name in enumerate(features):
                    item = QTableWidgetItem(str(values_dict.get(col_name, "")))
                    item.setTextAlignment(Qt.AlignCenter)
                    self.inf_table.setItem(row, i, item)

                item_cluster = QTableWidgetItem(f"Cluster {label}")
                item_cluster.setTextAlignment(Qt.AlignCenter)
                self.inf_table.setItem(row, len(features), item_cluster)

                item_conf = QTableWidgetItem(self._format_confidence(confidence))
                item_conf.setTextAlignment(Qt.AlignCenter)
                self.inf_table.setItem(row, len(features) + 1, item_conf)

                self._log(
                    f"[OK] Inferencia manual completada. Cluster: {label} | "
                    f"Seguridad: {self._format_confidence(confidence)}",
                    color="#8ab1ff",
                )
                logging.info(
                    f"Resultado inferencia manual K-Means: cluster={label} | seguridad={confidence:.2f}%"
                )
            except Exception as exc:
                self._log(f"[Error] Fallo durante la inferencia manual: {exc}", color="#ff8aa5")

    def _transform_features(self, df_features: pd.DataFrame) -> np.ndarray:
        features = self._bundle.get("features", [])
        encoders = self._bundle.get("label_encoders", {})

        X = df_features[features].copy()
        for col in features:
            if col in encoders:
                encoder = encoders[col]
                known_classes = set(encoder.classes_)
                X[col] = X[col].astype(str).map(
                    lambda value, known=known_classes, enc=encoder: value if value in known else enc.classes_[0]
                )
                X[col] = encoder.transform(X[col].astype(str))
            else:
                X[col] = pd.to_numeric(X[col], errors="coerce").fillna(0)

        return self._bundle["scaler"].transform(X)

    def _show_clusters_info(self):
        message = (
            "Clusters:\n"
            "Indica cuantos grupos internos quieres que K-Means intente descubrir.\n\n"
            "- Un valor bajo crea agrupaciones mas amplias.\n"
            "- Un valor alto crea grupos mas pequenos y especificos.\n"
            "- Debe ser menor o igual al numero de muestras del dataset.\n\n"
            "Si no conoces el valor ideal, empieza con 3 o 4 y compara los graficos."
        )
        QMessageBox.information(self, "Informacion de Clusters", message)

    def _show_init_info(self):
        message = (
            "Inicializacion:\n"
            "Define como se colocan los centroides antes de empezar a iterar.\n\n"
            "- k-means++: suele dar resultados mas estables y converge mejor.\n"
            "- random: elige centroides iniciales al azar y puede variar mas entre ejecuciones.\n\n"
            "En la mayoria de casos, k-means++ es la opcion recomendada."
        )
        QMessageBox.information(self, "Informacion de Inicializacion", message)

    def _show_max_iter_info(self):
        message = (
            "Max iter:\n"
            "Es el numero maximo de ciclos de ajuste que puede ejecutar el algoritmo.\n\n"
            "- Si el modelo converge antes, se detiene solo.\n"
            "- Si el dataset es complejo, un limite mayor puede ayudar a estabilizar los centroides.\n"
            "- Un valor demasiado alto solo aumenta el tiempo de calculo si no aporta mejora.\n\n"
            "300 suele ser un valor razonable para empezar."
        )
        QMessageBox.information(self, "Informacion de Max Iter", message)

    def _install_training_guards(self):
        self._training_guarded_widgets = [
            self.train_box.toggle_button,
            self.combo_ignore,
            self.spin_clusters,
            self.spin_clusters.lineEdit(),
            self.combo_init,
            self.spin_n_init,
            self.spin_n_init.lineEdit(),
            self.spin_max_iter,
            self.spin_max_iter.lineEdit(),
        ]
        for widget in self._training_guarded_widgets:
            widget.installEventFilter(self)

    def eventFilter(self, watched, event):
        if self._should_warn_missing_dataset(watched, event):
            self._show_missing_dataset_warning()
        return super().eventFilter(watched, event)

    def _should_warn_missing_dataset(self, watched, event) -> bool:
        if self._df is not None:
            return False
        if watched not in getattr(self, "_training_guarded_widgets", []):
            return False
        return event.type() in (QEvent.MouseButtonPress, QEvent.Wheel)

    def _show_missing_dataset_warning(self):
        message = "No hay ningun dataset cargado. Carga un CSV en la seccion de entrenamiento."
        self._log(f"[Aviso] {message}", color="#d8b46a")
        QMessageBox.warning(self, "Dataset no cargado", message)

    def _populate_samples(self):
        if self._df is None:
            return
        df_slice = self._df.head(self.spin_samples.value())
        self._fill_samples_table(df_slice)

    def _filter_samples(self, text: str):
        if self._df is None:
            return
        df_slice = self._df.head(self.spin_samples.value())
        if text.strip():
            mask = df_slice.apply(
                lambda row: row.astype(str).str.contains(text, case=False, na=False).any(),
                axis=1,
            )
            df_slice = df_slice[mask]
        self._fill_samples_table(df_slice)

    def _fill_samples_table(self, df: pd.DataFrame):
        self.samples_table.setRowCount(0)
        self.samples_table.setColumnCount(len(df.columns))
        self.samples_table.setHorizontalHeaderLabels(list(df.columns))
        for _, row_data in df.iterrows():
            row_idx = self.samples_table.rowCount()
            self.samples_table.insertRow(row_idx)
            for col_idx, value in enumerate(row_data):
                item = QTableWidgetItem(str(value))
                item.setTextAlignment(Qt.AlignCenter)
                self.samples_table.setItem(row_idx, col_idx, item)

    def _set_inference_headers(self, features):
        self.inf_table.setColumnCount(len(features) + 2)
        self.inf_table.setHorizontalHeaderLabels(features + ["Cluster", "% Seguridad"])

    def _estimate_prediction_confidence(self, X_scaled, labels=None) -> np.ndarray:
        model = self._bundle["model"]
        X_scaled = np.atleast_2d(np.asarray(X_scaled, dtype=float))
        if labels is None:
            labels = model.predict(X_scaled)

        distances = model.transform(X_scaled)
        assigned_distances = distances[np.arange(len(labels)), labels]

        stats = (self._bundle or {}).get("confidence_stats", {})
        cluster_refs = stats.get("cluster_distance_reference", {})
        quality_score = float(np.clip(stats.get("quality_score", 0.55), 0.0, 1.0))

        confidences = []
        for label, distance in zip(labels, assigned_distances):
            reference = float(cluster_refs.get(int(label), 1.0))
            if not np.isfinite(reference) or reference <= 0:
                reference = 1.0
            proximity_score = float(np.exp(-distance / reference))
            confidence = (0.75 * proximity_score + 0.25 * quality_score) * 100.0
            confidences.append(float(np.clip(confidence, 1.0, 99.0)))
        return np.asarray(confidences, dtype=float)

    @staticmethod
    def _format_confidence(value: float) -> str:
        return f"{value:.1f} %"

    def _build_visualization_section(self):
        viz_layout = QVBoxLayout()
        viz_layout.setSpacing(10)

        ctrl_row = QHBoxLayout()
        lbl_chart = QLabel("Grafico:")
        lbl_chart.setFixedWidth(60)
        lbl_chart.setProperty("tone", "section")

        self.combo_chart = QComboBox()
        self.combo_chart.addItems(
            [
                "Proyeccion PCA de Clusters",
                "Tamano por Cluster",
                "Distancia al Centroide",
                "Centroides Normalizados",
            ]
        )
        self.combo_chart.currentIndexChanged.connect(self._on_chart_type_changed)

        self.btn_refresh_charts = QPushButton("Actualizar")
        self.btn_refresh_charts.setCursor(Qt.PointingHandCursor)
        self.btn_refresh_charts.setEnabled(False)
        self.btn_refresh_charts.clicked.connect(self._refresh_charts)

        ctrl_row.addWidget(lbl_chart)
        ctrl_row.addWidget(self.combo_chart)
        ctrl_row.addSpacing(12)
        ctrl_row.addWidget(self.btn_refresh_charts)
        ctrl_row.addStretch()
        viz_layout.addLayout(ctrl_row)

        self._fig, self._ax = plt.subplots(figsize=(8, 4))
        self._fig.patch.set_facecolor("#11161f")
        self._ax.set_facecolor("#0d121a")
        self._canvas = FigureCanvas(self._fig)
        self._canvas.setObjectName("KMeansChartCanvas")
        self._canvas.setMinimumHeight(320)
        self._canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        viz_layout.addWidget(self._canvas)

        self._viz_status = QLabel("Entrena un modelo para visualizar los graficos.")
        self._set_viz_status_tone("status-muted")
        viz_layout.addWidget(self._viz_status)

        self.viz_box.add_layout(viz_layout)

    def _on_chart_type_changed(self, _index: int):
        if self._bundle is not None:
            self._refresh_charts()

    def _refresh_charts(self):
        if self._bundle is None or self._df is None:
            self._set_viz_status("Carga un dataset y entrena el modelo para visualizar.", "status-muted")
            return

        chart_name = self.combo_chart.currentText()
        self._fig.clear()
        self._ax = self._fig.add_subplot(111)
        self._fig.patch.set_facecolor("#11161f")
        self._ax.set_facecolor("#0d121a")

        try:
            features = self._bundle["features"]
            X_scaled = self._transform_features(self._df[features].copy())
            model = self._bundle["model"]
            labels = model.predict(X_scaled)
            distances = model.transform(X_scaled)
            assigned_distances = distances[np.arange(len(labels)), labels]

            accent = "#4c81ff"
            accent2 = "#8ab1ff"
            grid_c = "#263042"
            text_c = "#dbe3f6"
            tick_c = "#92a0bb"

            def _style_ax(ax):
                ax.set_facecolor("#0d121a")
                ax.tick_params(colors=tick_c, labelsize=9)
                ax.xaxis.label.set_color(text_c)
                ax.yaxis.label.set_color(text_c)
                ax.title.set_color(text_c)
                for spine in ax.spines.values():
                    spine.set_edgecolor(grid_c)
                ax.grid(True, color=grid_c, linewidth=0.6, linestyle="--", alpha=0.7)

            if chart_name == "Proyeccion PCA de Clusters":
                if X_scaled.shape[1] >= 2:
                    reducer = PCA(n_components=2, random_state=42)
                    points = reducer.fit_transform(X_scaled)
                    centers = reducer.transform(model.cluster_centers_)
                    xlabel = "Componente 1"
                    ylabel = "Componente 2"
                else:
                    points = np.column_stack([X_scaled[:, 0], np.zeros(len(X_scaled))])
                    centers = np.column_stack([model.cluster_centers_[:, 0], np.zeros(model.n_clusters)])
                    xlabel = features[0]
                    ylabel = "Escala auxiliar"

                palette = ["#4c81ff", "#ff8aa5", "#7bd389", "#ffd166", "#c19cff", "#6fd3ff"]
                for cluster_id in range(model.n_clusters):
                    mask = labels == cluster_id
                    color = palette[cluster_id % len(palette)]
                    self._ax.scatter(
                        points[mask, 0],
                        points[mask, 1],
                        color=color,
                        alpha=0.6,
                        edgecolors="none",
                        s=28,
                        label=f"Cluster {cluster_id}",
                    )
                self._ax.scatter(
                    centers[:, 0],
                    centers[:, 1],
                    color="#ffffff",
                    edgecolors="#11161f",
                    s=120,
                    marker="X",
                    linewidths=1.0,
                    label="Centroides",
                )
                self._ax.set_xlabel(xlabel)
                self._ax.set_ylabel(ylabel)
                self._ax.set_title("Proyeccion 2D de Clusters")
                self._ax.legend(facecolor="#11161f", edgecolor=grid_c, labelcolor=text_c, fontsize=9)
                _style_ax(self._ax)

            elif chart_name == "Tamano por Cluster":
                cluster_ids = list(range(model.n_clusters))
                sizes = [int(np.sum(labels == cluster_id)) for cluster_id in cluster_ids]
                self._ax.bar(cluster_ids, sizes, color=accent, edgecolor="none", width=0.65)
                self._ax.set_xlabel("Cluster")
                self._ax.set_ylabel("Muestras")
                self._ax.set_title("Tamano de cada Cluster")
                self._ax.set_xticks(cluster_ids)
                _style_ax(self._ax)

            elif chart_name == "Distancia al Centroide":
                box_data = []
                labels_text = []
                for cluster_id in range(model.n_clusters):
                    cluster_distances = assigned_distances[labels == cluster_id]
                    if cluster_distances.size:
                        box_data.append(cluster_distances)
                        labels_text.append(f"C{cluster_id}")
                if box_data:
                    bp = self._ax.boxplot(box_data, patch_artist=True, labels=labels_text)
                    for patch in bp["boxes"]:
                        patch.set_facecolor(accent2)
                        patch.set_edgecolor("#11161f")
                    for median in bp["medians"]:
                        median.set_color("#ff8aa5")
                    self._ax.set_xlabel("Cluster")
                    self._ax.set_ylabel("Distancia asignada")
                    self._ax.set_title("Distancia de las muestras a su centroide")
                else:
                    self._ax.text(
                        0.5,
                        0.5,
                        "No hay suficientes datos para mostrar distancias.",
                        ha="center",
                        va="center",
                        color=text_c,
                        fontsize=11,
                        transform=self._ax.transAxes,
                    )
                _style_ax(self._ax)

            else:
                heatmap = self._ax.imshow(
                    model.cluster_centers_,
                    aspect="auto",
                    cmap="Blues",
                    interpolation="nearest",
                )
                self._ax.set_title("Centroides normalizados")
                self._ax.set_xlabel("Feature")
                self._ax.set_ylabel("Cluster")
                self._ax.set_xticks(range(len(features)))
                self._ax.set_xticklabels(features, rotation=45, ha="right", fontsize=8)
                self._ax.set_yticks(range(model.n_clusters))
                self._ax.set_yticklabels([f"Cluster {idx}" for idx in range(model.n_clusters)], fontsize=9)
                self._fig.colorbar(heatmap, ax=self._ax, fraction=0.04, pad=0.03)
                _style_ax(self._ax)

            self._fig.tight_layout(pad=1.5)
            self._canvas.draw()
            self._set_viz_status(f"Grafico generado: {chart_name}", "status-success")
        except Exception as exc:
            self._set_viz_status(f"Error al generar grafico: {exc}", "status-error")
            logging.error(f"Error visualizacion K-Means: {exc}")

    def _log(self, msg: str, color: str = "#cccccc"):
        self.output_log.append(f"<span style='color:{color};'>{msg}</span>")

    def _create_info_button(self, tooltip: str, callback) -> QPushButton:
        button = QPushButton("i")
        button.setFixedSize(28, 28)
        button.setProperty("variant", "info")
        button.setCursor(Qt.PointingHandCursor)
        button.setToolTip(tooltip)
        button.clicked.connect(callback)
        return button

    def _set_viz_status_tone(self, tone: str):
        set_dynamic_property(self._viz_status, "tone", tone)

    def _set_viz_status(self, text: str, tone: str):
        self._viz_status.setText(text)
        self._set_viz_status_tone(tone)

    def load_bundle(self, bundle: dict):
        self._bundle = bundle
        self._df = None
        self._last_metrics = None
        self.ds_input.setText("")
        self.combo_ignore.clear()
        self.combo_ignore.setEnabled(False)

        self.btn_export.setEnabled(True)
        self.btn_infer.setEnabled(True)
        self.btn_infer_manual.setEnabled(True)
        self.progress_bar.setVisible(False)

        features = bundle.get("features", [])
        self._set_inference_headers(features)
        self.inf_table.setRowCount(0)

        self._log("-" * 55)
        self._log("[OK] Modelo K-Means cargado desde archivo.", color="#8ab1ff")
        self._log(f"  Features esperadas: {len(features)}", color="#cccccc")
        if bundle.get("ignored_column"):
            self._log(f"  Columna ignorada: {bundle['ignored_column']}", color="#cccccc")
        self._log("Listo para inferencia.", color="#cccccc")
        logging.info("Modelo K-Means inyectado en la vista exitosamente.")

        self.train_box.expand()
        self.inf_box.collapse()
        self.viz_box.collapse()
        self.export_box.collapse()
        self.console_box.expand()
        self.btn_refresh_charts.setEnabled(False)
        self._fig.clear()
        self._ax = self._fig.add_subplot(111)
        self._fig.patch.set_facecolor("#11161f")
        self._ax.set_facecolor("#0d121a")
        self._canvas.draw()
        self._set_viz_status("Entrena un modelo para visualizar los graficos.", "status-muted")

    def reset_view(self):
        self._bundle = None
        self._df = None
        self._last_metrics = None
        self.ds_input.setText("")
        self.combo_ignore.clear()
        self.combo_ignore.setEnabled(False)

        self.btn_export.setEnabled(False)
        self.btn_infer.setEnabled(False)
        self.btn_infer_manual.setEnabled(False)

        self.inf_table.setRowCount(0)
        self.inf_table.setColumnCount(3)
        self.inf_table.setHorizontalHeaderLabels(["Muestra", "Cluster", "% Seguridad"])

        self._log("-" * 55)
        self._log("[Info] Nuevo modelo de K-Means inicializado.", color="#cccccc")
        self._log("Selecciona un dataset CSV para empezar a entrenar.", color="#cccccc")

        self.train_box.expand()
        self.inf_box.collapse()
        self.viz_box.collapse()
        self.export_box.collapse()
        self.console_box.expand()
        self.btn_refresh_charts.setEnabled(False)
        self._fig.clear()
        self._ax = self._fig.add_subplot(111)
        self._fig.patch.set_facecolor("#11161f")
        self._ax.set_facecolor("#0d121a")
        self._canvas.draw()
        self._set_viz_status("Entrena un modelo para visualizar los graficos.", "status-muted")
