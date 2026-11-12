# deriva-costes

> **Tema 12 del MID de EBIS, Día 2.** Esta carpeta contiene el estado con el que empieza el Día 2, que es el que deja el Día 1: con `AGENTS.md`, la especificación del informe semanal y el informe construido. Equivale al zip `deriva-costes-dia-1.zip` del campus. Más información en el [README del repositorio](../README.md).

Herramienta interna de Deriva para saber cuánto gasta cada equipo en modelos de
lenguaje y avisar antes de que se pase de su presupuesto.

Los servicios de Deriva registran cada llamada a un modelo en la API
(`POST /llamadas`). El uso de Abisal llega aparte, en un CSV que se descarga a
mano de su consola cada día y se importa con `main.py importar`.

## Arrancar

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

uvicorn main:app --reload        # API en http://localhost:8000/docs
streamlit run panel.py           # panel en http://localhost:8501
```

La base de datos de ejemplo ya está en `datos/deriva.db`. Para volver a crearla
desde cero: `python datos/generar_datos.py`.

## Informe semanal

`GET /informe-semanal` y la primera sección del panel. Especificación en
`specs/informe-semanal.md`.

## Importar el uso de Abisal

```bash
python main.py importar datos/uso_abisal_2026-11-10.csv
```

## Explicación del gasto con OpenAI

El botón «Explicar el gasto» del panel usa la API de OpenAI. Hace falta
`pip install openai` y la variable `OPENAI_API_KEY` con tu clave. Sin ella,
el panel enseña los datos sin llamar al modelo.

## API de Abisal (simulada)

En `proveedor_simulado/` hay una copia de la API de uso de Abisal para
desarrollo, con su contrato en `openapi.json`:

```bash
uvicorn proveedor_simulado.app:app --port 8100
```

Clave de prueba: `abisal-clave-de-prueba`, en la cabecera `X-Abisal-Key`.

## Pendiente

- Tests.
- Sacar las tarifas a un fichero aparte.
- Leer el uso de Abisal de su API en vez del CSV.
