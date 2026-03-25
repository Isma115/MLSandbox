# Navegacion del Panel de Modelos

## Explicacion no tecnica

La seccion **Modelos** del panel lateral izquierdo aparece contraida al abrir la aplicacion. Esto deja la navegacion inicial mas limpia y evita ocupar espacio vertical si todavia no se va a crear o cargar un modelo.

Cuando el usuario necesita trabajar con modelos, solo tiene que pulsar el encabezado **Modelos** para desplegar las acciones de crear, cargar y revisar los modelos que ya estan en memoria.

## Explicacion tecnica

La logica vive en `views/main_window.py`.

- Se ha centralizado el estado visual del desplegable en el metodo `_set_modelos_expanded(expanded: bool)`.
- Durante la construccion de `MainWindow`, el contenedor `self.modelos_container` se inicializa mediante `_set_modelos_expanded(False)`, garantizando que el panel arranque contraido por defecto.
- El metodo `toggle_modelos()` ya no manipula el texto y la visibilidad por separado; ahora delega en `_set_modelos_expanded(...)` para mantener sincronizados el icono del boton (`►` o `▼`) y la visibilidad del contenedor interno.
- Cuando el usuario selecciona un modelo nuevo en memoria, `MainWindow` indica a `ModelView` que actualice el encabezado a `Crear modelo (tipo)`. Si el elemento seleccionado corresponde a un modelo cargado desde archivo, la vista mantiene el titulo general de configuracion.
