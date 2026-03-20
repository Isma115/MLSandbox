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
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QComboBox, QDoubleSpinBox,
    QTextEdit, QFileDialog, QSpinBox, QFrame, QGroupBox, QTableWidget,
    QTableWidgetItem, QHeaderView
)


# ─────────────────────────────────────────────────────────────────────────────
# Worker de entrenamiento (hilo separado para no bloquear la UI)
# ─────────────────────────────────────────────────────────────────────────────

class TrainingWorker(QThread):
    finished = Signal(object, dict)   # bundle entrenado, métricas
    error    = Signal(str)

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
            X = X.apply(pd.to_numeric, errors='coerce').fillna(0)
            y = pd.to_numeric(y, errors='coerce').fillna(0)

            if X.empty:
                self.error.emit("El dataset no contiene columnas usables como features.")
                return

            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=self.test_size, random_state=42
            )

            scaler = StandardScaler()
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

            bundle = {"model": model, "scaler": scaler, "features": list(X.columns), "label_encoders": label_encoders}
            self.finished.emit(bundle, metrics)

        except Exception as exc:
            self.error.emit(str(exc))


# ─────────────────────────────────────────────────────────────────────────────
# Vista principal
# ─────────────────────────────────────────────────────────────────────────────

class RegressionView(QWidget):
    def __init__(self):
        super().__init__()

        self._bundle = None   # dict con model, scaler, features
        self._df     = None   # DataFrame cargado (pandas, importado diferidamente)

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(16)

        # ── Título ────────────────────────────────────────────────────────────
        title = QLabel("Entrenamiento: Modelo de Regresion")
        title.setStyleSheet("color:#d4d4d4; font-size:22px; font-weight:bold;")
        root.addWidget(title)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color:#333333;")
        root.addWidget(sep)

        # ── Sección: Dataset ──────────────────────────────────────────────────
        ds_group = self._group("Dataset")
        ds_layout = ds_group.layout()

        row1 = QHBoxLayout()
        lbl_ds = QLabel("Archivo CSV:")
        lbl_ds.setFixedWidth(130)
        self.ds_input = QLineEdit()
        self.ds_input.setPlaceholderText("Ruta al archivo dataset.csv...")
        self.ds_input.setReadOnly(True)
        self.ds_input.setStyleSheet(self._input_style())
        btn_browse = QPushButton("Explorar")
        btn_browse.setStyleSheet(self._btn_style())
        btn_browse.setCursor(Qt.PointingHandCursor)
        btn_browse.clicked.connect(self._browse_dataset)
        row1.addWidget(lbl_ds)
        row1.addWidget(self.ds_input)
        row1.addWidget(btn_browse)
        ds_layout.addLayout(row1)

        row2 = QHBoxLayout()
        lbl_target = QLabel("Variable objetivo:")
        lbl_target.setFixedWidth(130)
        self.combo_target = QComboBox()
        self.combo_target.setPlaceholderText("Carga un CSV primero...")
        self.combo_target.setEnabled(False)
        self.combo_target.setStyleSheet(self._combo_style())
        row2.addWidget(lbl_target)
        row2.addWidget(self.combo_target)
        row2.addStretch()
        ds_layout.addLayout(row2)

        root.addWidget(ds_group)

        # ── Sección: Hiperparámetros ──────────────────────────────────────────
        hp_group = self._group("Hiperparametros")
        hp_layout = hp_group.layout()

        row3 = QHBoxLayout()
        lbl_reg = QLabel("Regularizacion:")
        lbl_reg.setFixedWidth(130)
        self.combo_reg = QComboBox()
        self.combo_reg.addItems(["Ninguna (OLS)", "Ridge (L2)", "Lasso (L1)", "ElasticNet"])
        self.combo_reg.setStyleSheet(self._combo_style())
        self.combo_reg.currentIndexChanged.connect(self._toggle_alpha)

        lbl_alpha = QLabel("Alpha:")
        self.spin_alpha = QDoubleSpinBox()
        self.spin_alpha.setRange(0.0001, 100.0)
        self.spin_alpha.setValue(1.0)
        self.spin_alpha.setSingleStep(0.1)
        self.spin_alpha.setStyleSheet(self._input_style())

        lbl_test = QLabel("% Test:")
        self.spin_test = QSpinBox()
        self.spin_test.setRange(5, 50)
        self.spin_test.setValue(20)
        self.spin_test.setSuffix(" %")
        self.spin_test.setStyleSheet(self._input_style())

        row3.addWidget(lbl_reg)
        row3.addWidget(self.combo_reg)
        row3.addSpacing(30)
        row3.addWidget(lbl_alpha)
        row3.addWidget(self.spin_alpha)
        row3.addSpacing(30)
        row3.addWidget(lbl_test)
        row3.addWidget(self.spin_test)
        row3.addStretch()
        hp_layout.addLayout(row3)

        root.addWidget(hp_group)

        # ── Botones de acción ─────────────────────────────────────────────────
        actions_row = QHBoxLayout()
        self.btn_train = QPushButton("Entrenar Modelo")
        self.btn_train.setStyleSheet(self._btn_primary_style())
        self.btn_train.setCursor(Qt.PointingHandCursor)
        self.btn_train.clicked.connect(self._on_train)

        self.btn_export = QPushButton("Exportar Modelo")
        self.btn_export.setStyleSheet(self._btn_style())
        self.btn_export.setCursor(Qt.PointingHandCursor)
        self.btn_export.setEnabled(False)
        self.btn_export.clicked.connect(self._on_export)

        actions_row.addWidget(self.btn_train)
        actions_row.addWidget(self.btn_export)
        actions_row.addStretch()
        root.addLayout(actions_row)

        # ── Log de entrenamiento ──────────────────────────────────────────────
        lbl_log = QLabel("Resultados de entrenamiento:")
        lbl_log.setStyleSheet("color:#a0a0a0; font-size:13px;")
        root.addWidget(lbl_log)

        self.output_log = QTextEdit()
        self.output_log.setReadOnly(True)
        self.output_log.setFixedHeight(150)
        self.output_log.setStyleSheet(
            "background-color:#0d0d0d; color:#cccccc; border:1px solid #1a1a1a;"
            "font-family:monospace; font-size:12px; padding:10px;"
        )
        root.addWidget(self.output_log)

        # ── Sección: Inferencia ───────────────────────────────────────────────
        inf_group = self._group("Inferencia")
        inf_layout = inf_group.layout()

        row_inf = QHBoxLayout()
        lbl_inf = QLabel("CSV de entrada:")
        lbl_inf.setFixedWidth(130)
        self.inf_input = QLineEdit()
        self.inf_input.setPlaceholderText("Ruta al CSV con nuevos datos...")
        self.inf_input.setReadOnly(True)
        self.inf_input.setStyleSheet(self._input_style())
        btn_inf_browse = QPushButton("Explorar")
        btn_inf_browse.setStyleSheet(self._btn_style())
        btn_inf_browse.setCursor(Qt.PointingHandCursor)
        btn_inf_browse.clicked.connect(self._browse_inference)

        self.btn_infer = QPushButton("Inferir")
        self.btn_infer.setStyleSheet(self._btn_style())
        self.btn_infer.setCursor(Qt.PointingHandCursor)
        self.btn_infer.setEnabled(False)
        self.btn_infer.clicked.connect(self._on_infer)

        row_inf.addWidget(lbl_inf)
        row_inf.addWidget(self.inf_input)
        row_inf.addWidget(btn_inf_browse)
        row_inf.addWidget(self.btn_infer)
        inf_layout.addLayout(row_inf)

        self.inf_table = QTableWidget(0, 2)
        self.inf_table.setHorizontalHeaderLabels(["Muestra", "Prediccion"])
        self.inf_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.inf_table.setStyleSheet("""
            QTableWidget {
                background-color: #1a1a1a;
                color: #d4d4d4;
                border: 1px solid #333333;
                gridline-color: #2a2a2a;
                font-size: 13px;
            }
            QHeaderView::section {
                background-color: #252525;
                color: #d4d4d4;
                border: none;
                padding: 6px;
                font-weight: bold;
            }
            QTableWidget::item:selected { background-color: #333333; }
        """)
        self.inf_table.setFixedHeight(160)
        inf_layout.addWidget(self.inf_table)

        root.addWidget(inf_group)
        root.addStretch()

        # Estado inicial de alpha
        self._toggle_alpha(0)

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
            self._log(f"[Error] No se pudo leer el CSV: {exc}", color="#cc4444")
            return

        self._df = df
        self.ds_input.setText(ruta)

        self.combo_target.clear()
        self.combo_target.addItems(list(df.columns))
        self.combo_target.setEnabled(True)

        rows, cols = df.shape
        self._log(f"[OK] Dataset cargado: {os.path.basename(ruta)} "
                  f"— {rows} filas, {cols} columnas.", color="#88cc88")

    # ── Lógica: entrenamiento ──────────────────────────────────────────────────

    def _on_train(self):
        if self._df is None:
            self._log("[Error] Primero carga un archivo CSV.", color="#cc4444")
            return

        target = self.combo_target.currentText()
        if not target:
            self._log("[Error] Selecciona una columna como variable objetivo.", color="#cc4444")
            return

        reg_type  = self.combo_reg.currentText()
        alpha     = self.spin_alpha.value()
        test_size = self.spin_test.value() / 100.0

        self._log(f"[Info] Iniciando entrenamiento — tipo: {reg_type} | target: {target} "
                  f"| alpha: {alpha} | test_size: {test_size:.0%}")

        self.btn_train.setEnabled(False)
        self._worker = TrainingWorker(self._df, target, reg_type, alpha, test_size)
        self._worker.finished.connect(self._on_training_done)
        self._worker.error.connect(self._on_training_error)
        self._worker.start()

    def _on_training_done(self, bundle: dict, metrics: dict):
        self._bundle = bundle
        self.btn_train.setEnabled(True)
        self.btn_export.setEnabled(True)
        self.btn_infer.setEnabled(True)

        self._log("─" * 55)
        self._log(f"  Muestras de entrenamiento : {metrics['n_train']}")
        self._log(f"  Muestras de test          : {metrics['n_test']}")
        self._log(f"  Features utilizadas       : {metrics['n_features']}")
        self._log(f"  MSE                       : {metrics['mse']:.6f}")
        self._log(f"  RMSE                      : {metrics['rmse']:.6f}")
        self._log(f"  MAE                       : {metrics['mae']:.6f}")
        self._log(f"  R2 Score                  : {metrics['r2']:.6f}")
        self._log("─" * 55)
        self._log("[OK] Modelo entrenado correctamente.", color="#88cc88")
        logging.info(
            f"Modelo de Regresion entrenado. R2={metrics['r2']:.4f} | RMSE={metrics['rmse']:.4f}"
        )

    def _on_training_error(self, msg: str):
        self.btn_train.setEnabled(True)
        self._log(f"[Error] {msg}", color="#cc4444")
        logging.error(f"Error en entrenamiento de Regresion: {msg}")

    # ── Lógica: exportación ────────────────────────────────────────────────────

    def _on_export(self):
        if self._bundle is None:
            self._log("[Error] No hay ningun modelo entrenado para exportar.", color="#cc4444")
            return

        ruta, _ = QFileDialog.getSaveFileName(
            self, "Exportar Modelo", "modelo_regresion.pkl",
            "Pickle (*.pkl);;Todos los archivos (*)"
        )
        if not ruta:
            return

        try:
            joblib.dump(self._bundle, ruta)
            self._log(f"[OK] Modelo exportado: {ruta}", color="#88cc88")
            logging.info(f"Modelo de Regresion exportado a: {ruta}")
        except Exception as exc:
            self._log(f"[Error] No se pudo guardar: {exc}", color="#cc4444")

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
            self._log("[Error] Primero entrena o carga un modelo.", color="#cc4444")
            return

        ruta = self.inf_input.text().strip()
        if not ruta or not os.path.isfile(ruta):
            self._log("[Error] Especifica un CSV de entrada valido.", color="#cc4444")
            return

        try:
            df_infer = pd.read_csv(ruta)
        except Exception as exc:
            self._log(f"[Error] No se pudo leer el CSV: {exc}", color="#cc4444")
            return

        features = self._bundle["features"]
        missing  = [c for c in features if c not in df_infer.columns]
        if missing:
            self._log(f"[Error] Faltan columnas en el CSV: {missing}", color="#cc4444")
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
        except Exception as exc:
            self._log(f"[Error] Fallo durante la inferencia: {exc}", color="#cc4444")
            return

        self.inf_table.setRowCount(0)
        for i, pred in enumerate(preds[:200]):
            row = self.inf_table.rowCount()
            self.inf_table.insertRow(row)
            self.inf_table.setItem(row, 0, QTableWidgetItem(str(i + 1)))
            item_pred = QTableWidgetItem(f"{pred:.6f}")
            item_pred.setTextAlignment(Qt.AlignCenter)
            self.inf_table.setItem(row, 1, item_pred)

        self._log(f"[OK] Inferencia completada: {len(preds)} predicciones generadas.", color="#88cc88")
        logging.info(f"Inferencia de Regresion completada: {len(preds)} muestras.")

    # ── Helpers ────────────────────────────────────────────────────────────────

    def _toggle_alpha(self, index: int):
        self.spin_alpha.setEnabled(index > 0)

    def _log(self, msg: str, color: str = "#cccccc"):
        self.output_log.append(f"<span style='color:{color};'>{msg}</span>")

    @staticmethod
    def _group(title: str) -> QGroupBox:
        g = QGroupBox(title)
        g.setStyleSheet("""
            QGroupBox {
                color: #d4d4d4;
                border: 1px solid #333333;
                margin-top: 10px;
                padding-top: 10px;
                font-weight: bold;
                font-size: 13px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 4px;
            }
        """)
        lay = QVBoxLayout(g)
        lay.setSpacing(10)
        lay.setContentsMargins(14, 14, 14, 14)
        return g

    @staticmethod
    def _input_style() -> str:
        return (
            "background-color:#1a1a1a; color:#e0e0e0;"
            "border:1px solid #333333; border-radius:0px; padding:6px;"
        )

    @staticmethod
    def _combo_style() -> str:
        return (
            "background-color:#1a1a1a; color:#e0e0e0;"
            "border:1px solid #333333; border-radius:0px; padding:4px;"
        )

    @staticmethod
    def _btn_style() -> str:
        return (
            "QPushButton { background-color:#333333; color:#e0e0e0;"
            "border-radius:0px; padding:6px 16px; font-size:13px; }"
            "QPushButton:hover { background-color:#444444; }"
            "QPushButton:disabled { color:#666666; }"
        )

    @staticmethod
    def _btn_primary_style() -> str:
        return (
            "QPushButton { background-color:#d4d4d4; color:#0d0d0d; font-weight:bold;"
            "font-size:14px; padding:10px 24px; border-radius:0px; }"
            "QPushButton:hover { background-color:#ffffff; }"
            "QPushButton:disabled { background-color:#555555; color:#888888; }"
        )
