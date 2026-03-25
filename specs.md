Futuro software de creración de modelos de inteligencia artificial

Reglas:

1. Ni se te ocurra usar emojis ni en el código ni en la interfaz
2. No marques las tareas como COMPLETADA, solo el usuario podrá hacerlo
3. Documenta cada funcionalidad en una carpeta de docs, para cada sección de la aplicación con información en lenguaje no técnico y luego en lenguaje técnico, explicando las funcionalidades, como se han implementado y el flujo de ejecución que siguen en el programa.
4. Lee la documentación de docs en caso de que necesites más información sobre el proyecto

Primera funcionalidad:

[COMPLETADA] Construir un panel principal con un sidebar para poder navegar entre las diferentes funcionalidades, y un area de trabajo para poder realizar las diferentes funcionalidades, y un area de consola para poder ver los logs de la aplicacion. Utiliza Python y PySide para la interfaz gráfica

[COMPLETADA] La primera funcionalidad será la página Home, con dos botones para poder crear un nuevo modelo de IA o cargar uno existente. Quita los tres primeros logs de la consola, y que por defecto esté oculta y que se pueda desplegar con un menú en la barra de menú de la aplicación

[COMPLETADA] Divide responsabilidades, utiliza un sistema de ficheros para separar las diferentes funcionalidades

[COMPLETADA] La ventana se tiene que desplegar en modo ventana pero ocupando toda la pantalla del pc disponible

[COMPLETADA] En el panel lateral debajo del botón Home estará el panel "modelo" que desplegará el panel del modelo cargado, según dependiendo del tipo de modelo de IA la distribución será de una forma u otra, dependiendo de la arquitectura del modelo. De momento haz posible la creación de 3 tipos de modelos

[COMPLETADA] En el panel de "Modelo" en el mismo panel izquierdo en esa parte "Modelo" tendrá que aparecer un botón para poder crear el modelo, y un botón para poder cargar un modelo, entonces será un subpanel "Modelo" que listará todos los modelos cargados en memoria para poder intercambiar entre ellos.

[COMPLETADA] Primer tipo de modelo: Regresión, este modelo se podrá crear desde el panel de "Modelo" en el subpanel "Modelo" en el botón "Crear modelo", y se podrá cargar desde el botón "Cargar modelo" en el subpanel "Modelo" en el botón "Cargar modelo" con un popup primero que diga, que modelo quieres crear. Y el panel de control de dicho modelo coincidirá con los controles para crear un modelo de regresión, implementa las funcionalidades necesarias.

[COMPLETADA] La pantalla de configuración del modelo no debe tener un selector de tipo de modelo, sino que tiene que tener los controles necesarios para entrenar el modelo con la arquitectura correspondiente

[COMPLETADA] Pestaña Recursos: en el panel lateral izquierdo va a haber una sección que permita gestionar todos los recursos del programa en cuanto a datasets, modelos cargados, sets de imágenes, etc, etc. Se van a poder cargar o eliminar de la memoria

[COMPLETADA] Optimiza el fichero main.py ahí solo tiene que estar la funcionalidad de ejecución principal de la aplicación

[COMPLETADA] La pestaña modelos tiene que ser un desplegable, y dentro de ella estarán los botones de crear y cargar modelo, y debajo la lista de modelos cargados en memoria.

[COMPLETADA] Cambia la interfaz gráfica por una escala de grises, botones y componentes cuadrados sin bordes redondeados, y una paleta de colores definida para todo el programa. Utiliza una fuente moderna y legible, y un espaciado adecuado para que la interfaz sea agradable a la vista.

[COMPLETADA] En la pestaña de recursos, solo hay una lista de recursos que se pueden cargar y eliminar.

[COMPLETADA] Implementa la funcionalidad para importar Recursos, de cualquier tipo, pero se va a poder importar carpetas o archivos, para uno u otro se tendrá un botón de importar.

[COMPLETADA] En la pestaña de recursos, se podrá eliminar los recursos cargados en memoria, y se podrá ver una lista de los recursos cargados en memoria.

[COMPLETADA] Habrá una carpeta en la raíz del proyecto llamado examples, que tendrá datasets famosos típicos para realizar entrenamientos e inferencia con datasets de ejemplo (como Iris por ejemplo)

[COMPLETADA] Colocar en el gitignore todos los ficheros y carpetas que no deban subirse a github, los datasets de ejemplo deben subirse, esos no se ignorarán

[COMPLETADA] Para las ventanas que piden que cargues un archivo de dataset haz que sea funcional, haz que la ventana de regresión sea totalmente funcional y se pueda entrenar exportar y hacer inferencia sobre el modelo de regresión

[COMPLETADA] Lee image.png en specs_images, el dataset como iris.csv tiene una variable objetivo de tipo texto, por lo que no lo procesa bien por que espera float, consigue que el sistema sea sólido para cualquier tipo de dato.

[COMPLETADA] Añade una barra de carga al momento de entrenar un modelo

[COMPLETADA] Permite que se pueda realizar inferencia sobre el modelo de regresión con una entrada manual, y que se muestre el resultado en la consola

[COMPLETADA] Lee image1.png en specs_images y quiero que esa sección de la ventana, de entrenamiento, quiero que sea una sección desplegable mediante una flecha a la izquierda que señale arriba o abajo, y que al pulsarla se pueda desplegar o contraer esa sección

[COMPLETADA] La consola y la inferencia debe también poder desplegarse y contraerse mediante una flecha a la izquierda que señale arriba o abajo, y que al pulsarla se pueda desplegar o contraer esa sección

[COMPLETADA] La inferencia manual debe desplegar un popup con cada columna a probar, y rellenar una tabla con los datos manuales que quiero probar para obtener un output y en la columna de la variable objetivo se va a poner el resultado de la inferencia

[COMPLETADA] Al momento de hacer inferencias (con csv o manualmente) en caso de que la variable objetivo sea texto, la columna de la variable objetivo en la tabla de inferencia debe mostrar el texto de la variable objetivo en vez de un número

[COMPLETADA] La funcionalidad de Cargar modelo debe cargar un modelo (seleccionar una carpeta o un fichero .pkl) y dependiendo del tipo de modelo a cargar se debe mostrar el panel de configuración del modelo correspondiente

[COMPLETADA] Las ventanas de configuración de todos los tipos de modelos deben poder ser scrolleables hacia abajo, la forma en la que está organizada la ventana de configuracion de los modelos es como un pipeline, paso por paso, de hecho organizalo de esta manera de forma numerada 

[COMPLETADA] Añade una subsección encima de Resultados (renombra la sección de Consola (resultados) a simplemente Resultados) esta nueva subsección será la de Exportar (elimina el botón anterior de Exportar) y añade nuevas posibles opciones de Exportación

[COMPLETADA] Al querer crear o cargar un modelo las subsecciones 2, 3, para abajo, deben estar comprimidas por defecto

[COMPLETADA] La pestaña Home los botones de Crear modelo y Cargar no funcionan

[COMPLETADA] Entre las subsecciones de Inferencia y Exportación, añade una subsección que permita ver la tabla con las muestras de datos (Que el número de muestras sea configurable), y con un buscador que permita buscar por columnas

[COMPLETADA] Simplifica la interfaz quitando textos redundantes y textos informativos que son redundantes y pueden sobrecargar la interfaz

[COMPLETADA] Al hacer click sobre algun elemento que sea combobox, campo de texto o botón tiene que aparecer un mensaje de advertencia en caso de que no se haya seleccionado ningún dataset

[COMPLETADA] En el menú de la aplicación quiero un botón Guardar para poder guardar el modelo que se esté editando actualmente, en caso de que no esté en ninguna vista, es decir que no esté editando ningún modelo actualmente, que la ventana de guardado me de a elegir cual de los modelos cargados en memoria quiero guardar, y en caso de que esté en una vista, es decir que esté editando un modelo actualmente, que se guarde el modelo que se esté editando actualmente, el modelo se podrá guardar en cualquier parte en una carpeta con todos los recursos necesarios para continuar con su creación más adelante

[COMPLETADA] La pestaña desplegable de Modelos del panel lateral izquierdo tiene que estar contraida por defecto

[COMPLETADA] Cuando no hay ningún dataset cargado e intento interactuar con algún combobox, botón de entrenamiento, o desplegable, o componente general SOLAMENTE DE LA PESTAÑA DE ENTRENAMIENTO, tiene que aparecerme un mensaje que me advierta de que no hay un dataset cargado

[COMPLETADA] En la parde de "Regularización" añade un botón de información para que el usuario sepa cada método de regularización y en que consiste este término en este contexto

[COMPLETADA] Cada subsección de las vistas de configuración del modelo quiero que estén rodeadas en un cuadro con bordes redondeados más gris que el color de fondo

[COMPLETADA] La pestaña de inferencia debe mostrar también una columna con porcentaje de seguridad de la predicción, y en la inferencia con csv también

[COMPLETADA] Agrega una nueva sección debajo de Muestra de datos que permita visualizar el modelo en gráficos, de momento implementa esto para el modelo de regresión que se permita visualizar el modelo de varias formas gráficas diferentes

[COMPLETADA] Los bordes de los componentes en toda la app deben ser cuadrados en lugar de redondeados

[COMPLETADA] Basándote en el aspecto y estructura de componentes del modelo de Regresión, crea una vista para crear modelos de K-Means, con su propia configuración, entrenamiento, inferencia, exportación y visualización

[TAREA] Separa los estilos en una carpeta nueva llamada styles, y que cada componente tenga su propio estilo en un fichero .qss