# AGENTS.md · deriva-costes

Instrucciones para el asistente de código. Léelas antes de proponer cambios.

## Qué es

Herramienta interna de Deriva que calcula cuánto gasta cada equipo en modelos
de lenguaje y avisa antes de que se pase de su presupuesto. La usan los
responsables de equipo y el CTO. Es código en uso: un cambio en el cálculo del
coste cambia lo que se le dice a un equipo sobre su dinero.

## Piezas

| Fichero | Qué hace |
|---|---|
| `main.py` | API FastAPI y lógica de gasto, avisos, informe e importación |
| `tarifas.py` | Tarifas de los modelos y `calcular_coste()`. Único sitio donde se calcula un coste |
| `tests/` | pytest. `conftest.py` da una copia de la base de datos con el fixture `db` |
| `panel.py` | Panel Streamlit. Solo pinta: llama a funciones de `main.py` |
| `datos/deriva.db` | SQLite con las tablas `equipos` y `llamadas` |
| `proveedor_simulado/` | Copia de la API de uso de Abisal para desarrollo. No se modifica |

## Convenciones que no se negocian

1. Base de datos con `sqlite3` de la biblioteca estándar y SQL escrito a mano.
   Nada de SQLAlchemy ni de otro ORM.
2. Nada de pandas en `main.py`. Las funciones devuelven listas de
   diccionarios; `panel.py` puede pintarlas como quiera.
3. Todo coste sale de `tarifas.calcular_coste()`. No se repite la fórmula en
   otro sitio.
4. `tokens_cache` puede llegar a `None` desde la base de datos: léelo siempre
   a través de `_fila_a_dict()`, que lo deja en 0.
5. La fecha de hoy es `HOY`, no `date.today()`. Los datos de ejemplo terminan
   en noviembre de 2026.
6. Funciones, variables y textos en español. Los nombres que vienen de
   librerías o de APIs externas se dejan como están.
7. Sin dependencias nuevas sin preguntar. Si hace falta una, dilo y explica
   por qué antes de añadirla a `requirements.txt`, con la versión fija. Las
   dependencias se instalan con `pip install -r requirements.txt`, nunca con un
   `pip install` suelto.
8. No modifiques `datos/deriva.db` para probar. Usa una copia.

## Avisos del editor

Ruff y Pylance marcan problemas en el editor, en la vista Problemas. Tratarlos es
parte de cada tarea:

- Al terminar de editar, consulta los problemas del editor de los ficheros que has
  tocado y ejecuta `ruff check .`. No des la tarea por terminada con avisos nuevos.
- Los avisos de Ruff se corrigen en el código. Los arreglos automáticos seguros
  (`ruff check --fix`) se pueden aplicar. Los no seguros (`--unsafe-fixes`) no:
  propón el cambio y espera.
- No silencies un aviso con `# noqa` ni lo quites de `pyproject.toml`. Si crees que
  un aviso no procede, explica por qué y deja la decisión a quien revisa.
- Si corregir un aviso cambia el comportamiento, por ejemplo una excepción que se
  tragaba un error, explica el cambio antes de hacerlo.
- Si Pylance dice que no resuelve un import de una librería externa, no cambies el
  código ni instales nada: avísame. Suele faltar la dependencia, o VS Code no está usando el entorno virtual.
- Corrige solo los avisos de los ficheros que la tarea toca, salvo que se te pida
  cerrar todos los avisos.

## Cómo se prueba

```bash
pytest                         # tiene que terminar en verde antes de dar algo por hecho
ruff check .                   # sin avisos
uvicorn main:app --reload      # API en http://localhost:8000/docs
streamlit run panel.py         # panel en http://localhost:8501
```

`tests/test_tarifas.py` y `tests/test_gasto.py` son tests de caracterización:
fijan lo que hacía el código heredado. Si un cambio los rompe, para y
explícalo; no cambies el valor esperado para que pase.

## Cómo trabajar

- Antes de cambiar más de un fichero, propón un plan y espera a que lo apruebe.
- Cambios pequeños, uno por petición.
- Antes de un refactor, comprueba que hay tests que cubren lo que vas a tocar.
  Si no los hay, escríbelos primero contra el código actual.
- Un test nuevo tiene que fallar si quitas el código que prueba. Si pasa
  igual, no prueba nada.
- Si una especificación no aclara algo, pregunta en vez de suponer.
