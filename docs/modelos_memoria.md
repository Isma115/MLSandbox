# Gestion de Modelos en Memoria

## Explicacion no tecnica

La lista lateral de modelos ahora permite no solo crear, cargar e intercambiar modelos, sino tambien eliminarlos.

Cuando el usuario pulsa **Eliminar modelo**, aparece un popup con dos opciones:

- **Solo memoria**: quita el modelo de la sesion actual sin tocar archivos del disco.
- **Borrar completo**: elimina el modelo de la lista y tambien borra su ruta guardada, ya sea un fichero cargado directamente o la carpeta exportada desde la aplicacion.

Si el modelo no tiene una ruta persistida, la opcion de borrado completo aparece desactivada para evitar que el usuario piense que se va a borrar algo que realmente no existe en disco.

Ademas, cuando un modelo nuevo se entrena, deja de ser solo un placeholder y su estado queda asociado a la entrada de la lista lateral para que el guardado, la recarga y la eliminacion trabajen siempre sobre el bundle correcto.

---

## Explicacion tecnica

### Archivo principal

La logica se implementa en `views/main_window.py` y el popup en `core/dialogs.py`.

### Roles asociados a cada elemento de la lista

Cada `QListWidgetItem` de `self.lista_modelos` guarda ahora varios datos:

- Arquitectura (`ROLE_ARCH`)
- Bundle entrenado o cargado (`ROLE_BUNDLE`)
- Ruta persistida (`ROLE_STORAGE`)
- Ruta real a borrar (`ROLE_DELETE_TARGET`)

Esto permite separar el estado visual del elemento del estado funcional necesario para guardar, cargar o eliminar.

### Sincronizacion del bundle con la lista lateral

Las vistas que ya entrenan modelos (`RegressionView`, `KMeansView` y la nueva `MLPView`) emiten la señal `bundle_changed`.

`MainWindow` escucha esa señal y:

1. Guarda el bundle entrenado en el elemento actualmente seleccionado.
2. Mantiene la ruta persistida si el modelo ya venia de disco.
3. Cambia el sufijo `(Nuevo)` a `(Memoria)` una vez el modelo ya tiene estado entrenado utilizable.

### Popup de eliminacion

`DeleteModelDialog` recibe:

- Nombre del modelo.
- Ruta asociada si existe.

Si hay ruta, habilita la opcion de borrado completo. Si no la hay, solo permite retirarlo de memoria.

### Borrado fisico

Para eliminar en disco se usa `_delete_model_storage(...)`:

- Si la ruta apunta a una carpeta, se borra con `shutil.rmtree`.
- Si apunta a un fichero, se elimina con `os.remove`.

`_resolve_delete_target(...)` detecta el caso especial de modelos guardados por la propia aplicacion (`model.pkl` dentro de una carpeta con `metadata.json`) y en ese escenario marca la carpeta completa como objetivo de borrado, no solo el fichero del modelo.

### Guardado y persistencia

Al guardar un modelo desde el menu:

- Se actualiza el bundle del item correspondiente.
- Se registra la carpeta de destino como ruta persistida.
- Queda habilitado el borrado completo posterior sobre esa carpeta exportada.
