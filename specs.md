Futuro software de creración de modelos de inteligencia artificial

Reglas:

1. Ni se te ocurra usar emojis ni en el código ni en la interfaz
2. No marques las tareas como COMPLETADA, solo el usuario podrá hacerlo
3. Documenta cada funcionalidad en una carpeta de docs, para cada sección de la aplicación con información en lenguaje no técnico y luego en lenguaje técnico, explicando las funcionalidades, como se han implementado y el flujo de ejecución que siguen en el programa.

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

[TAREA] Lee image.png en specs_images, el dataset como iris.csv tiene una variable objetivo de tipo texto, por lo que no lo procesa bien por que espera float, consigue que el sistema sea sólido para cualquier tipo de dato.