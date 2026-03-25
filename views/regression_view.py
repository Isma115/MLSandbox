"""
Vista de Regresion — Se han movido los imports de pandas, sklearn y joblib
al nivel global dado que pandas ahora se importa tempranamente en main.py para
evitar el conflicto con el hook de shiboken/PySide6.
"""
import logging
import os
import pandas as pd
import joblib
from sklearn.linear_model import LinearRegression, Ridge, Lasso, ElasticNet
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
import numpy as np
from PySide6.QtCore import Qt, QThread, Signal, QEvent
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QComboBox, QDoubleSpinBox,
    QTextEdit, QFileDialog, QSpinBox, QFrame, QGroupBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QProgressBar, QMessageBox, QScrollArea,
    QSizePolicy
)
from PySide6.QtGui import QFont
from core.components import CollapsibleBox
from core.styles import apply_stylesheet, set_dynamic_property
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas


# ─────────────────────────────────────────────────────────────────────────────
# Worker de entrenamiento (hilo separado para no bloquear la UI)
# ─────────────────────────────────────────────────────────────────────────────

class TrainingWorker(QThread):
    finished = Signal(object, dict)   # bundle entrenado, métricas
    error    = Signal(str)
    progress = Signal(int)

    def __init__(self, df, target_col: str, reg_type: str,
                 alpha: float, test_size: float):
        super().__init__()
        self.df         = df
        self.target_col = target_col
        self.reg_type   = reg_type
        self.alpha      = alpha
        self.test_size  = test_size

    def run(self):
        try:
            self.progress.emit(10)
            X = self.df.drop(columns=[self.target_col]).copy()
            y = self.df[self.target_col].copy()

            label_encoders = {}
            
            # Handle target variable if it's categorical/text
            if y.dtype == 'object' or str(y.dtype) == 'category' or str(y.dtype) == 'string':
                le_y = LabelEncoder()
                y = pd.Series(le_y.fit_transform(y.astype(str)), index=y.index)
                label_encoders['target'] = le_y

            # Handle features if they are categorical/text
            for col in X.columns:
                if X[col].dtype == 'object' or str(X[col].dtype) == 'category' or str(X[col].dtype) == 'string':
                    le = LabelEncoder()
                    X[col] = le.fit_transform(X[col].astype(str))
                    label_encoders[col] = le
            
            # Fill NaNs for safety
            self.progress.emit(30)
            X = X.apply(pd.to_numeric, errors='coerce').fillna(0)
            y = pd.to_numeric(y, errors='coerce').fillna(0)

            if X.empty:
                self.error.emit("El dataset no contiene columnas usables como features.")
                return

            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=self.test_size, random_state=42
            )

            scaler = StandardScaler()
            self.progress.emit(60)
            X_train_s = scaler.fit_transform(X_train)
            X_test_s  = scaler.transform(X_test)

            reg_map = {
                "Ninguna (OLS)": LinearRegression(),
                "Ridge (L2)":    Ridge(alpha=self.alpha),
                "Lasso (L1)":    Lasso(alpha=self.alpha, max_iter=10000),
                "ElasticNet":    ElasticNet(alpha=self.alpha, max_iter=10000),
            }
            model = reg_map.get(self.reg_type, LinearRegression())
            model.fit(X_train_s, y_train)

            self.progress.emit(80)
            y_pred = model.predict(X_test_s)
            mse  = mean_squared_error(y_test, y_pred)
            rmse = float(mse) ** 0.5
            mae  = mean_absolute_error(y_test, y_pred)
            r2   = r2_score(y_test, y_pred)

            metrics = {
                "mse": mse, "rmse": rmse, "mae": mae, "r2": r2,
                "n_train": len(X_train), "n_test": len(X_test),
                "n_features": X_train.shape[1],
            }

            if "target" in label_encoders:
                max_class = len(label_encoders["target"].classes_) - 1
                pred_labels = np.rint(y_pred).astype(int)
                pred_labels = np.clip(pred_labels, 0, max_class)
                quality_score = float(np.mean(pred_labels == y_test.to_numpy(dtype=int)))
            else:
                quality_score = float(np.clip(r2, 0.0, 1.0))

            train_distances = np.mean(np.abs(X_train_s), axis=1)
            distance_reference = float(np.percentile(train_distances, 90)) if train_distances.size else 1.0
            if not np.isfinite(distance_reference) or distance_reference <= 0:
                distance_reference = 1.0

            metrics["quality_score"] = quality_score

            bundle = {
                "model": model,
                "scaler": scaler,
                "features": list(X.columns),
                "label_encoders": label_encoders,
                "confidence_stats": {
                    "quality_score": quality_score,
                    "distance_reference": distance_reference,
                },
            }
            self.progress.emit(100)
            self.finished.emit(bundle, metrics)

        except Exception as exc:
            self.error.emit(str(exc))


# ─────────────────────────────────────────────────────────────────────────────
# Vista principal
# ─────────────────────────────────────────────────────────────────────────────

class RegressionView(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("RegressionView")
        apply_stylesheet(self, "regression_view.qss")

        self._bundle = None   # dict con model, scaler, features
        self._df     = None   # DataFrame cargado (pandas, importado diferidamente)

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(16)

        # ── Sección: Entrenamiento (Desplegable) ─────────────────────────────
        self.train_box = CollapsibleBox("1. Entrenamiento de Modelo")
        root.addWidget(self.train_box)


        # -- Dataset --
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
        self.combo_target.setPlaceholderText("Primero carga un CSV...")
        self.combo_target.setEnabled(False)
        row2.addWidget(lbl_target)
        row2.addWidget(self.combo_target)
        row2.addStretch()
        self.train_box.add_layout(row2)

        # -- Hiperparametros --
        row3 = QHBoxLayout()
        lbl_reg = QLabel("Regularizacion:")
        lbl_reg.setFixedWidth(105)
        self.btn_reg_info = self._create_info_button(
            "Informacion sobre regularizacion",
            self._show_regularization_info,
        )
        self.combo_reg = QComboBox()
        self.combo_reg.addItems(["Ninguna (OLS)", "Ridge (L2)", "Lasso (L1)", "ElasticNet"])
        self.combo_reg.currentIndexChanged.connect(self._toggle_alpha)

        lbl_alpha = QLabel("Alpha:")
        lbl_alpha.setFixedWidth(80)
        self.btn_alpha_info = self._create_info_button(
            "Informacion sobre alpha",
            self._show_alpha_info,
        )
        self.spin_alpha = QDoubleSpinBox()
        self.spin_alpha.setRange(0.0001, 100.0)
        self.spin_alpha.setValue(1.0)
        self.spin_alpha.setSingleStep(0.1)

        lbl_test = QLabel("% Test:")
        lbl_test.setFixedWidth(95)
        self.btn_test_info = self._create_info_button(
            "Informacion sobre porcentaje de test",
            self._show_test_split_info,
        )
        self.spin_test = QSpinBox()
        self.spin_test.setRange(5, 50)
        self.spin_test.setValue(20)
        self.spin_test.setSuffix(" %")

        row3.addWidget(lbl_reg)
        row3.addWidget(self.btn_reg_info)
        row3.addWidget(self.combo_reg)
        row3.addSpacing(20)
        row3.addWidget(lbl_alpha)
        row3.addWidget(self.btn_alpha_info)
        row3.addWidget(self.spin_alpha)
        row3.addSpacing(20)
        row3.addWidget(lbl_test)
        row3.addWidget(self.btn_test_info)
        row3.addWidget(self.spin_test)
        row3.addStretch()
        self.train_box.add_layout(row3)


        # ── Botones de acción ─────────────────────────────────────────────────
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

        # ── Sección: Inferencia ───────────────────────────────────────────────
        self.inf_box = CollapsibleBox("2. Inferencia y Pruebas")
        root.addWidget(self.inf_box)

        # -- Inferencia --
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

        # -- Seccion: Muestras de Datos ------------------------------------------
        self.datos_box = CollapsibleBox("3. Muestras de Datos")
        root.addWidget(self.datos_box)

        # -- Muestras de Datos --
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
        
        # ── Sección: Visualización del Modelo ────────────────────────────────
        self.viz_box = CollapsibleBox("4. Visualizacion del Modelo")
        root.addWidget(self.viz_box)
        self._build_visualization_section()

        # ── Sección: Exportación ──────────────────────────────────────────────
        self.export_box = CollapsibleBox("5. Exportacion")
        root.addWidget(self.export_box)
        
        # -- Exportacion --
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
        
        # ── Log de entrenamiento (Consola) ────────────────────────────────────
        self.console_box = CollapsibleBox("6. Resultados")
        root.addWidget(self.console_box)
        
        self.output_log = QTextEdit()
        self.output_log.setReadOnly(True)
        self.output_log.setFixedHeight(150)
        self.console_box.add_widget(self.output_log)
        
        root.addStretch()

        # Estado inicial de alpha
        self._toggle_alpha(0)
        self._install_training_guards()
        
        # Colapsar subsecciones 2, 3, 4, 5 pero mantener Resultados visible
        self.inf_box.collapse()
        self.datos_box.collapse()
        self.viz_box.collapse()
        self.export_box.collapse()
        self.console_box.expand()

    # ── Lógica: carga de dataset ───────────────────────────────────────────────

    def _browse_dataset(self):
        examples_dir = os.path.join(os.path.dirname(__file__), "..", "examples")
        ruta, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar Dataset CSV",
            os.path.abspath(examples_dir),
            "CSV (*.csv);;Todos los archivos (*)"
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

        rows, cols = df.shape
        self._log(f"[OK] Dataset cargado: {os.path.basename(ruta)} "
                  f"— {rows} filas, {cols} columnas.", color="#8ab1ff")
        self._populate_samples()

    # ── Lógica: entrenamiento ──────────────────────────────────────────────────

    def _on_train(self):
        if self._df is None:
            self._show_missing_dataset_warning()
            return

        target = self.combo_target.currentText()
        if not target:
            self._log("[Error] Selecciona una columna como variable objetivo.", color="#ff8aa5")
            return

        reg_type  = self.combo_reg.currentText()
        alpha     = self.spin_alpha.value()
        test_size = self.spin_test.value() / 100.0

        self._log(f"[Info] Iniciando entrenamiento — tipo: {reg_type} | target: {target} "
                  f"| alpha: {alpha} | test_size: {test_size:.0%}")

        self.btn_train.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self._worker = TrainingWorker(self._df, target, reg_type, alpha, test_size)
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

        self._log("─" * 55)
        self._log(f"  Muestras de entrenamiento : {metrics['n_train']}")
        self._log(f"  Muestras de test          : {metrics['n_test']}")
        self._log(f"  Features utilizadas       : {metrics['n_features']}")
        self._log(f"  MSE                       : {metrics['mse']:.6f}")
        self._log(f"  RMSE                      : {metrics['rmse']:.6f}")
        self._log(f"  MAE                       : {metrics['mae']:.6f}")
        self._log(f"  R2 Score                  : {metrics['r2']:.6f}")
        self._log(f"  Calidad base confianza    : {metrics['quality_score']:.2%}")
        self._log("─" * 55)
        self._log("[OK] Modelo entrenado correctamente.", color="#8ab1ff")
        logging.info(
            f"Modelo de Regresion entrenado. R2={metrics['r2']:.4f} | RMSE={metrics['rmse']:.4f}"
        )
        self._populate_samples()
        self._refresh_charts()

    def _on_training_error(self, msg: str):
        self.btn_train.setEnabled(True)
        self.progress_bar.setVisible(False)
        self._log(f"[Error] {msg}", color="#ff8aa5")
        logging.error(f"Error en entrenamiento de Regresion: {msg}")

    # ── Lógica: exportación ────────────────────────────────────────────────────

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
        elif "JSON" in formato:
            ext = ".json"
            filtro = "JSON (*.json);;Todos los archivos (*)"
        else:
            ext = ".pkl"
            filtro = "Pickle (*.pkl);;Todos los archivos (*)"

        ruta, _ = QFileDialog.getSaveFileName(
            self, "Exportar Modelo", f"modelo_regresion{ext}", filtro
        )
        if not ruta:
            return

        try:
            if ext == ".json":
                import json
                model = self._bundle["model"]
                data = {
                    "tipo": type(model).__name__,
                    "features": self._bundle["features"]
                }
                if hasattr(model, "coef_"):
                    data["coeficientes"] = model.coef_.tolist()
                if hasattr(model, "intercept_"):
                    data["intercepto"] = float(model.intercept_)
                
                with open(ruta, "w") as f:
                    json.dump(data, f, indent=4)
            else:
                import joblib
                joblib.dump(self._bundle, ruta)
                
            self._log(f"[OK] Modelo exportado ({ext}): {ruta}", color="#8ab1ff")
            logging.info(f"Modelo de Regresion exportado a: {ruta}")
        except Exception as exc:
            self._log(f"[Error] No se pudo guardar: {exc}", color="#ff8aa5")

    # ── Lógica: inferencia ─────────────────────────────────────────────────────

    def _browse_inference(self):
        ruta, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar CSV para Inferencia", "",
            "CSV (*.csv);;Todos los archivos (*)"
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
        missing  = [c for c in features if c not in df_infer.columns]
        if missing:
            self._log(f"[Error] Faltan columnas en el CSV: {missing}", color="#ff8aa5")
            return

        try:
            X = df_infer[features].copy()
            encoders = self._bundle.get("label_encoders", {})
            for col in features:
                if col in encoders:
                    le = encoders[col]
                    known_classes = set(le.classes_)
                    X[col] = X[col].astype(str).map(lambda x: x if x in known_classes else le.classes_[0])
                    X[col] = le.transform(X[col].astype(str))
                else:
                    X[col] = pd.to_numeric(X[col], errors='coerce').fillna(0)

            X_s = self._bundle["scaler"].transform(X)
            preds = self._bundle["model"].predict(X_s)
            confidences = self._estimate_prediction_confidence(X_s)
        except Exception as exc:
            self._log(f"[Error] Fallo durante la inferencia: {exc}", color="#ff8aa5")
            return

        self.inf_table.setRowCount(0)
        for i, (idx, row_series) in enumerate(df_infer.iterrows()):
            if i >= 200: break
            row = self.inf_table.rowCount()
            self.inf_table.insertRow(row)
            
            for j, col_name in enumerate(features):
                val = str(row_series.get(col_name, ""))
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignCenter)
                self.inf_table.setItem(row, j, item)
                
            pred = preds[i]
            
            encoders = self._bundle.get("label_encoders", {})
            if "target" in encoders:
                le_y = encoders["target"]
                pred_int = int(round(pred))
                pred_int = max(0, min(pred_int, len(le_y.classes_) - 1))
                pred_display = str(le_y.inverse_transform([pred_int])[0])
            else:
                pred_display = f"{pred:.6f}"
                
            item_pred = QTableWidgetItem(pred_display)
            item_pred.setTextAlignment(Qt.AlignCenter)
            self.inf_table.setItem(row, len(features), item_pred)

            item_conf = QTableWidgetItem(self._format_confidence(confidences[i]))
            item_conf.setTextAlignment(Qt.AlignCenter)
            self.inf_table.setItem(row, len(features) + 1, item_conf)

        avg_conf = float(np.mean(confidences)) if len(confidences) else 0.0
        self._log(
            f"[OK] Inferencia completada: {len(preds)} predicciones generadas. "
            f"Seguridad media: {self._format_confidence(avg_conf)}",
            color="#8ab1ff"
        )
        logging.info(f"Inferencia de Regresion completada: {len(preds)} muestras.")

    def _on_infer_manual(self):
        if self._bundle is None:
            self._log("[Error] Primero entrena o carga un modelo.", color="#ff8aa5")
            return

        features = self._bundle.get("features", [])
        
        from core.dialogs import ManualInferenceDialog
        dialog = ManualInferenceDialog(features, parent=self)
        if dialog.exec():
            values_dict = dialog.get_values()
            
            try:
                # build dataframe from dict
                df_infer = pd.DataFrame([values_dict])
                
                # apply same transformations
                X = df_infer.copy()
                encoders = self._bundle.get("label_encoders", {})
                for col in features:
                    if col in encoders:
                        le = encoders[col]
                        known_classes = set(le.classes_)
                        X[col] = X[col].astype(str).map(lambda x: x if x in known_classes else le.classes_[0])
                        X[col] = le.transform(X[col].astype(str))
                    else:
                        X[col] = pd.to_numeric(X[col], errors='coerce').fillna(0)

                X_s = self._bundle["scaler"].transform(X)
                pred = self._bundle["model"].predict(X_s)[0]
                confidence = self._estimate_prediction_confidence(X_s)[0]
                
                encoders = self._bundle.get("label_encoders", {})
                if "target" in encoders:
                    le_y = encoders["target"]
                    pred_int = int(round(pred))
                    pred_int = max(0, min(pred_int, len(le_y.classes_) - 1))
                    pred_display = str(le_y.inverse_transform([pred_int])[0])
                else:
                    pred_display = f"{pred:.6f}"
                
                # Update table
                row = self.inf_table.rowCount()
                self.inf_table.insertRow(row)
                for i, col_name in enumerate(features):
                    val = str(values_dict.get(col_name, ""))
                    item = QTableWidgetItem(val)
                    item.setTextAlignment(Qt.AlignCenter)
                    self.inf_table.setItem(row, i, item)
                    
                item_pred = QTableWidgetItem(pred_display)
                item_pred.setTextAlignment(Qt.AlignCenter)
                self.inf_table.setItem(row, len(features), item_pred)

                item_conf = QTableWidgetItem(self._format_confidence(confidence))
                item_conf.setTextAlignment(Qt.AlignCenter)
                self.inf_table.setItem(row, len(features) + 1, item_conf)
                
                self._log(
                    f"[OK] Inferencia manual completada. Prediccion: {pred_display} | "
                    f"Seguridad: {self._format_confidence(confidence)}",
                    color="#8ab1ff"
                )
                logging.info(
                    f"Resultado inferencia manual: {pred_display} | seguridad={confidence:.2f}%"
                )
                
            except Exception as exc:
                self._log(f"[Error] Fallo durante la inferencia manual: {exc}", color="#ff8aa5")

    # ── Helpers ────────────────────────────────────────────────────────────────

    def _toggle_alpha(self, index: int):
        self.spin_alpha.setEnabled(index > 0)

    def _show_regularization_info(self):
        message = (
            "Regularizacion:\n"
            "En este contexto sirve para limitar como de agresivamente se ajusta el modelo "
            "a los datos de entrenamiento, reduciendo el riesgo de sobreajuste.\n\n"
            "Metodos disponibles:\n"
            "- Ninguna (OLS): ajusta el modelo sin penalizar coeficientes.\n"
            "- Ridge (L2): penaliza coeficientes grandes de forma suave y suele dar "
            "estabilidad cuando varias variables estan relacionadas.\n"
            "- Lasso (L1): puede llevar algunos coeficientes a cero, ayudando a simplificar "
            "el modelo y a descartar variables poco utiles.\n"
            "- ElasticNet: combina L1 y L2 para equilibrar simplificacion y estabilidad.\n\n"
            "Alpha controla la fuerza de la penalizacion: a mayor valor, mas restrictivo es "
            "el ajuste del modelo."
        )
        QMessageBox.information(self, "Informacion de Regularizacion", message)

    def _show_alpha_info(self):
        message = (
            "Alpha:\n"
            "Es la intensidad de la regularizacion.\n\n"
            "- Un valor mas bajo deja que el modelo se ajuste con mas libertad.\n"
            "- Un valor mas alto penaliza mas los coeficientes y hace el modelo mas conservador.\n"
            "- Solo afecta a Ridge, Lasso y ElasticNet. En OLS no se usa.\n\n"
            "Si el modelo se ajusta demasiado a los datos de entrenamiento, subir alpha puede ayudar. "
            "Si pierde demasiada capacidad de ajuste, conviene bajarlo."
        )
        QMessageBox.information(self, "Informacion de Alpha", message)

    def _show_test_split_info(self):
        message = (
            "% Test:\n"
            "Indica que porcentaje del dataset se reserva para evaluar el modelo tras entrenarlo.\n\n"
            "- El resto de muestras se usa para entrenamiento.\n"
            "- Un porcentaje mayor da una evaluacion mas exigente, pero deja menos datos para aprender.\n"
            "- Un porcentaje menor deja mas datos para entrenamiento, pero la evaluacion puede ser menos representativa.\n\n"
            "Como punto de partida, 20 % suele ser una division equilibrada para muchos datasets."
        )
        QMessageBox.information(self, "Informacion de % Test", message)

    def _install_training_guards(self):
        """Muestra un aviso si se tocan controles de entrenamiento sin dataset."""
        self._training_guarded_widgets = [
            self.train_box.toggle_button,
            self.combo_reg,
            self.spin_alpha,
            self.spin_alpha.lineEdit(),
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
        message = (
            "No hay ningun dataset cargado. Carga un CSV en la seccion de "
            "entrenamiento."
        )
        self._log(f"[Aviso] {message}", color="#d8b46a")
        QMessageBox.warning(self, "Dataset no cargado", message)

    def _populate_samples(self):
        """Rellena la tabla de muestras con las filas del dataset cargado."""
        if self._df is None:
            return
        n = self.spin_samples.value()
        df_slice = self._df.head(n)
        self._fill_samples_table(df_slice)

    def _filter_samples(self, text: str):
        """Filtra las filas de la tabla de muestras por el texto buscado."""
        if self._df is None:
            return
        n = self.spin_samples.value()
        df_slice = self._df.head(n)
        if text.strip():
            mask = df_slice.apply(
                lambda row: row.astype(str).str.contains(text, case=False, na=False).any(),
                axis=1
            )
            df_slice = df_slice[mask]
        self._fill_samples_table(df_slice)

    def _fill_samples_table(self, df):
        """Puebla self.samples_table con el DataFrame recibido."""
        self.samples_table.setRowCount(0)
        self.samples_table.setColumnCount(len(df.columns))
        self.samples_table.setHorizontalHeaderLabels(list(df.columns))
        for _, row_data in df.iterrows():
            row_idx = self.samples_table.rowCount()
            self.samples_table.insertRow(row_idx)
            for col_idx, val in enumerate(row_data):
                item = QTableWidgetItem(str(val))
                item.setTextAlignment(Qt.AlignCenter)
                self.samples_table.setItem(row_idx, col_idx, item)

    def _set_inference_headers(self, features):
        self.inf_table.setColumnCount(len(features) + 2)
        self.inf_table.setHorizontalHeaderLabels(features + ["Prediccion", "% Seguridad"])

    def _estimate_prediction_confidence(self, X_scaled) -> np.ndarray:
        stats = (self._bundle or {}).get("confidence_stats", {})
        quality_score = float(np.clip(stats.get("quality_score", 0.5), 0.0, 1.0))
        distance_reference = float(stats.get("distance_reference", 1.0))
        if not np.isfinite(distance_reference) or distance_reference <= 0:
            distance_reference = 1.0

        X_scaled = np.atleast_2d(np.asarray(X_scaled, dtype=float))
        distances = np.mean(np.abs(X_scaled), axis=1)
        proximity_score = np.exp(-distances / distance_reference)
        confidences = (0.6 * proximity_score + 0.4 * quality_score) * 100.0
        return np.clip(confidences, 1.0, 99.0)

    @staticmethod
    def _format_confidence(value: float) -> str:
        return f"{value:.1f} %"



    # ── Sección: Visualización ─────────────────────────────────────────────────

    def _build_visualization_section(self):
        """Construye el widget de visualizacion con graficos de matplotlib embebidos."""
        self._last_metrics = None
        self._chart_type = "pred_vs_real"

        viz_layout = QVBoxLayout()
        viz_layout.setSpacing(10)

        # Selector de tipo de grafico
        ctrl_row = QHBoxLayout()
        lbl_chart = QLabel("Grafico:")
        lbl_chart.setFixedWidth(60)
        lbl_chart.setProperty("tone", "section")

        self.combo_chart = QComboBox()
        self.combo_chart.addItems([
            "Predicciones vs Valores Reales",
            "Residuos",
            "Importancia de Variables",
            "Distribucion de Errores",
        ])
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

        # Canvas de matplotlib
        self._fig, self._ax = plt.subplots(figsize=(8, 4))
        self._fig.patch.set_facecolor("#11161f")
        self._ax.set_facecolor("#0d121a")
        self._canvas = FigureCanvas(self._fig)
        self._canvas.setObjectName("RegressionChartCanvas")
        self._canvas.setMinimumHeight(320)
        self._canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        viz_layout.addWidget(self._canvas)

        # Etiqueta de estado
        self._viz_status = QLabel("Entrena un modelo para visualizar los graficos.")
        self._set_viz_status_tone("status-muted")
        viz_layout.addWidget(self._viz_status)

        self.viz_box.add_layout(viz_layout)

    def _on_chart_type_changed(self, _index: int):
        """Refresca el grafico cuando cambia la seleccion."""
        if self._bundle is not None:
            self._refresh_charts()

    def _refresh_charts(self):
        """Regenera el grafico seleccionado con los datos del modelo actual."""
        if self._bundle is None or self._df is None:
            self._set_viz_status("Carga un dataset y entrena el modelo para visualizar.", "status-muted")
            return

        chart_name = self.combo_chart.currentText()
        self._ax.clear()
        self._fig.patch.set_facecolor("#11161f")
        self._ax.set_facecolor("#0d121a")

        try:
            # Preparar datos
            target_col = self.combo_target.currentText()
            if not target_col or target_col not in self._df.columns:
                self._set_viz_status("Selecciona la variable objetivo para generar graficos.", "status-muted")
                return

            X_raw = self._df.drop(columns=[target_col]).copy()
            y_raw = self._df[target_col].copy()

            encoders = self._bundle.get("label_encoders", {})
            y_is_categorical = "target" in encoders

            # Codificar features igual que el entrenamiento
            features = self._bundle["features"]
            X = X_raw[features].copy()
            for col in features:
                if col in encoders:
                    le = encoders[col]
                    known = set(le.classes_)
                    X[col] = X[col].astype(str).map(lambda v, k=known, l=le: v if v in k else l.classes_[0])
                    X[col] = encoders[col].transform(X[col].astype(str))
                else:
                    X[col] = pd.to_numeric(X[col], errors="coerce").fillna(0)

            if y_is_categorical:
                le_y = encoders["target"]
                y_num = pd.Series(le_y.transform(y_raw.astype(str).map(
                    lambda v: v if v in set(le_y.classes_) else le_y.classes_[0]
                )), index=y_raw.index)
            else:
                y_num = pd.to_numeric(y_raw, errors="coerce").fillna(0)

            X_s = self._bundle["scaler"].transform(X)
            y_pred = self._bundle["model"].predict(X_s)
            y_true = y_num.to_numpy()
            residuals = y_true - y_pred

            # ── Estilos comunes ────────────────────────────────────────────────
            accent   = "#4c81ff"
            accent2  = "#b7a6ff"
            grid_c   = "#263042"
            text_c   = "#dbe3f6"
            tick_c   = "#92a0bb"

            def _style_ax(ax):
                ax.set_facecolor("#0d121a")
                ax.tick_params(colors=tick_c, labelsize=9)
                ax.xaxis.label.set_color(text_c)
                ax.yaxis.label.set_color(text_c)
                ax.title.set_color(text_c)
                for spine in ax.spines.values():
                    spine.set_edgecolor(grid_c)
                ax.grid(True, color=grid_c, linewidth=0.6, linestyle="--", alpha=0.7)

            if chart_name == "Predicciones vs Valores Reales":
                self._ax.scatter(y_true, y_pred, color=accent, alpha=0.55,
                                 edgecolors="none", s=28)
                mn = min(y_true.min(), y_pred.min())
                mx = max(y_true.max(), y_pred.max())
                self._ax.plot([mn, mx], [mn, mx], color="#ff8aa5",
                              linewidth=1.4, linestyle="--", label="Ideal")
                self._ax.set_xlabel("Valor Real")
                self._ax.set_ylabel("Prediccion")
                self._ax.set_title("Predicciones vs Valores Reales")
                self._ax.legend(facecolor="#11161f", edgecolor=grid_c,
                                labelcolor=text_c, fontsize=9)
                _style_ax(self._ax)

            elif chart_name == "Residuos":
                self._ax.scatter(y_pred, residuals, color=accent2, alpha=0.55,
                                 edgecolors="none", s=28)
                self._ax.axhline(0, color="#ff8aa5", linewidth=1.4, linestyle="--")
                self._ax.set_xlabel("Prediccion")
                self._ax.set_ylabel("Residuo (Real - Prediccion)")
                self._ax.set_title("Grafico de Residuos")
                _style_ax(self._ax)

            elif chart_name == "Importancia de Variables":
                model = self._bundle["model"]
                if hasattr(model, "coef_"):
                    coefs = np.abs(model.coef_)
                    feat_labels = features
                    # Ordenar de mayor a menor
                    order = np.argsort(coefs)[::-1][:15]  # top-15
                    coefs_sorted = coefs[order]
                    labels_sorted = [feat_labels[i] for i in order]
                    bars = self._ax.barh(range(len(labels_sorted)), coefs_sorted,
                                        color=accent, edgecolor="none", height=0.6)
                    self._ax.set_yticks(range(len(labels_sorted)))
                    self._ax.set_yticklabels(labels_sorted, fontsize=9)
                    self._ax.invert_yaxis()
                    self._ax.set_xlabel("|Coeficiente| (magnitud)")
                    self._ax.set_title("Importancia de Variables (|coef|)")
                    _style_ax(self._ax)
                else:
                    self._ax.text(0.5, 0.5,
                                  "Este tipo de modelo no expone coeficientes lineales.",
                                  ha="center", va="center", color=text_c, fontsize=11,
                                  transform=self._ax.transAxes)
                    self._ax.set_title("Importancia de Variables")
                    _style_ax(self._ax)

            elif chart_name == "Distribucion de Errores":
                self._ax.hist(residuals, bins=30, color=accent, edgecolor="#11161f",
                              alpha=0.85)
                self._ax.axvline(0, color="#ff8aa5", linewidth=1.4, linestyle="--")
                mean_res = float(np.mean(residuals))
                self._ax.axvline(mean_res, color="#8ab1ff", linewidth=1.2,
                                 linestyle="-", label=f"Media: {mean_res:.3f}")
                self._ax.set_xlabel("Residuo")
                self._ax.set_ylabel("Frecuencia")
                self._ax.set_title("Distribucion de Errores")
                self._ax.legend(facecolor="#11161f", edgecolor=grid_c,
                                labelcolor=text_c, fontsize=9)
                _style_ax(self._ax)

            self._fig.tight_layout(pad=1.5)
            self._canvas.draw()
            self._set_viz_status(f"Grafico generado: {chart_name}", "status-success")

        except Exception as exc:
            self._set_viz_status(f"Error al generar grafico: {exc}", "status-error")
            logging.error(f"Error visualizacion regresion: {exc}")

    def _log(self, msg: str, color: str = "#cccccc"):
        self.output_log.append(f"<span style='color:{color};'>{msg}</span>")

    @staticmethod
    def _group(title: str) -> QGroupBox:
        g = QGroupBox(title)
        g.setProperty("card", True)
        lay = QVBoxLayout(g)
        lay.setSpacing(10)
        lay.setContentsMargins(14, 14, 14, 14)
        return g

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
        self.ds_input.setText("")
        self.combo_target.clear()
        self.combo_target.setEnabled(False)
        
        self.btn_export.setEnabled(True)
        self.btn_infer.setEnabled(True)
        self.btn_infer_manual.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        features = bundle.get("features", [])
        self._set_inference_headers(features)
        self.inf_table.setRowCount(0)
        
        self._log("─" * 55)
        self._log(f"[OK] Modelo cargado desde archivo.", color="#8ab1ff")
        self._log(f"  Features esperadas: {len(features)}", color="#cccccc")
        self._log("Listo para inferencia.", color="#cccccc")
        logging.info("Modelo de Regresión inyectado en la vista exitosamente.")
        
        self.train_box.expand()
        self.inf_box.collapse()
        self.viz_box.collapse()
        self.export_box.collapse()
        self.console_box.expand()
        self.btn_refresh_charts.setEnabled(False)
        self._last_metrics = None
        self._ax.clear()
        self._canvas.draw()
        self._set_viz_status("Entrena un modelo para visualizar los graficos.", "status-muted")

    def reset_view(self):
        self._bundle = None
        self._df = None
        self.ds_input.setText("")
        self.combo_target.clear()
        self.combo_target.setEnabled(False)
        
        self.btn_export.setEnabled(False)
        self.btn_infer.setEnabled(False)
        self.btn_infer_manual.setEnabled(False)
        
        self.inf_table.setRowCount(0)
        self.inf_table.setColumnCount(3)
        self.inf_table.setHorizontalHeaderLabels(["Muestra", "Prediccion", "% Seguridad"])
        
        self._log("─" * 55)
        self._log("[Info] Nuevo modelo de Regresión inicializado.", color="#cccccc")
        self._log("Selecciona un dataset CSV para empezar a entrenar.", color="#cccccc")

        self.train_box.expand()
        self.inf_box.collapse()
        self.viz_box.collapse()
        self.export_box.collapse()
        self.console_box.expand()
        self.btn_refresh_charts.setEnabled(False)
        self._last_metrics = None
        self._ax.clear()
        self._canvas.draw()
        self._set_viz_status("Entrena un modelo para visualizar los graficos.", "status-muted")
