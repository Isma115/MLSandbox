# Vista de Regresión — Entrenamiento e Inferencia

## Explicación no técnica

La sección de **Regresión** permite al usuario entrenar modelos de Inteligencia Artificial que predicen valores numéricos continuos a partir de un conjunto de datos (dataset). 

El usuario selecciona un archivo CSV que contiene sus datos y especifica cuál de las columnas es la "variable objetivo" (lo que la IA debe aprender a predecir). Posteriormente, puede ajustar ciertos parámetros avanzados (hiperparámetros) como el tipo de regularización y el tamaño del conjunto de validación, y hacer clic en "Entrenar Modelo".

El sistema está diseñado de forma robusta para ser capaz de manejar datos que contengan texto en lugar de números. Si el archivo CSV, como por ejemplo `iris.csv`, tiene etiquetas de texto (como "setosa" o "versicolor"), el sistema se encargará automáticamente de convertirlas en valores numéricos interpretables por el modelo. Además, el sistema manejará valores incompletos.

Una vez finalizado el entrenamiento, el usuario puede observar métricas de error y precisión del modelo. A partir de ahí, se habilita la opción de "Exportar Modelo" para guardarlo, y "Inferir" para cargar un nuevo archivo con datos no vistos por el modelo y predecir los resultados.

---

## Explicación técnica

### Arquitectura de `RegressionView`

Definida en `views/regression_view.py`, la interfaz actúa como ventana principal para la configuración, entrenamiento e inferencia de modelos de regresión `scikit-learn`.

### Manejo Robusto de Datos (Object / String)

Se ha implementado un sistema robusto que analiza el tipo de dato de las variables elegidas en `TrainingWorker`.
- Para las **variables predictoras (X)** y la **variable objetivo (y)**, si pandas detecta que son de tipo `object`, `category` o `string`, el hilo de entrenamiento inicializa un `LabelEncoder` de `sklearn.preprocessing`.
- Se aplica `fit_transform` para convertir todas las clases (texto) numéricamente.
- Todos los valores numéricos se parsean de forma segura y los nulos (`NaN`) se rellenan explícitamente (`fillna(0)`).
- Los encoders utilizados se almacenan en un diccionario `label_encoders` que se comparte e integra en el `bundle` de modelo exportado para que en la inferencia el sistema pueda decodificar / transformar categorías nuevas o existentes de forma idéntica.

### Worker de Entrenamiento: `TrainingWorker` (QThread)

Para no bloquear la interfaz principal (UI), el modelo se entrena en un hilo secundario:
1. Extrae los hiperparámetros de la UI.
2. Separa el set objetivo del set predictor.
3. Efectua la transformación de los datos categóricos usando `LabelEncoder`.
4. Divide los datos en Train y Test usando `train_test_split`.
5. Escala los valores usando `StandardScaler()`.
6. Entrena el modelo seleccionado (`LinearRegression`, `Ridge`, `Lasso`, `ElasticNet`).
7. Retorna el modelo entrenado, escalador, encoders y métricas a la interfaz de usuario.

### Inferencia

- **Inferencia**: Carga un nuevo CSV, valida compatibilidad entre columnas, aplica los mismos transformadores (`LabelEncoder` guardado) resolviendo clases desconocidas a la base para no romper la ejecución, escala mediante `StandardScaler` y genera predicciones iterando las muestras en un `QTableWidget` mediante predicciones de un solo pase.
