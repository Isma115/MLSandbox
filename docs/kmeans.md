# Vista de K-Means - Entrenamiento, Inferencia y Visualizacion

## Explicacion no tecnica

La seccion de **K-Means** permite agrupar automaticamente las muestras de un dataset en varios conjuntos parecidos entre si, sin necesitar una columna objetivo. En lugar de predecir un valor exacto como hace Regresion, aqui el sistema busca patrones y separa los datos en clusters.

El flujo para el usuario sigue la misma estructura visual que la vista de Regresion:

- Carga un archivo CSV.
- Decide si quiere ignorar una columna concreta antes de entrenar.
- Configura el numero de clusters y los parametros principales del algoritmo.
- Entrena el modelo.
- Usa inferencia por CSV o manual para saber a que cluster pertenece una muestra nueva.
- Exporta el modelo o revisa sus graficos.

La interfaz mantiene las mismas subsecciones desplegables: entrenamiento, inferencia, muestra de datos, visualizacion, exportacion y resultados. Esto hace que el cambio de una arquitectura a otra sea directo y consistente dentro de la aplicacion.

La inferencia muestra tanto el **cluster asignado** como un **porcentaje de seguridad**. Ese porcentaje no debe interpretarse como una probabilidad matematica exacta; es una referencia practica basada en lo cerca que queda cada muestra del centro de su cluster y en la calidad general del agrupamiento conseguido durante el entrenamiento.

La seccion de visualizacion ayuda a entender el modelo con graficos: una proyeccion 2D de los clusters, el tamano de cada grupo, la distancia de las muestras a su centroide y una vista de los centroides normalizados.

---

## Explicacion tecnica

### Archivo principal

La implementacion vive en `views/kmeans_view.py`.

### Worker de entrenamiento

El entrenamiento se ejecuta en `KMeansTrainingWorker`, un `QThread` separado para no bloquear la interfaz:

1. Duplica el `DataFrame` cargado.
2. Elimina la columna marcada como ignorada, si existe.
3. Codifica automaticamente columnas categoricas con `LabelEncoder`.
4. Convierte el resto de columnas a numerico y rellena nulos con `0`.
5. Escala los datos con `StandardScaler`.
6. Entrena `sklearn.cluster.KMeans`.
7. Calcula metadatos utiles para inferencia y visualizacion:
   - `inertia_`
   - `silhouette_score` cuando es posible
   - tamano de cada cluster
   - una referencia de distancia por cluster para estimar seguridad

El resultado se empaqueta en un `bundle` compatible con el flujo general del proyecto:

- `sandbox_model_type`
- `model`
- `scaler`
- `features`
- `label_encoders`
- `ignored_column`
- `confidence_stats`

### Inferencia

La vista reutiliza el mismo pipeline de transformacion del entrenamiento:

- Valida que el CSV de entrada contenga todas las columnas esperadas.
- Reaplica los `LabelEncoder` guardados en el bundle.
- Escala las muestras con el `StandardScaler` almacenado.
- Obtiene el cluster asignado con `model.predict(...)`.
- Calcula una confianza heuristica usando la distancia al centroide asignado frente a una referencia interna del cluster.

La inferencia manual usa el mismo mecanismo, pero construyendo un `DataFrame` de una sola fila a partir del popup `ManualInferenceDialog`.

### Visualizacion

La seccion de graficos usa `matplotlib` embebido en Qt mediante `FigureCanvasQTAgg`.

Se implementan cuatro vistas:

1. **Proyeccion PCA de Clusters**: reduce los datos escalados a 2 dimensiones con `PCA` para representar visualmente las agrupaciones y sus centroides.
2. **Tamano por Cluster**: muestra cuantas muestras cayeron en cada grupo.
3. **Distancia al Centroide**: usa un `boxplot` por cluster para ver dispersion y compactacion.
4. **Centroides Normalizados**: renderiza una matriz de calor con `cluster_centers_`.

### Integracion con la aplicacion

Para exponer la nueva arquitectura se han actualizado estos puntos:

- `core/dialogs.py`: anade K-Means al selector de creacion de modelo.
- `views/model_page.py`: registra `KMeansView` como nueva pagina del `QStackedWidget`.
- `views/main_window.py`: detecta bundles de `KMeans` al cargar modelos `.pkl` o `.joblib` y guarda metadatos especificos del clustering.

Con esto, K-Means queda integrado en el mismo flujo de memoria, seleccion lateral, guardado y carga que el resto de arquitecturas.
