# Vista de Regresión — Entrenamiento e Inferencia

## Explicación no técnica

La sección de **Regresión** permite al usuario entrenar modelos de Inteligencia Artificial que predicen valores numéricos continuos a partir de un conjunto de datos (dataset). 

El usuario selecciona un archivo CSV que contiene sus datos y especifica cuál de las columnas es la "variable objetivo" (lo que la IA debe aprender a predecir). Posteriormente, puede ajustar ciertos parámetros avanzados (hiperparámetros) como el tipo de regularización y el tamaño del conjunto de validación, y hacer clic en "Entrenar Modelo".

El sistema está diseñado de forma robusta para ser capaz de manejar datos que contengan texto en lugar de números. Si el archivo CSV, como por ejemplo `iris.csv`, tiene etiquetas de texto (como "setosa" o "versicolor"), el sistema se encargará automáticamente de convertirlas en valores numéricos interpretables por el modelo. Además, el sistema manejará valores incompletos.

Una vez finalizado el entrenamiento, el usuario puede observar métricas de error y precisión del modelo. A partir de ahí, se habilita la opción de "Exportar Modelo" para guardarlo, y "Inferir" para cargar un nuevo archivo con datos no vistos por el modelo y predecir los resultados.

Si todavía no se ha cargado un dataset y el usuario intenta tocar los controles de la zona de entrenamiento, la aplicación muestra un aviso inmediato indicando que primero debe seleccionar un CSV. De esta forma se evita avanzar en un flujo de entrenamiento sin datos de entrada.

En la fila de hiperparámetros hay botones de información junto a **Regularización**, **Alpha** y **% Test**. Cada uno explica el concepto correspondiente dentro de esta pantalla para que el usuario pueda ajustar el entrenamiento con contexto suficiente sin salir de la aplicación.

La tabla de inferencia ahora muestra también un **porcentaje de seguridad** por predicción, tanto cuando se hace una prueba manual como cuando se carga un CSV. Ese porcentaje ofrece una referencia rápida sobre la confianza relativa de cada resultado dentro del contexto del modelo entrenado.

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

### Seguridad de la prediccion

- Cada fila de inferencia incorpora una columna adicional `% Seguridad`.
- En inferencia manual y en inferencia por CSV se calcula la seguridad con el mismo criterio para que la tabla sea consistente.
- El porcentaje no representa una probabilidad estadistica exacta; es una estimacion heuristica basada en dos factores: la calidad general del modelo tras el entrenamiento y la cercania de la muestra inferida al patron de datos visto durante entrenamiento.
- Para modelos antiguos cargados desde archivo que no traigan estos metadatos, la vista usa valores de respaldo para seguir mostrando la columna sin romper la compatibilidad.

### Avisos por falta de dataset en Entrenamiento

- La vista instala un `eventFilter` sobre los controles interactivos de la subsección de entrenamiento (`CollapsibleBox`, regularización y parámetros numéricos) mientras `self._df` sea `None`.
- Cuando el usuario intenta abrir un desplegable, girar la rueda o pulsar esos controles sin haber cargado antes un CSV, `RegressionView` invoca `_show_missing_dataset_warning()`.
- El botón `Entrenar` reutiliza esa misma validación al entrar en `_on_train`, por lo que el aviso es consistente tanto en la interacción previa como en el intento explícito de lanzar el entrenamiento.

### Ayuda contextual de Hiperparámetros

- La fila de hiperparámetros añade botones `i` junto a `Regularizacion`, `Alpha` y `% Test`.
- Cada botón abre un `QMessageBox.information(...)` con una explicación breve del parámetro dentro del flujo de entrenamiento.
- La ayuda de regularización describe `Ninguna (OLS)`, `Ridge (L2)`, `Lasso (L1)` y `ElasticNet`; la ayuda de `Alpha` aclara que controla la intensidad de la penalización; y la ayuda de `% Test` explica cómo se reparte el dataset entre entrenamiento y evaluación.

---

## Visualización del Modelo

### Explicación no técnica

Una vez que el modelo ha sido entrenado, la sección **Visualización del Modelo** permite al usuario explorar gráficamente cómo se está comportando el modelo. En lugar de interpretar solo números y métricas, el usuario puede ver de forma visual si las predicciones del modelo se acercan a los valores reales, si los errores están bien distribuidos, qué variables tienen más peso en la predicción y cómo están distribuidos los fallos del modelo.

Hay cuatro tipos de gráfico disponibles:

- **Predicciones vs Valores Reales**: muestra un punto por cada muestra del dataset. Cuanto más cerca estén los puntos de la línea diagonal punteada, mejor está prediciendo el modelo.
- **Residuos**: representa la diferencia entre lo que predijo el modelo y el valor real. Un modelo bien ajustado debería tener los puntos dispersos de forma aleatoria alrededor del cero, sin patrones claros.
- **Importancia de Variables**: muestra qué columnas del dataset tienen más influencia sobre las predicciones, ordenadas de mayor a menor. Útil para entender qué factores son más determinantes.
- **Distribución de Errores**: un histograma que muestra la frecuencia de cada tamaño de error. Un buen modelo debería tener la mayoría de los errores concentrados cerca del cero.

El usuario puede cambiar el tipo de gráfico en cualquier momento con el selector desplegable, y actualizar manualmente el gráfico con el botón "Actualizar". Los gráficos se generan automáticamente tras cada entrenamiento.

### Explicación técnica

#### Integración de matplotlib en Qt

La visualización se basa en `matplotlib` con el backend `Agg` (no interactivo), renderizado dentro de la interfaz Qt mediante `FigureCanvasQTAgg` del módulo `matplotlib.backends.backend_qtagg`. El canvas se incrusta directamente en el layout de la `CollapsibleBox` de visualización.

Se usa `matplotlib.use("Agg")` en el nivel de módulo para evitar conflictos con el bucle de eventos de Qt. El canvas se crea una única vez en `_build_visualization_section()` y se reutiliza en cada actualización limpiando el eje (`self._ax.clear()`) y llamando a `self._canvas.draw()`.

#### Flujo de ejecución

1. Al finalizar el entrenamiento (`_on_training_done`), se activa el botón "Actualizar" y se llama automáticamente a `_refresh_charts()`.
2. `_refresh_charts()` verifica que existan `self._bundle` y `self._df`.
3. Recupera el target actual desde `combo_target`, reaplica los mismos `LabelEncoder` usados en entrenamiento (de `self._bundle["label_encoders"]`) y el `StandardScaler` almacenado en `self._bundle["scaler"]`.
4. Genera predicciones sobre el dataset completo para calcular `y_pred`, `y_true` y `residuals`.
5. Según la selección del `combo_chart`, renderiza uno de los cuatro tipos de gráfico:
   - `scatter` para Predicciones vs Reales con línea ideal `y=x`.
   - `scatter` de residuos contra predicciones con línea horizontal en cero.
   - `barh` horizontal de `|coef_|` para importancia, filtrando el top-15 si hay muchas variables.
   - `hist` de residuos con líneas verticales en cero y la media.
6. Todos los ejes se estilizan con la paleta oscura del proyecto (fondo `#1a1a1a`, texto `#cccccc`, rejilla `#2a2a2a`).
7. `tight_layout` y `canvas.draw()` finalizan el renderizado.
8. Un `QLabel` de estado bajo el canvas informa del gráfico activo o del error ocurrido.

#### Reset y carga de modelos

Al reiniciar la vista (`reset_view`) o cargar un modelo desde archivo (`load_bundle`), el botón "Actualizar" se desactiva, el eje se limpia y el label de estado vuelve al mensaje inicial. Esto garantiza que nunca se muestre un gráfico desactualizado de un modelo anterior.
