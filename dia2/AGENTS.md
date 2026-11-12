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
| `main.py` | API FastAPI y toda la lógica: tarifas, coste, gasto, avisos, importación |
| `panel.py` | Panel Streamlit. Solo pinta: llama a funciones de `main.py` |
| `datos/deriva.db` | SQLite con las tablas `equipos` y `llamadas` |
| `proveedor_simulado/` | Copia de la API de uso de Abisal para desarrollo. No se modifica |

## Convenciones que no se negocian

1. Base de datos con `sqlite3` de la biblioteca estándar y SQL escrito a mano.
   Nada de SQLAlchemy ni de otro ORM.
2. Nada de pandas en `main.py`. Las funciones devuelven listas de
   diccionarios; `panel.py` puede pintarlas como quiera.
3. Todo coste sale de `calcular_coste()`. No se repite la fórmula en otro
   sitio.
4. `tokens_cache` puede llegar a `None` desde la base de datos: léelo siempre
   a través de `_fila_a_dict()`, que lo deja en 0.
5. La fecha de hoy es `HOY`, no `date.today()`. Los datos de ejemplo terminan
   en noviembre de 2026.
6. Funciones, variables y textos en español. Los nombres que vienen de
   librerías o de APIs externas se dejan como están.
7. Sin dependencias nuevas sin preguntar. Si hace falta una, dilo y explica
   por qué antes de añadirla a `requirements.txt`.
8. No modifiques `datos/deriva.db` para probar. Usa una copia.

## Cómo se prueba

```bash
uvicorn main:app --reload      # API en http://localhost:8000/docs
streamlit run panel.py         # panel en http://localhost:8501
```

## Cómo trabajar

- Antes de cambiar más de un fichero, propón un plan y espera a que lo apruebe.
- Cambios pequeños, uno por petición.
- Si una especificación no aclara algo, pregunta en vez de suponer.
