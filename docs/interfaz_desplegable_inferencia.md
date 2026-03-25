# Componentes Desplegables e Inferencia Manual

## Documentación No Técnica (Para el Usuario)
Hemos implementado una mejora visual y funcional en la interfaz de la aplicación:
1. **Consola y Sección de Inferencia Plegables**: Ahora, tanto el área de la consola (donde se muestran los mensajes del sistema) como la sección de "Inferencia" (donde pruebas el modelo entrenado), se pueden ocultar o mostrar haciendo clic en una pequeña flecha apuntando hacia abajo o hacia la derecha. Esto te permite tener una pantalla más limpia y centrarte solo en los controles que necesitas en cada momento.
2. **Inferencia Manual Mejorada (Popup)**: Antes, para probar el modelo manualmente, tenías que introducir todos los valores separados por comas en una caja de texto. Ahora, al hacer clic en "Nueva Inferencia Manual", se abrirá una ventana emergente (Popup) con cajas separadas para cada dato que el modelo necesita, con sus nombres correspondientes.
3. **Tabla de Resultados Detallada**: Los resultados de la prueba manual y la prueba con archivo no solo te muestran el número de fila y la predicción, sino que la tabla se adapta de forma inteligente para mostrar también los valores introducidos. Así puedes comparar fácilmente los datos analizados frente al resultado de la predicción en una sola vista estructurada.
4. **Subsecciones enmarcadas**: Cada subsección del flujo de configuración del modelo queda dentro de un cuadro gris con esquinas redondeadas. Esto ayuda a separar visualmente cada paso del pipeline sin cambiar la estructura de trabajo.

## Documentación Técnica (Para el Desarrollador)
### Funcionalidades Implementadas
Se ha integrado el uso de la clase `CollapsibleBox` para reducir el ruido visual en la ventana principal e implementado la entrada dinámica para inferencia.

### Detalles de Implementación
1. **Consola Desplegable (`views/main_window.py`)**: 
   - El widget principal de salida de texto (`self.console`, de tipo `QTextEdit`) se ha anidado dentro de una instancia de `CollapsibleBox` titulada "Consola".
   - Esto afecta al `right_splitter`, en el cual ahora se inserta el `CollapsibleBox` en lugar del campo de texto plano.
   - El método `toggle_console` ha sido actualizado para conmutar la visibilidad de toda la caja envolvente.

2. **Inferencia Desplegable (`views/regression_view.py`)**:
   - De forma análoga a la sección de entrenamiento, el grupo de interfaz de "Inferencia" se ha movido dentro de `self.inf_box` (instancia de `CollapsibleBox`).

3. **Inferencia Manual Dinámica (`core/dialogs.py` y `views/regression_view.py`)**:
   - Se introdujo `ManualInferenceDialog` en `core/dialogs.py`, un `QDialog` que itera sobre la lista de *features* del modelo para generar dinámicamente un `QLineEdit` para cada una (acomodados en un `QFormLayout` con su `QScrollArea`).
   - El método `_on_infer_manual` invoca este diálogo y recupera los valores introducidos en forma de diccionario.
   - La tabla `self.inf_table` (tipo `QTableWidget`) reajusta sus columnas mediante `setColumnCount` y `setHorizontalHeaderLabels` cada vez que el entrenamiento finaliza, adoptando dinámicamente el formato `[*features, "Predicción"]`. Posteriormente, las filas rellenadas incorporan tanto la característica introducida como la inferencia extraída.

4. **Marco visual reutilizable (`core/components.py`)**:
   - `CollapsibleBox` ahora encapsula su cabecera y contenido dentro de un `QFrame` contenedor con fondo gris, borde ligeramente mas claro y `border-radius`.
   - Como las subsecciones de configuracion reutilizan este componente, el cambio visual se propaga de forma global sin duplicar estilos en cada vista.

### Flujo de Ejecución
1. El usuario completa el entrenamiento.
2. `_on_training_done` recibe las `features` dentro de `bundle`. Inmediatamente redefine las columnas de la tabla de inferencia.
3. El usuario presiona "Nueva Inferencia Manual".
4. `_on_infer_manual` evalúa `features`, la instancia de `ManualInferenceDialog` se abre y renderiza un campo de formulario por feature esperado.
5. El usuario envía los datos; éstos se recuperan mediante `dialog.get_values()`.
6. En `regression_view.py`, se parsea el diccionario, se preprocesa usando los mismos escaladores e imputadores que componen el `bundle`, y se calcula la predicción.
7. Almacena todos los valores individuales junto a la predicción en una nueva fila insertada en `inf_table`.
8. Cada subsección se renderiza dentro del nuevo contenedor visual de `CollapsibleBox`, manteniendo la misma lógica de expandir y contraer pero con un marco persistente alrededor del bloque completo.
