"""Genera los datos sintéticos de deriva-costes.

Crea tres cosas a partir de la misma semilla, para que todo cuadre:

- datos/deriva.db: equipos y llamadas registradas hasta el 09/11/2026.
- datos/uso_abisal_2026-11-10.csv: el export manual de Abisal del 10/11.
- proveedor_simulado/uso_abisal.json: todo el histórico de Abisal, que sirve
  la API simulada.

Uso: python datos/generar_datos.py
"""

import csv
import json
import random
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SEMILLA = 1212
INICIO = datetime(2026, 10, 1)
FIN = datetime(2026, 11, 11, 23, 59)
CORTE_DB = datetime(2026, 11, 10)  # lo anterior ya está en la base de datos
DIA_CSV = datetime(2026, 11, 10)

EQUIPOS = {
    "producto": 300.0,
    "datos": 120.0,
    "plataforma": 60.0,
    "marketing": 25.0,
}

# (equipo, proyecto, modelo, llamadas por día laborable, entrada, salida, fracción en caché, lote)
PROYECTOS = [
    ("producto", "buscador", "nautilus-flash", 60, (3_000, 9_000), (200, 600), 0.0, False),
    ("producto", "resumen-documentos", "orca-large", 25, (15_000, 40_000), (500, 1_500), 0.6, False),
    ("producto", "redaccion-asistida", "orca-mini", 40, (1_000, 4_000), (300, 900), 0.0, False),
    ("datos", "clasificador-facturas", "orca-mini", 30, (2_000, 6_000), (50, 150), 0.0, True),
    ("datos", "analisis-contratos", "orca-large", 6, (20_000, 60_000), (800, 2_000), 0.3, False),
    ("datos", "extraccion-tablas", "nautilus-pro", 8, (5_000, 20_000), (500, 2_000), 0.0, False),
    ("plataforma", "revision-codigo", "nautilus-pro", 12, (8_000, 30_000), (400, 1_500), 0.5, False),
    ("plataforma", "triaje-alertas", "nautilus-flash", 30, (1_000, 3_000), (100, 300), 0.0, False),
    ("marketing", "textos-campanas", "orca-mini", 15, (800, 2_500), (400, 1_200), 0.0, False),
    ("marketing", "traduccion", "nautilus-flash", 20, (2_000, 8_000), (2_000, 8_000), 0.0, True),
]

PROVEEDOR = {"orca-large": "abisal", "orca-mini": "abisal", "nautilus-flash": "coral", "nautilus-pro": "coral"}


def _llamadas_del_dia(rnd, dia):
    """Devuelve las llamadas de un día, ordenadas por hora."""
    laborable = dia.weekday() < 5
    filas = []
    for equipo, proyecto, modelo, por_dia, entrada, salida, cache, lote in PROYECTOS:
        n = por_dia * 3 if laborable else por_dia * 3 // 5
        n = max(0, int(rnd.gauss(n, n * 0.15)))
        for _ in range(n):
            tokens_entrada = rnd.randint(*entrada)
            # Desde el 02/11, el equipo de Datos mete contratos enteros: contexto largo.
            if proyecto == "analisis-contratos" and dia >= datetime(2026, 11, 2):
                tokens_entrada = rnd.randint(210_000, 320_000)
            tokens_cache = int(tokens_entrada * cache * rnd.uniform(0.7, 1.0)) if cache else 0
            hora = dia + timedelta(seconds=rnd.randint(8 * 3600, 20 * 3600))
            filas.append({
                "fecha": hora,
                "equipo": equipo,
                "proyecto": proyecto,
                "modelo": modelo,
                "tokens_entrada": tokens_entrada,
                "tokens_salida": rnd.randint(*salida),
                "tokens_cache": tokens_cache,
                "lote": lote,
            })
    filas.sort(key=lambda f: f["fecha"])
    return filas


def generar():
    rnd = random.Random(SEMILLA)
    todas = []
    dia = INICIO
    while dia <= FIN:
        todas.extend(_llamadas_del_dia(rnd, dia))
        dia += timedelta(days=1)
    for i, fila in enumerate(todas, start=1):
        prefijo = "abs" if PROVEEDOR[fila["modelo"]] == "abisal" else "crl"
        fila["id_externo"] = f"{prefijo}_{i:06d}"

    # Una llamada que llegó de Coral con cached_tokens a null. Es la que rompe el aviso.
    nula = next(f for f in todas if f["proyecto"] == "extraccion-tablas" and f["fecha"] >= datetime(2026, 11, 5))
    nula["tokens_cache"] = None

    _escribir_db(f for f in todas if f["fecha"] < CORTE_DB)
    _escribir_csv(f for f in todas if f["fecha"].date() == DIA_CSV.date() and PROVEEDOR[f["modelo"]] == "abisal")
    _escribir_json(f for f in todas if PROVEEDOR[f["modelo"]] == "abisal")
    print(f"{len(todas)} llamadas generadas.")


def _escribir_db(filas):
    ruta = RAIZ / "datos" / "deriva.db"
    ruta.unlink(missing_ok=True)
    con = sqlite3.connect(ruta)
    con.executescript(
        """
        CREATE TABLE equipos (nombre TEXT PRIMARY KEY, presupuesto_mensual_usd REAL NOT NULL);
        CREATE TABLE llamadas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_externo TEXT,
            fecha TEXT NOT NULL,
            equipo TEXT NOT NULL,
            proyecto TEXT NOT NULL,
            modelo TEXT NOT NULL,
            tokens_entrada INTEGER NOT NULL,
            tokens_salida INTEGER NOT NULL,
            tokens_cache INTEGER,
            lote INTEGER NOT NULL DEFAULT 0
        );
        """
    )
    con.executemany("INSERT INTO equipos VALUES (?, ?)", EQUIPOS.items())
    con.executemany(
        "INSERT INTO llamadas (id_externo, fecha, equipo, proyecto, modelo, tokens_entrada, tokens_salida, tokens_cache, lote)"
        " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [
            (f["id_externo"], f["fecha"].isoformat(timespec="seconds"), f["equipo"], f["proyecto"], f["modelo"],
             f["tokens_entrada"], f["tokens_salida"], f["tokens_cache"], int(f["lote"]))
            for f in filas
        ],
    )
    con.commit()
    con.close()


def _escribir_csv(filas):
    ruta = RAIZ / "datos" / f"uso_abisal_{DIA_CSV:%Y-%m-%d}.csv"
    with open(ruta, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id_peticion", "fecha", "equipo", "proyecto", "modelo", "tokens_entrada", "tokens_salida", "tokens_cache", "lote"])
        for fila in filas:
            w.writerow([fila["id_externo"], fila["fecha"].isoformat(timespec="seconds"), fila["equipo"], fila["proyecto"],
                        fila["modelo"], fila["tokens_entrada"], fila["tokens_salida"], fila["tokens_cache"],
                        "si" if fila["lote"] else "no"])


def _escribir_json(filas):
    # La API de Abisal habla en inglés y con sus propios nombres de campo.
    ruta = RAIZ / "proveedor_simulado" / "uso_abisal.json"
    datos = [
        {
            "request_id": f["id_externo"],
            "created_at": f["fecha"].isoformat(timespec="seconds") + "Z",
            "metadata": {"team": f["equipo"], "project": f["proyecto"]},
            "model": f["modelo"],
            "usage": {
                "input_tokens": f["tokens_entrada"],
                "output_tokens": f["tokens_salida"],
                "cached_input_tokens": f["tokens_cache"],
            },
            "batch": f["lote"],
        }
        for f in filas
    ]
    ruta.write_text(json.dumps(datos, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    generar()
