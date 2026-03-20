# Recursos — Gestión de Recursos del Programa

## Explicación no técnica

La sección **Recursos** permite al usuario cargar en la aplicación cualquier tipo de archivo o carpeta
que quiera utilizar durante sus experimentos de Machine Learning.

Se pueden cargar dos tipos de elementos:

- **Archivos**: datasets en CSV, imágenes, modelos previamente entrenados, ficheros de texto, etc.
- **Carpetas**: directorios completos con conjuntos de datos o sets de imágenes.

Una vez importado un recurso, aparece en la lista de "Recursos cargados en memoria" con su nombre
y la ruta completa desde la que fue importado. El usuario puede eliminar cualquier recurso de
la lista cuando ya no lo necesite.

Los recursos se gestionan en memoria durante la sesión; al cerrar la aplicación no se persisten.

---

## Explicación técnica

### Clase `Resource` (dataclass)

Definida en `views/resources_view.py`, almacena los metadatos de cada recurso en memoria:

```python
@dataclass
class Resource:
    nombre: str
    tipo: str        # "archivo" o "carpeta"
    ruta: str
    extension: str   # Extension del fichero (ej: ".csv")
```

### Estado en memoria

La vista mantiene una lista `self.resources: list[Resource]` que actúa como fuente de verdad.
Cada vez que se añade o elimina un recurso se actualiza tanto esta lista como el `QListWidget` visual.

### Botón "Importar Archivo"

Llama a `QFileDialog.getOpenFileName()` con filtros predefinidos (CSV, imagenes, modelos, texto).
Al confirmar, se crea un `Resource` de tipo `"archivo"` y se llama a `_añadir_recurso()`.

### Botón "Importar Carpeta"

Llama a `QFileDialog.getExistingDirectory()`. Al confirmar, se crea un `Resource` de tipo `"carpeta"`.

### Método `_añadir_recurso(recurso: Resource)`

1. Comprueba si ya existe un recurso con la misma ruta (evita duplicados).
2. Appends al estado `self.resources`.
3. Crea un `QListWidgetItem` con etiqueta de tipo y ruta abreviada.
4. Lo registra en el `QListWidget` y emite un log con `logging.info`.

### Botón "Eliminar seleccionado"

Itera sobre `self.lista_recursos.selectedItems()`, filtra `self.resources` excluyendo la ruta del
item seleccionado, y llama a `takeItem()` para retirar el elemento del widget visual.

### Flujo de ejecución

```
Usuario hace clic "Importar Archivo"
    -> QFileDialog.getOpenFileName() abre diálogo nativo del SO
    -> Usuario selecciona fichero y confirma
    -> Se crea Resource(nombre, tipo="archivo", ruta, extension)
    -> _añadir_recurso() verifica duplicados
    -> Resource se añade a self.resources
    -> QListWidgetItem creado y añadido a self.lista_recursos
    -> logging.info() registra el evento en la consola

Usuario selecciona item de la lista y hace clic "Eliminar seleccionado"
    -> Se obtienen selectedItems() del QListWidget
    -> Para cada item: se extrae ruta via item.data(Qt.UserRole)
    -> self.resources se filtra eliminando el recurso con esa ruta
    -> takeItem() retira el elemento del QListWidget
    -> logging.info() registra la eliminación
```
