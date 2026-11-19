# Lenguaje de Programación Costeñol & Costeñol IDE

**Costeñol** es un lenguaje de programación imperativo, tipado estáticamente y de propósito educativo diseñado con sintaxis en español y diagnósticos de compilación y ejecución inspirados en la jerga del Caribe colombiano. El proyecto incluye su propio Entorno de Desarrollo Integrado (**Costeñol IDE**) construido de forma nativa en Python.

---

## Tabla de Contenidos

1. [Características Principales](#-características-principales)
2. [Arquitectura del Proyecto](#-arquitectura-del-proyecto)
3. [Requisitos e Instalación](#-requisitos-e-instalación)
4. [Guía de Sintaxis del Lenguaje](#-guía-de-sintaxis-del-lenguaje)
5. [Uso del IDE y Atajos de Teclado](#-uso-del-ide-y-atajos-de-teclado)
6. [Ejemplo Completo en Costeñol](#-ejemplo-completo-en-costeñol)

---

## Características Principales

* **Pipeline de Compilación Real:** Implementa separación estricta entre análisis léxico (tokenización mediante expresiones regulares), análisis sintáctico/semántico (construcción de AST y validación de tipos) e interpretación en tiempo de ejecución.
* **Cero Dependencias Externas:** Desarrollado íntegramente con la biblioteca estándar de Python (`tkinter`, `re`, `threading`, `os`, `sys`), sin necesidad de instalar paquetes mediante `pip`.
* **Validación Semántica Estática:** Detecta variables no declaradas, redeclaraciones duplicadas e incompatibilidades de tipos antes de ejecutar el código.
* **Protecciones en Tiempo de Ejecución:** Controla divisiones por cero, limita bucles infinitos a un máximo de `10,000` iteraciones y otorga hasta `3` intentos al capturar datos inválidos por teclado.
* **IDE Gráfico Completo:** Incluye tema oscuro (*Dark Mode*), numeración de líneas dinámica, autocierre de paréntesis y comillas, resaltado de sintaxis en tiempo real, visor de tokens para depuración y navegación interactiva al hacer clic sobre cualquier error.

---

## 🏗️ Arquitectura del Proyecto

El sistema está dividido en **4 módulos desacoplados**:

```text
costenol/
├── main.py              # Interfaz gráfica (Costeñol IDE) y coordinación multihilo
├── lexer.py             # Analizador léxico (Scanner basado en expresiones regulares)
├── parser_costenol.py   # Analizador sintáctico (Recursive Descent), Tabla de Símbolos y AST
├── interpreter.py       # Intérprete (Tree-Walk) y manejo de errores en tiempo de ejecución
└── README.md            # Documentación oficial del proyecto
```

### Descripción de Módulos

| Archivo | Rol en el Compilador / Sistema |
| :--- | :--- |
| **`lexer.py`** | Escanea el código fuente en una pasada lineal de complejidad $O(n)$ utilizando una expresión regular maestra de 24 reglas (`TOKEN_SPEC`). Genera objetos `Token` con tipo, valor, línea y columna, y exige mayúscula inicial en palabras reservadas y tipos. |
| **`parser_costenol.py`** | Construye el **Árbol de Sintaxis Abstracta (AST)** mediante descenso recursivo respetando la precedencia matemática de operadores. Mantiene la `symbol_table` e infiere tipos de expresiones para garantizar compatibilidad antes de ejecutar. |
| **`interpreter.py`** | Recorre y evalúa recursivamente los nodos del AST (`CostenolInterpreter`). Administra la memoria de variables, realiza coerción de tipos, ejecuta ciclos y condicionales, y captura excepciones mediante `CostenolError`. |
| **`main.py`** | Implementa la ventana principal (`CostenolIDE`), el editor (`CodeEditor`), el panel inferior de pestañas (`OutputPanel`: *Consola*, *Errores*, *Tokens*, *Depuración*) y sincroniza el hilo de ejecución con la interfaz mediante `threading.Event`. |

---

## Requisitos e Instalación

* **Python:** Versión `3.8` o superior.
* **Tkinter:** Incluido por defecto en las instalaciones estándar de Python en Windows y macOS. *(En distribuciones Linux basadas en Debian/Ubuntu, asegúrate de tener instalado `sudo apt install python3-tk`)*.

### Ejecución

1. Clona o descarga los archivos del proyecto en una misma carpeta.
2. Abre una terminal en el directorio del proyecto y ejecuta:

```bash
python main.py
```

---

## Guía de Sintaxis del Lenguaje

### 1. Comentarios
Los comentarios se abren y se cierran con doble barra (`//`). Soportan una o varias líneas:
```text
// Esto es un comentario de una línea //

// Esto es un comentario
   de múltiples líneas //
```

### 2. Tipos de Datos y Declaración
Toda variable debe declararse antes de usarse indicando su nombre seguido del tipo de dato y punto y coma (`;`). Las palabras reservadas y los tipos **deben respetar su mayúscula inicial**:

| Tipo | Descripción | Valores válidos / Ejemplo |
| :--- | :--- | :--- |
| **`Entero`** | Números enteros sin decimales | `edad Entero; edad = 25;` |
| **`Real`** | Números decimales (usan **coma** `,`) | `promedio Real; promedio = 4,5;` |
| **`Logico`** | Valores booleanos | `aprobado Logico; aprobado = Verdadero;` (`Verdadero` / `Falso`) |
| **`Texto`** | Cadenas de caracteres entre comillas dobles | `saludo Texto; saludo = "Habla llave";` |

> **Nota sobre variables:** Los nombres de variables pueden iniciar con letra mayúscula, minúscula o guion bajo (`nombre`, `Nombre`, `_total`). Opcionalmente, dentro de expresiones pueden referenciarse anteponiendo `$` (ej. `$nombre`).

### 3. Entrada y Salida de Datos
* **Imprimir en consola:** `Mensaje.Texto(expresion);` (el operador `+` concatena automáticamente si alguno de los operandos es `Texto`).
* **Capturar datos del usuario:** Despliega un cuadro de diálogo con validación estricta de tipo y hasta 3 intentos:
  * `variable = Captura.Entero();`
  * `variable = Captura.Real();`
  * `variable = Captura.Logico();`
  * `variable = Captura.Texto();`

### 4. Operadores
* **Aritméticos (orden de precedencia):** Negación unaria (`-`), multiplicación y división (`*`, `/`), suma y resta (`+`, `-`).
* **Relacionales:** Igualdad (`==`), desigualdad (`!=`), menor que (`<`), mayor que (`>`), menor o igual (`<=`), mayor o igual (`>=`).

### 5. Estructuras de Control

**Condicional (`Si` / `Sino` / `FinSi`):**
```text
Si (promedio >= 3,0)
    Mensaje.Texto("¡Coronaste la materia, el propio!");
Sino
    Mensaje.Texto("¡Paila socio, te descachaste!");
FinSi
```

**Ciclo Mientras (`Mientras` / `FinMientras`):**
```text
contador Entero;
contador = 1;

Mientras (contador <= 3)
    Mensaje.Texto("Vuelta número: " + contador);
    contador = contador + 1;
FinMientras
```

---

## 🖥️ Uso del IDE y Atajos de Teclado

El entorno gráfico ofrece cuatro pestañas de diagnóstico en el panel inferior:
1. **Consola:** Muestra la salida estándar del programa y mensajes de estado de ejecución.
2. **Errores:** Lista todos los errores léxicos o sintácticos con su línea y columna. **Al hacer clic sobre un error, el editor salta automáticamente a esa línea.**
3. **Tokens:** Al ejecutar en modo depuración, despliega la tabla completa de tokens reconocidos por el `Lexer`.
4. **Depuración:** Espacio reservado para trazas internas.

### Atajos Rápidos
* **`F5`**: Compilar y ejecutar el código actual.
* **`F6`**: Compilar y ejecutar en modo **Depuración** (llena la pestaña *Tokens*).
* **`Esc`**: Detener inmediatamente la ejecución en curso.
* **`Tab`**: Inserta una indentación de 4 espacios.

---

## Ejemplo Completo en Costeñol

Copia y pega el siguiente programa en **Costeñol IDE** y presiona `F5` para probar entrada de datos, condicionales y ciclos:

```text
// Programa de cálculo de notas en Costeñol //

estudiante Texto;
nota1 Real;
nota2 Real;
definitiva Real;
intento Entero;

Mensaje.Texto("=== SISTEMA ACADÉMICO COSTEÑOL ===");
estudiante = Captura.Texto();
nota1 = Captura.Real();
nota2 = Captura.Real();

definitiva = (nota1 + nota2) / 2;
Mensaje.Texto("Estudiante: " + estudiante + " | Definitiva: " + definitiva);

Si (definitiva >= 3,0)
    Mensaje.Texto("¡Coronaste el semestre, firme!");
Sino
    Mensaje.Texto("Toca meterle moral el próximo corte.");
FinSi

intento = 1;
Mientras (intento <= 2)
    Mensaje.Texto("Verificación de registro #" + intento);
    intento = intento + 1;
FinMientras
```