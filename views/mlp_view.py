import json
import logging
import os

import joblib
import matplotlib.pyplot as plt
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
    QDoubleSpinBox,
    QSpinBox,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QHeaderView,
)
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier, MLPRegressor
from sklearn.preprocessing import LabelEncoder, StandardScaler

from core.components import CollapsibleBox
from core.styles import apply_stylesheet, set_dynamic_property


class MLPTrainingWorker(QThread):
    finished = Signal(object, dict)
    error = Signal(str)
    progress = Signal(int)

    def __init__(
        self,
        df: pd.DataFrame,
        target_col: str,
        task_mode: str,
        hidden_layers_text: str,
        activation: str,
        alpha: float,
        learning_rate: float,
        max_iter: int,
        test_size: float,
    ):
        super().__init__()
        self.df = df
        self.target_col = target_col
        self.task_mode = task_mode
        self.hidden_layers_text = hidden_layers_text
        self.activation = activation
        self.alpha = alpha
        self.learning_rate = learning_rate
        self.max_iter = max_iter
        self.test_size = test_size

    @staticmethod
    def _parse_hidden_layers(text: str) -> tuple[int, ...]:
        values = [chunk.strip() for chunk in text.split(",") if chunk.strip()]
        if not values:
            raise ValueError("Define al menos una capa oculta.")
        parsed = tuple(int(value) for value in values)
        if any(value <= 0 for value in parsed):
            raise ValueError("Las capas ocultas deben ser enteros positivos.")
        return parsed

    @staticmethod
    def _infer_task_type(series: pd.Series, task_mode: str) -> str:
        if task_mode == "Clasificacion":
            return "classification"
        if task_mode == "Regresion":
            return "regression"

        dtype_name = str(series.dtype)
        if dtype_name in {"object", "category", "string"}:
            return "classification"

        numeric = pd.to_numeric(series, errors="coerce")
        unique_count = int(series.nunique(dropna=True))
        if unique_count <= max(12, min(20, len(series) // 8 or 1)):
            return "classification"
        if pd.api.types.is_integer_dtype(series.dtype) and unique_count <= 30:
            return "classification"
        if numeric.notna().sum() == 0:
            return "classification"
        return "regression"

    def run(self):
        try:
            self.progress.emit(10)
            hidden_layers = self._parse_hidden_layers(self.hidden_layers_text)

            X = self.df.drop(columns=[self.target_col]).copy()
            y = self.df[self.target_col].copy()

            if X.empty:
                self.error.emit("El dataset no contiene columnas usables como features.")
                return

            task_type = self._infer_task_type(y, self.task_mode)
            label_encoders = {}

            self.progress.emit(25)
            for col in X.columns:
                if X[col].dtype == "object" or str(X[col].dtype) in {"category", "string"}:
                    encoder = LabelEncoder()
                    X[col] = encoder.fit_transform(X[col].astype(str))
                    label_encoders[col] = encoder
                else:
                    X[col] = pd.to_numeric(X[col], errors="coerce")

            X = X.fillna(0)

            if task_type == "classification":
                y_series = y.astype(str).fillna("")
                encoder_y = LabelEncoder()
                y_processed = pd.Series(
                    encoder_y.fit_transform(y_series),
                    index=y.index,
                )
                label_encoders["target"] = encoder_y
                if y_processed.nunique() < 2:
                    self.error.emit("La clasificacion necesita al menos dos clases distintas.")
                    return
                class_counts = y_processed.value_counts()
                stratify = y_processed if not class_counts.empty and int(class_counts.min()) >= 2 else None
            else:
                y_processed = pd.to_numeric(y, errors="coerce").fillna(0)
                stratify = None

            X_train, X_test, y_train, y_test = train_test_split(
                X,
                y_processed,
                test_size=self.test_size,
                random_state=42,
                stratify=stratify,
            )

            scaler = StandardScaler()
            self.progress.emit(45)
            X_train_s = scaler.fit_transform(X_train)
            X_test_s = scaler.transform(X_test)

            common_kwargs = {
                "hidden_layer_sizes": hidden_layers,
                "activation": self.activation,
                "alpha": self.alpha,
                "learning_rate_init": self.learning_rate,
                "max_iter": self.max_iter,
                "random_state": 42,
            }
            if task_type == "classification":
                model = MLPClassifier(**common_kwargs)
            else:
                model = MLPRegressor(**common_kwargs)

            self.progress.emit(70)
            model.fit(X_train_s, y_train)
            y_pred = model.predict(X_test_s)

            metrics = {
                "task_type": task_type,
                "n_train": int(len(X_train)),
                "n_test": int(len(X_test)),
                "n_features": int(X_train.shape[1]),
                "hidden_layers": hidden_layers,
                "iterations": int(getattr(model, "n_iter_", 0)),
                "final_loss": float(getattr(model, "loss_", 0.0)),
            }

            confidence_stats = {}
            if task_type == "classification":
                accuracy = float(accuracy_score(y_test, y_pred))
                f1 = float(f1_score(y_test, y_pred, average="weighted", zero_division=0))
                max_prob = None
                if hasattr(model, "predict_proba"):
                    proba = model.predict_proba(X_test_s)
                    max_prob = float(np.mean(np.max(proba, axis=1))) if len(proba) else None
                quality_score = accuracy
                metrics.update(
                    {
                        "accuracy": accuracy,
                        "f1_weighted": f1,
                        "class_count": int(len(np.unique(y_processed))),
                        "mean_confidence": max_prob,
                    }
                )
                confidence_stats = {
                    "quality_score": quality_score,
                    "mean_probability": max_prob if max_prob is not None else accuracy,
                }
            else:
                mse = float(mean_squared_error(y_test, y_pred))
                rmse = float(mse ** 0.5)
                mae = float(mean_absolute_error(y_test, y_pred))
                r2 = float(r2_score(y_test, y_pred))
                quality_score = float(np.clip(r2, 0.0, 1.0))
                train_distances = np.mean(np.abs(X_train_s), axis=1)
                distance_reference = float(np.percentile(train_distances, 90)) if train_distances.size else 1.0
                if not np.isfinite(distance_reference) or distance_reference <= 0:
                    distance_reference = 1.0
                metrics.update(
                    {
                        "mse": mse,
                        "rmse": rmse,
                        "mae": mae,
                        "r2": r2,
                    }
                )
                confidence_stats = {
                    "quality_score": quality_score,
                    "distance_reference": distance_reference,
                }

            bundle = {
                "sandbox_model_type": "mlp",
                "model": model,
                "scaler": scaler,
                "features": list(X.columns),
                "label_encoders": label_encoders,
                "task_type": task_type,
                "target_column": self.target_col,
                "training_config": {
                    "task_mode": self.task_mode,
                    "hidden_layers": list(hidden_layers),
                    "activation": self.activation,
                    "alpha": self.alpha,
                    "learning_rate": self.learning_rate,
                    "max_iter": self.max_iter,
                    "test_size": self.test_size,
                },
                "confidence_stats": confidence_stats,
            }
            self.progress.emit(100)
            self.finished.emit(bundle, metrics)
        except Exception as exc:
            self.error.emit(str(exc))


class MLPView(QWidget):
    bundle_changed = Signal(dict)

    def __init__(self):
        super().__init__()
        self.setObjectName("MLPView")
        apply_stylesheet(self, "regression_view.qss", "mlp_view.qss")

        self._bundle = None
        self._df = None
        self._last_metrics = None

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(16)

        self.train_box = CollapsibleBox("1. Entrenamiento de Red Neuronal")
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
        lbl_target = QLabel("Variable objetivo:")
        lbl_target.setFixedWidth(170)
        self.combo_target = QComboBox()
        self.combo_target.setEnabled(False)

        lbl_task = QLabel("Modo:")
        lbl_task.setFixedWidth(60)
        self.combo_task = QComboBox()
        self.combo_task.addItems(["Auto", "Clasificacion", "Regresion"])

        row2.addWidget(lbl_target)
        row2.addWidget(self.combo_target)
        row2.addSpacing(18)
        row2.addWidget(lbl_task)
        row2.addWidget(self.combo_task)
        row2.addStretch()
        self.train_box.add_layout(row2)

        row3 = QHBoxLayout()
        lbl_layers = QLabel("Capas ocultas:")
        lbl_layers.setFixedWidth(105)
        self.btn_layers_info = self._create_info_button(
            "Informacion sobre capas ocultas",
            self._show_layers_info,
        )
        self.input_layers = QLineEdit("64,32")
        self.input_layers.setPlaceholderText("Ejemplo: 64,32")

        lbl_activation = QLabel("Activacion:")
        lbl_activation.setFixedWidth(90)
        self.btn_activation_info = self._create_info_button(
            "Informacion sobre activacion",
            self._show_activation_info,
        )
        self.combo_activation = QComboBox()
        self.combo_activation.addItems(["relu", "tanh", "logistic"])

        row3.addWidget(lbl_layers)
        row3.addWidget(self.btn_layers_info)
        row3.addWidget(self.input_layers)
        row3.addSpacing(18)
        row3.addWidget(lbl_activation)
        row3.addWidget(self.btn_activation_info)
        row3.addWidget(self.combo_activation)
        row3.addStretch()
        self.train_box.add_layout(row3)

        row4 = QHBoxLayout()
        lbl_alpha = QLabel("Alpha:")
        lbl_alpha.setFixedWidth(80)
        self.btn_alpha_info = self._create_info_button(
            "Informacion sobre regularizacion",
            self._show_alpha_info,
        )
        self.spin_alpha = QDoubleSpinBox()
        self.spin_alpha.setRange(0.0001, 10.0)
        self.spin_alpha.setDecimals(4)
        self.spin_alpha.setValue(0.0001)
        self.spin_alpha.setSingleStep(0.0005)

        lbl_lr = QLabel("Learning rate:")
        lbl_lr.setFixedWidth(110)
        self.btn_lr_info = self._create_info_button(
            "Informacion sobre learning rate",
            self._show_learning_rate_info,
        )
        self.spin_learning_rate = QDoubleSpinBox()
        self.spin_learning_rate.setRange(0.0001, 1.0)
        self.spin_learning_rate.setDecimals(4)
        self.spin_learning_rate.setValue(0.001)
        self.spin_learning_rate.setSingleStep(0.0005)

        lbl_iter = QLabel("Epocas max:")
        lbl_iter.setFixedWidth(90)
        self.btn_iter_info = self._create_info_button(
            "Informacion sobre epocas maximas",
            self._show_iterations_info,
        )
        self.spin_max_iter = QSpinBox()
        self.spin_max_iter.setRange(10, 5000)
        self.spin_max_iter.setValue(300)
        self.spin_max_iter.setSingleStep(10)

        lbl_test = QLabel("% Test:")
        lbl_test.setFixedWidth(75)
        self.spin_test = QSpinBox()
        self.spin_test.setRange(5, 50)
        self.spin_test.setValue(20)
        self.spin_test.setSuffix(" %")

        row4.addWidget(lbl_alpha)
        row4.addWidget(self.btn_alpha_info)
        row4.addWidget(self.spin_alpha)
        row4.addSpacing(18)
        row4.addWidget(lbl_lr)
        row4.addWidget(self.btn_lr_info)
        row4.addWidget(self.spin_learning_rate)
        row4.addSpacing(18)
        row4.addWidget(lbl_iter)
        row4.addWidget(self.btn_iter_info)
        row4.addWidget(self.spin_max_iter)
        row4.addSpacing(18)
        row4.addWidget(lbl_test)
        row4.addWidget(self.spin_test)
        row4.addStretch()
        self.train_box.add_layout(row4)

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
        self.inf_table.setHorizontalHeaderLabels(["Muestra", "Prediccion", "% Seguridad"])
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
        self.combo_format.addItems(["Pickle (.pkl)", "Joblib (.joblib)", "JSON (pesos)"])

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
        self.combo_target.clear()
        self.combo_target.addItems(list(df.columns))
        self.combo_target.setEnabled(True)

        expected_target = (self._bundle or {}).get("target_column")
        if expected_target and expected_target in df.columns:
            self.combo_target.setCurrentText(expected_target)

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

        target = self.combo_target.currentText().strip()
        if not target:
            self._log("[Error] Selecciona una variable objetivo.", color="#ff8aa5")
            return

        hidden_layers = self.input_layers.text().strip()
        task_mode = self.combo_task.currentText()
        activation = self.combo_activation.currentText()
        alpha = self.spin_alpha.value()
        learning_rate = self.spin_learning_rate.value()
        max_iter = self.spin_max_iter.value()
        test_size = self.spin_test.value() / 100.0

        self._log(
            "[Info] Iniciando entrenamiento - "
            f"target: {target} | modo: {task_mode} | capas: {hidden_layers} | "
            f"activacion: {activation} | alpha: {alpha} | lr: {learning_rate}"
        )

        self.btn_train.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self._worker = MLPTrainingWorker(
            self._df,
            target,
            task_mode,
            hidden_layers,
            activation,
            alpha,
            learning_rate,
            max_iter,
            test_size,
        )
        self._worker.progress.connect(self.progress_bar.setValue)
        self._worker.finished.connect(self._on_training_done)
        self._worker.error.connect(self._on_training_error)
        self._worker.start()

    def _on_training_done(self, bundle: dict, metrics: dict):
        self._bundle = bundle
        self._last_metrics = metrics
        self.bundle_changed.emit(bundle)
        self.btn_train.setEnabled(True)
        self.btn_export.setEnabled(True)
        self.btn_infer.setEnabled(True)
        self.btn_infer_manual.setEnabled(True)
        self.btn_refresh_charts.setEnabled(True)
        self.progress_bar.setVisible(False)

        features = bundle.get("features", [])
        self._set_inference_headers(features)
        self._sync_controls_with_bundle(bundle)

        self._log("-" * 55)
        self._log(f"  Tipo de tarea            : {self._task_label(bundle.get('task_type'))}")
        self._log(f"  Muestras de entrenamiento: {metrics['n_train']}")
        self._log(f"  Muestras de test         : {metrics['n_test']}")
        self._log(f"  Features utilizadas      : {metrics['n_features']}")
        self._log(f"  Capas ocultas            : {metrics['hidden_layers']}")
        self._log(f"  Iteraciones              : {metrics['iterations']}")
        self._log(f"  Loss final               : {metrics['final_loss']:.6f}")
        if metrics["task_type"] == "classification":
            self._log(f"  Accuracy                 : {metrics['accuracy']:.2%}")
            self._log(f"  F1 weighted              : {metrics['f1_weighted']:.2%}")
            if metrics.get("mean_confidence") is not None:
                self._log(f"  Confianza media          : {metrics['mean_confidence']:.2%}")
            self._log(f"  Numero de clases         : {metrics['class_count']}")
        else:
            self._log(f"  MSE                      : {metrics['mse']:.6f}")
            self._log(f"  RMSE                     : {metrics['rmse']:.6f}")
            self._log(f"  MAE                      : {metrics['mae']:.6f}")
            self._log(f"  R2 Score                 : {metrics['r2']:.6f}")
        self._log("-" * 55)
        self._log("[OK] Modelo MLP entrenado correctamente.", color="#8ab1ff")
        logging.info(
            "Modelo MLP entrenado. "
            f"task={bundle.get('task_type')} | layers={bundle.get('training_config', {}).get('hidden_layers')}"
        )
        self._populate_samples()
        self._refresh_charts()

    def _on_training_error(self, msg: str):
        self.btn_train.setEnabled(True)
        self.progress_bar.setVisible(False)
        self._log(f"[Error] {msg}", color="#ff8aa5")
        logging.error(f"Error en entrenamiento de MLP: {msg}")

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
            f"modelo_mlp{ext}",
            filtro,
        )
        if not ruta:
            return

        try:
            if ext == ".json":
                model = self._bundle["model"]
                data = {
                    "tipo": type(model).__name__,
                    "task_type": self._bundle.get("task_type"),
                    "features": self._bundle.get("features", []),
                    "target_column": self._bundle.get("target_column"),
                    "training_config": self._bundle.get("training_config", {}),
                    "coefs": [coef.tolist() for coef in getattr(model, "coefs_", [])],
                    "intercepts": [bias.tolist() for bias in getattr(model, "intercepts_", [])],
                }
                with open(ruta, "w", encoding="utf-8") as file:
                    json.dump(data, file, indent=4, ensure_ascii=False)
            else:
                joblib.dump(self._bundle, ruta)

            self._log(f"[OK] Modelo exportado ({ext}): {ruta}", color="#8ab1ff")
            logging.info(f"Modelo MLP exportado a: {ruta}")
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
            predictions, confidences = self._predict_with_confidence(X_scaled)
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

            item_pred = QTableWidgetItem(str(predictions[i]))
            item_pred.setTextAlignment(Qt.AlignCenter)
            self.inf_table.setItem(row, len(features), item_pred)

            item_conf = QTableWidgetItem(self._format_confidence(confidences[i]))
            item_conf.setTextAlignment(Qt.AlignCenter)
            self.inf_table.setItem(row, len(features) + 1, item_conf)

        avg_conf = float(np.mean(confidences)) if len(confidences) else 0.0
        self._log(
            f"[OK] Inferencia completada: {len(predictions)} predicciones generadas. "
            f"Seguridad media: {self._format_confidence(avg_conf)}",
            color="#8ab1ff",
        )
        logging.info(f"Inferencia MLP completada: {len(predictions)} muestras.")

    def _on_infer_manual(self):
        if self._bundle is None:
            self._log("[Error] Primero entrena o carga un modelo.", color="#ff8aa5")
            return

        from core.dialogs import ManualInferenceDialog

        features = self._bundle.get("features", [])
        dialog = ManualInferenceDialog(features, parent=self, title="Inferencia Manual MLP")
        if dialog.exec():
            values_dict = dialog.get_values()
            try:
                df_infer = pd.DataFrame([values_dict])
                X_scaled = self._transform_features(df_infer.copy())
                predictions, confidences = self._predict_with_confidence(X_scaled)

                row = self.inf_table.rowCount()
                self.inf_table.insertRow(row)
                for i, col_name in enumerate(features):
                    item = QTableWidgetItem(str(values_dict.get(col_name, "")))
                    item.setTextAlignment(Qt.AlignCenter)
                    self.inf_table.setItem(row, i, item)

                item_pred = QTableWidgetItem(str(predictions[0]))
                item_pred.setTextAlignment(Qt.AlignCenter)
                self.inf_table.setItem(row, len(features), item_pred)

                item_conf = QTableWidgetItem(self._format_confidence(confidences[0]))
                item_conf.setTextAlignment(Qt.AlignCenter)
                self.inf_table.setItem(row, len(features) + 1, item_conf)

                self._log(
                    f"[OK] Inferencia manual completada. Prediccion: {predictions[0]} | "
                    f"Seguridad: {self._format_confidence(confidences[0])}",
                    color="#8ab1ff",
                )
                logging.info(
                    f"Resultado inferencia manual MLP: {predictions[0]} | seguridad={confidences[0]:.2f}%"
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

    def _predict_with_confidence(self, X_scaled: np.ndarray):
        model = self._bundle["model"]
        task_type = self._bundle.get("task_type")
        stats = self._bundle.get("confidence_stats", {})
        quality_score = float(np.clip(stats.get("quality_score", 0.5), 0.0, 1.0))

        if task_type == "classification":
            raw_preds = model.predict(X_scaled)
            if "target" in self._bundle.get("label_encoders", {}):
                encoder = self._bundle["label_encoders"]["target"]
                predictions = encoder.inverse_transform(np.asarray(raw_preds, dtype=int))
            else:
                predictions = raw_preds

            if hasattr(model, "predict_proba"):
                probabilities = model.predict_proba(X_scaled)
                confidences = (0.75 * np.max(probabilities, axis=1) + 0.25 * quality_score) * 100.0
            else:
                confidences = np.full(len(raw_preds), quality_score * 100.0, dtype=float)
            return predictions, np.clip(confidences, 1.0, 99.0)

        predictions = model.predict(X_scaled)
        distance_reference = float(stats.get("distance_reference", 1.0))
        if not np.isfinite(distance_reference) or distance_reference <= 0:
            distance_reference = 1.0
        distances = np.mean(np.abs(X_scaled), axis=1)
        proximity_score = np.exp(-distances / distance_reference)
        confidences = (0.6 * proximity_score + 0.4 * quality_score) * 100.0
        display = [f"{value:.6f}" for value in predictions]
        return display, np.clip(confidences, 1.0, 99.0)

    def _show_layers_info(self):
        message = (
            "Capas ocultas:\n"
            "Define cuantas neuronas tendra cada capa interna de la red.\n\n"
            "Escribe una lista separada por comas, por ejemplo 64,32.\n"
            "Mas capas o mas neuronas aumentan la capacidad del modelo, "
            "pero tambien el tiempo de entrenamiento y el riesgo de sobreajuste."
        )
        QMessageBox.information(self, "Informacion de Capas Ocultas", message)

    def _show_activation_info(self):
        message = (
            "Activacion:\n"
            "Controla como responde cada neurona ante la informacion recibida.\n\n"
            "- relu: suele ser la opcion mas equilibrada.\n"
            "- tanh: puede funcionar bien con datos centrados.\n"
            "- logistic: util cuando quieres respuestas mas suaves, aunque suele ser mas lenta."
        )
        QMessageBox.information(self, "Informacion de Activacion", message)

    def _show_alpha_info(self):
        message = (
            "Alpha:\n"
            "Es la regularizacion aplicada a la red neuronal.\n\n"
            "Un valor mayor frena pesos extremos y ayuda a evitar sobreajuste. "
            "Un valor demasiado alto puede hacer que la red aprenda de forma demasiado conservadora."
        )
        QMessageBox.information(self, "Informacion de Alpha", message)

    def _show_learning_rate_info(self):
        message = (
            "Learning rate:\n"
            "Marca el tamano de los ajustes que hace la red en cada paso.\n\n"
            "Si es muy alto, el entrenamiento puede volverse inestable. "
            "Si es muy bajo, la red tardara mucho en converger."
        )
        QMessageBox.information(self, "Informacion de Learning Rate", message)

    def _show_iterations_info(self):
        message = (
            "Epocas max:\n"
            "Es el numero maximo de iteraciones completas que intentara la red.\n\n"
            "Si el modelo no converge antes, seguira intentandolo hasta llegar a este limite."
        )
        QMessageBox.information(self, "Informacion de Epocas Maximas", message)

    def _install_training_guards(self):
        self._training_guarded_widgets = [
            self.train_box.toggle_button,
            self.combo_target,
            self.combo_task,
            self.input_layers,
            self.combo_activation,
            self.spin_alpha,
            self.spin_alpha.lineEdit(),
            self.spin_learning_rate,
            self.spin_learning_rate.lineEdit(),
            self.spin_max_iter,
            self.spin_max_iter.lineEdit(),
            self.spin_test,
            self.spin_test.lineEdit(),
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
        self.inf_table.setHorizontalHeaderLabels(features + ["Prediccion", "% Seguridad"])

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
                "Curva de perdida",
                "Predicciones vs Referencia",
                "Distribucion de seguridad",
                "Pesos de la primera capa",
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
        self._canvas.setObjectName("MLPChartCanvas")
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
            target_col = self.combo_target.currentText() or self._bundle.get("target_column")
            if not target_col or target_col not in self._df.columns:
                self._set_viz_status("Selecciona la variable objetivo para generar graficos.", "status-muted")
                return

            X_scaled = self._transform_features(self._df[features].copy())
            task_type = self._bundle.get("task_type")
            model = self._bundle["model"]

            text_c = "#dbe3f6"
            tick_c = "#92a0bb"
            grid_c = "#263042"

            def _style_ax(ax):
                ax.set_facecolor("#0d121a")
                ax.tick_params(colors=tick_c, labelsize=9)
                ax.xaxis.label.set_color(text_c)
                ax.yaxis.label.set_color(text_c)
                ax.title.set_color(text_c)
                for spine in ax.spines.values():
                    spine.set_edgecolor(grid_c)
                ax.grid(True, color=grid_c, linewidth=0.6, linestyle="--", alpha=0.7)

            if chart_name == "Curva de perdida":
                loss_curve = getattr(model, "loss_curve_", [])
                if loss_curve:
                    self._ax.plot(range(1, len(loss_curve) + 1), loss_curve, color="#4c81ff", linewidth=2.0)
                    self._ax.set_xlabel("Iteracion")
                    self._ax.set_ylabel("Loss")
                    self._ax.set_title("Curva de perdida")
                else:
                    self._ax.text(
                        0.5,
                        0.5,
                        "Este modelo no expone historial de perdida.",
                        ha="center",
                        va="center",
                        color=text_c,
                        fontsize=11,
                        transform=self._ax.transAxes,
                    )
                _style_ax(self._ax)

            elif chart_name == "Predicciones vs Referencia":
                if task_type == "classification":
                    encoder = self._bundle.get("label_encoders", {}).get("target")
                    if encoder is not None:
                        known_classes = set(encoder.classes_)
                        y_true = self._df[target_col].astype(str).map(
                            lambda value, known=known_classes, enc=encoder: value if value in known else enc.classes_[0]
                        )
                        y_true = encoder.transform(y_true)
                        class_names = [str(name) for name in encoder.classes_]
                    else:
                        y_true = pd.to_numeric(self._df[target_col], errors="coerce").fillna(0).astype(int).to_numpy()
                        class_names = [str(value) for value in sorted(np.unique(y_true))]
                    y_pred = model.predict(X_scaled)
                    matrix = confusion_matrix(y_true, y_pred)
                    image = self._ax.imshow(matrix, cmap="Blues", interpolation="nearest")
                    self._fig.colorbar(image, ax=self._ax, fraction=0.04, pad=0.03)
                    self._ax.set_title("Matriz de confusion")
                    self._ax.set_xlabel("Prediccion")
                    self._ax.set_ylabel("Referencia")
                    ticks = list(range(len(class_names)))
                    self._ax.set_xticks(ticks)
                    self._ax.set_yticks(ticks)
                    self._ax.set_xticklabels(class_names, rotation=45, ha="right", fontsize=8)
                    self._ax.set_yticklabels(class_names, fontsize=8)
                    for row_index in range(matrix.shape[0]):
                        for col_index in range(matrix.shape[1]):
                            self._ax.text(
                                col_index,
                                row_index,
                                str(int(matrix[row_index, col_index])),
                                ha="center",
                                va="center",
                                color="#11161f" if matrix[row_index, col_index] > matrix.max() / 2 else text_c,
                                fontsize=8,
                            )
                    _style_ax(self._ax)
                else:
                    y_true = pd.to_numeric(self._df[target_col], errors="coerce").fillna(0).to_numpy()
                    y_pred = model.predict(X_scaled)
                    mn = min(float(np.min(y_true)), float(np.min(y_pred)))
                    mx = max(float(np.max(y_true)), float(np.max(y_pred)))
                    self._ax.scatter(y_true, y_pred, color="#4c81ff", alpha=0.55, edgecolors="none", s=28)
                    self._ax.plot([mn, mx], [mn, mx], color="#ff8aa5", linewidth=1.4, linestyle="--")
                    self._ax.set_xlabel("Valor Real")
                    self._ax.set_ylabel("Prediccion")
                    self._ax.set_title("Predicciones vs Referencia")
                    _style_ax(self._ax)

            elif chart_name == "Distribucion de seguridad":
                _, confidences = self._predict_with_confidence(X_scaled)
                self._ax.hist(confidences, bins=20, color="#8ab1ff", edgecolor="#11161f", alpha=0.9)
                self._ax.set_xlabel("% Seguridad")
                self._ax.set_ylabel("Frecuencia")
                self._ax.set_title("Distribucion de seguridad")
                _style_ax(self._ax)

            else:
                weights = getattr(model, "coefs_", None)
                if weights:
                    matrix = weights[0]
                    heatmap = self._ax.imshow(matrix, aspect="auto", cmap="Blues", interpolation="nearest")
                    self._fig.colorbar(heatmap, ax=self._ax, fraction=0.04, pad=0.03)
                    self._ax.set_title("Pesos de la primera capa")
                    self._ax.set_xlabel("Neurona oculta")
                    self._ax.set_ylabel("Feature")
                    self._ax.set_yticks(range(len(features)))
                    self._ax.set_yticklabels(features, fontsize=8)
                else:
                    self._ax.text(
                        0.5,
                        0.5,
                        "No hay pesos disponibles para visualizar.",
                        ha="center",
                        va="center",
                        color=text_c,
                        fontsize=11,
                        transform=self._ax.transAxes,
                    )
                _style_ax(self._ax)

            self._fig.tight_layout(pad=1.5)
            self._canvas.draw()
            self._set_viz_status(f"Grafico generado: {chart_name}", "status-success")
        except Exception as exc:
            self._set_viz_status(f"Error al generar grafico: {exc}", "status-error")
            logging.error(f"Error visualizacion MLP: {exc}")

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

    def _sync_controls_with_bundle(self, bundle: dict):
        config = bundle.get("training_config", {})
        hidden_layers = config.get("hidden_layers")
        if hidden_layers:
            self.input_layers.setText(",".join(str(value) for value in hidden_layers))
        activation = config.get("activation")
        if activation:
            self.combo_activation.setCurrentText(str(activation))
        task_mode = config.get("task_mode")
        if task_mode:
            self.combo_task.setCurrentText(str(task_mode))
        target_col = bundle.get("target_column")
        if target_col and target_col in [self.combo_target.itemText(i) for i in range(self.combo_target.count())]:
            self.combo_target.setCurrentText(target_col)

    @staticmethod
    def _task_label(task_type: str | None) -> str:
        return {
            "classification": "Clasificacion",
            "regression": "Regresion",
        }.get(task_type, "Desconocida")

    def load_bundle(self, bundle: dict):
        self._bundle = bundle
        self._df = None
        self._last_metrics = None
        self.ds_input.setText("")
        self.combo_target.clear()
        self.combo_target.setEnabled(False)
        self._sync_controls_with_bundle(bundle)

        self.btn_export.setEnabled(True)
        self.btn_infer.setEnabled(True)
        self.btn_infer_manual.setEnabled(True)
        self.progress_bar.setVisible(False)

        features = bundle.get("features", [])
        self._set_inference_headers(features)
        self.inf_table.setRowCount(0)

        self._log("-" * 55)
        self._log("[OK] Modelo MLP cargado desde archivo.", color="#8ab1ff")
        self._log(f"  Tipo de tarea            : {self._task_label(bundle.get('task_type'))}")
        self._log(f"  Features esperadas       : {len(features)}")
        self._log("Listo para inferencia.", color="#cccccc")
        logging.info("Modelo MLP inyectado en la vista exitosamente.")

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
        self.combo_target.clear()
        self.combo_target.setEnabled(False)
        self.combo_task.setCurrentText("Auto")
        self.input_layers.setText("64,32")
        self.combo_activation.setCurrentText("relu")
        self.spin_alpha.setValue(0.0001)
        self.spin_learning_rate.setValue(0.001)
        self.spin_max_iter.setValue(300)
        self.spin_test.setValue(20)

        self.btn_export.setEnabled(False)
        self.btn_infer.setEnabled(False)
        self.btn_infer_manual.setEnabled(False)

        self.inf_table.setRowCount(0)
        self.inf_table.setColumnCount(3)
        self.inf_table.setHorizontalHeaderLabels(["Muestra", "Prediccion", "% Seguridad"])

        self._log("-" * 55)
        self._log("[Info] Nuevo modelo MLP inicializado.", color="#cccccc")
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
