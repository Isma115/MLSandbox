# Vista de Redes Neuronales Densas (MLP)

## Explicacion no tecnica

La nueva vista de **Redes Neuronales** permite crear un modelo MLP dentro del mismo flujo que ya usan Regresion y K-Means.

El usuario puede:

- Cargar un dataset CSV.
- Elegir la columna objetivo.
- Decidir si quiere que la tarea se interprete automaticamente, como clasificacion o como regresion.
- Configurar la red con capas ocultas, funcion de activacion, regularizacion, learning rate y numero maximo de epocas.
- Entrenar el modelo sin bloquear la interfaz.
- Probar el modelo con un CSV o con una inferencia manual.
- Exportarlo en `pkl`, `joblib` o JSON con pesos y metadatos.
- Revisar graficos para entender como ha entrenado la red.

La tabla de inferencia muestra tanto la prediccion como un porcentaje de seguridad. Cuando la tarea es de clasificacion, la salida final se presenta usando el texto original de la clase. Cuando es de regresion, la salida se muestra como valor numerico.

La seccion de visualizacion ofrece varias formas de inspeccionar el modelo: curva de perdida, comparacion entre predicciones y referencia, distribucion de seguridad y mapa de pesos de la primera capa.

---

## Explicacion tecnica

### Archivo principal

La implementacion vive en `views/mlp_view.py`.

### Entrenamiento

El entrenamiento se ejecuta en `MLPTrainingWorker`, un `QThread` para evitar bloquear la UI.

El flujo interno es:

1. Parsear la configuracion de capas ocultas desde el campo de texto.
2. Separar `X` e `y` a partir de la columna objetivo.
3. Codificar columnas categoricas de entrada con `LabelEncoder`.
4. Inferir el tipo de tarea cuando el usuario deja el modo en `Auto`.
5. Codificar la variable objetivo si la tarea es de clasificacion.
6. Escalar features con `StandardScaler`.
7. Entrenar `MLPClassifier` o `MLPRegressor` de `scikit-learn`.
8. Calcular metricas y metadatos de confianza para inferencia posterior.

El `bundle` resultante incluye:

- `sandbox_model_type = "mlp"`
- `model`
- `scaler`
- `features`
- `label_encoders`
- `task_type`
- `target_column`
- `training_config`
- `confidence_stats`

### Inferencia

La inferencia reutiliza exactamente el pipeline almacenado en el bundle:

- Validacion de columnas esperadas.
- Reaplicacion de los `LabelEncoder` de entrada.
- Escalado con el `StandardScaler` entrenado.
- Prediccion con el modelo MLP cargado.

Para clasificacion:

- Se usa `predict` para obtener la clase.
- Si existe encoder de la variable objetivo, se revierte a la etiqueta original.
- La confianza se estima combinando la probabilidad maxima (`predict_proba`) y la calidad global del modelo.

Para regresion:

- Se usa `predict` para obtener el valor.
- La confianza se estima con una heuristica basada en la distancia de la muestra al patron de entrenamiento y la calidad global (`R2`) del modelo.

### Visualizacion

La seccion de graficos esta embebida con `matplotlib` y `FigureCanvasQTAgg`.

Graficos implementados:

1. **Curva de perdida**: usa `loss_curve_` del modelo.
2. **Predicciones vs Referencia**:
   - Clasificacion: matriz de confusion.
   - Regresion: dispersión valor real frente a prediccion.
3. **Distribucion de seguridad**: histograma del porcentaje de seguridad por muestra.
4. **Pesos de la primera capa**: mapa de calor con `coefs_[0]`.

### Integracion con la aplicacion

La nueva vista queda integrada en:

- `views/model_page.py`: registro de `MLPView` en el `QStackedWidget`.
- `views/main_window.py`: deteccion de bundles MLP al cargar desde disco.
- `views/main_window.py`: persistencia del bundle en la lista lateral para poder volver a cada modelo MLP en memoria.
