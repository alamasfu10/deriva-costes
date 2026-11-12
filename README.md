# deriva-costes

Código de práctica del **Tema 12, Vibe coding e integración de IA en el IDE**, del Máster en Ingeniería y Desarrollo de Soluciones de IA Generativa (MID) de EBIS Business Techschool. Docente: Álvaro Lamas.

`deriva-costes` es la herramienta interna de una empresa ficticia, Deriva, que calcula cuánto gasta cada equipo en modelos de lenguaje y avisa antes de que se pase de su presupuesto. Los datos son sintéticos y los modelos y precios son inventados. Durante las tres sesiones se amplía con la ayuda de un asistente de IA dentro de VS Code.

## Qué hay en cada carpeta

Cada carpeta es el estado con el que se empieza un día. Todas son proyectos completos e independientes: no hay nada compartido entre ellas.

| Carpeta | Estado con el que empieza | Lo que se hace ese día |
|---|---|---|
| `dia1` | El repositorio heredado: todo en `main.py`, sin tests y con fallos sembrados | Entender el código, escribir `AGENTS.md` y una especificación, y construir el informe semanal |
| `dia2` | El que deja el Día 1: con `AGENTS.md`, la especificación y el informe semanal | Corregir el aviso de presupuesto y el error 500, dejar Ruff sin avisos y mover las tarifas a su módulo con tests |
| `dia3` | El que deja el Día 2: con `tarifas.py`, tests y Ruff limpio | Leer el uso del proveedor de su API, construir un servidor MCP propio y escribir las reglas del equipo |

Si terminas un día, tu proyecto será parecido al estado inicial del día siguiente. Si no lo terminas, o quieres comprobar tu solución, empieza el siguiente desde su carpeta.

## Cómo empezar con un clon

Alternativa al zip del campus, que sigue disponible con el mismo contenido.

1. Clona el repositorio:

```bash
git clone https://github.com/alamasfu10/deriva-costes.git
```

2. Abre en VS Code la carpeta del día que quieras, no el clon entero. Para el Día 1 es `deriva-costes/dia1`. Para otro día, `dia2` o `dia3`.

3. Sigue la guía del ejercicio. El clon ya es un repositorio de Git, así que no hace falta `git init`: el estado de partida es el primer commit del historial y los commits que hagas se quedan en tu ordenador. No tienes permiso de escritura en este repositorio, así que un `git push` desde tu copia fallaría.

Cada carpeta tiene su propio `README.md` con las instrucciones de instalación y arranque del proyecto: entorno virtual, `pip install -r requirements.txt`, API y panel.

## Qué no incluye

Las guías y las diapositivas de cada sesión están en el campus de EBIS. En este repositorio solo está el código de partida.
