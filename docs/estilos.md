# Sistema de Estilos

## Explicación no técnica

La aplicación ahora guarda sus estilos visuales en una carpeta específica llamada `styles/`.

Esto significa que los colores, bordes, tamaños de texto y apariencia general ya no están mezclados dentro del código Python de cada pantalla. En su lugar, cada parte importante de la interfaz tiene su propio fichero `.qss`, que actúa como una hoja de estilos de Qt.

¿Qué ventaja tiene esto?

- Cambiar la apariencia de una vista concreta es más rápido.
- Es más fácil mantener una imagen visual consistente en toda la aplicación.
- El código Python queda más limpio y se centra en la lógica y el comportamiento.

Ejemplos de esta organización:

- `styles/app.qss`: estilos base compartidos por toda la aplicación.
- `styles/main_window.qss`: estilos del contenedor principal y el panel lateral.
- `styles/regression_view.qss`: ajustes visuales propios de la vista de regresión.
- `styles/kmeans_view.qss`: ajustes visuales propios de la vista de K-Means.
- `styles/dialogs.qss`: aspecto de los cuadros de diálogo.

## Explicación técnica

### Estructura

Se ha sustituido el bloque de estilos en Python por una carga de hojas QSS externas desde `core/styles.py`.

Funciones principales:

- `load_stylesheet(*filenames)`: lee uno o varios archivos `.qss` desde la carpeta `styles/` y devuelve el contenido combinado.
- `apply_stylesheet(widget, *filenames)`: aplica al widget el QSS cargado.
- `set_dynamic_property(widget, name, value)`: actualiza propiedades dinámicas Qt y repinta el widget para que los selectores QSS basados en propiedades entren en efecto.

### Flujo de ejecución

1. `views/main_window.py` carga `styles/app.qss` y `styles/main_window.qss`.
2. Cada vista o componente relevante carga además su propio fichero `.qss`.
3. Los widgets que necesitan variantes visuales concretas usan `objectName` o propiedades dinámicas:
   - `variant="primary"` para acciones principales.
   - `variant="danger"` para acciones destructivas o cancelación.
   - `variant="info"` para botones de ayuda contextual.
   - `tone="status-muted|status-success|status-error"` para estados visuales como el de los gráficos.
4. Cuando una propiedad dinámica cambia en tiempo de ejecución, `set_dynamic_property(...)` fuerza el repintado para que Qt reaplique el selector correspondiente.

### Componentes cubiertos

- Ventana principal y sidebar.
- `CollapsibleBox`.
- Diálogos reutilizables.
- Home.
- Recursos.
- Configuración del modelo.
- Ajustes.
- Regresión.
- K-Means.
- Vistas placeholder de MLP, CNN y Transformer.

### Criterio de diseño aplicado

- Estilos comunes centralizados en `styles/app.qss`.
- Estilos específicos aislados por componente para evitar acoplamiento visual entre vistas.
- Eliminación de `setStyleSheet(...)` inline en el código de interfaz para que la fuente de verdad del estilo quede en QSS.
