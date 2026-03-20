# Datasets de Ejemplo — MLSandbox

Esta carpeta contiene datasets clásicos de Machine Learning listos para usar con la aplicación.

| Archivo | Descripcion | Filas | Columnas | Tipo de problema |
|---|---|---|---|---|
| `iris.csv` | Clasificacion de flores Iris | 150 | 5 | Clasificacion (3 clases) |
| `wine.csv` | Clasificacion de vinos por quimica | 178 | 14 | Clasificacion (3 clases) |
| `diabetes.csv` | Prediccion de progresion de diabetes | 442 | 11 | Regresion |

---

## iris.csv

Dataset de clasificacion de tres especies de flores (Setosa, Versicolor, Virginica)
basado en medidas de sus petalos y sepalos.

**Columnas**: `sepal length (cm)`, `sepal width (cm)`, `petal length (cm)`, `petal width (cm)`, `species`

Uso recomendado: modelo de **Clasificacion** o **Red Neuronal Densa (MLP)**.

---

## wine.csv

Dataset de clasificacion de vinos italianos de tres cultivares distintos.
Contiene 13 parametros quimicos como alcohol, acido malico, intensidad de color, etc.

**Columnas**: 13 propiedades quimicas + `class` (0, 1 o 2)

Uso recomendado: modelo de **Clasificacion** o **Red Neuronal Densa (MLP)**.

---

## diabetes.csv

Dataset de regresion para predecir la progresion de la enfermedad un año despues
del diagnostico, a partir de 10 variables fisiologicas.

**Columnas**: `age`, `sex`, `bmi`, `bp`, `s1`-`s6`, `target`

Uso recomendado: modelo de **Regresion**.
