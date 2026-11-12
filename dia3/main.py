"""deriva-costes: cuánto gasta cada equipo de Deriva en modelos de lenguaje.

API para registrar llamadas a modelos y consultar el gasto, más funciones que
usa el panel (panel.py). Arrancar con: uvicorn main:app --reload

Tarifas y cálculo del coste: tarifas.py. Tests: pytest.
"""

import calendar
import csv
import os
import sqlite3
import sys
from datetime import date, datetime, timedelta
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from tarifas import TARIFAS, calcular_coste

RUTA_DB = os.environ.get("DERIVA_DB", os.path.join(os.path.dirname(__file__), "datos", "deriva.db"))

# Fecha de referencia. En producción sería date.today(), pero los datos de
# ejemplo llegan hasta noviembre de 2026.
HOY = date.fromisoformat(os.environ.get("DERIVA_HOY", "2026-11-11"))

UMBRAL_AVISO = 0.8  # se avisa al llegar al 80 % del presupuesto

app = FastAPI(title="deriva-costes")


def conectar():
    con = sqlite3.connect(RUTA_DB)
    con.row_factory = sqlite3.Row
    return con


def _fila_a_dict(fila):
    d = dict(fila)
    d["tokens_cache"] = d["tokens_cache"] or 0
    d["lote"] = bool(d["lote"])
    d["coste"] = calcular_coste(d["modelo"], d["tokens_entrada"], d["tokens_salida"], d["tokens_cache"], d["lote"])
    return d


def _limites_mes(mes):
    """'2026-11' -> ('2026-11-01', '2026-12-01')"""
    inicio = datetime.strptime(mes, "%Y-%m")
    if inicio.month == 12:
        fin = inicio.replace(year=inicio.year + 1, month=1)
    else:
        fin = inicio.replace(month=inicio.month + 1)
    return inicio.strftime("%Y-%m-%d"), fin.strftime("%Y-%m-%d")


def mes_actual():
    return HOY.strftime("%Y-%m")


def llamadas_del_mes(mes, equipo=None):
    desde, hasta = _limites_mes(mes)
    con = conectar()
    if equipo:
        filas = con.execute(
            "SELECT * FROM llamadas WHERE fecha >= ? AND fecha < ? AND equipo = ? ORDER BY fecha",
            (desde, hasta, equipo),
        ).fetchall()
    else:
        filas = con.execute(
            "SELECT * FROM llamadas WHERE fecha >= ? AND fecha < ? ORDER BY fecha", (desde, hasta)
        ).fetchall()
    con.close()
    return [_fila_a_dict(f) for f in filas]


def presupuestos():
    con = conectar()
    filas = con.execute("SELECT nombre, presupuesto_mensual_usd FROM equipos").fetchall()
    con.close()
    return {f["nombre"]: f["presupuesto_mensual_usd"] for f in filas}


def gasto_por_equipo(mes):
    llamadas = llamadas_del_mes(mes)
    gasto = {}
    for ll in llamadas:
        gasto[ll["equipo"]] = gasto.get(ll["equipo"], 0) + ll["coste"]
    resultado = []
    for equipo, presupuesto in presupuestos().items():
        g = round(gasto.get(equipo, 0), 2)
        resultado.append({
            "equipo": equipo,
            "gasto": g,
            "presupuesto": presupuesto,
            "porcentaje": round(g / presupuesto * 100, 1) if presupuesto else None,
        })
    resultado.sort(key=lambda r: r["gasto"], reverse=True)
    return resultado


def gasto_por_proyecto(equipo, mes):
    llamadas = llamadas_del_mes(mes, equipo)
    por_proyecto = {}
    for ll in llamadas:
        p = por_proyecto.setdefault(ll["proyecto"], {"proyecto": ll["proyecto"], "gasto": 0, "llamadas": 0})
        p["gasto"] += ll["coste"]
        p["llamadas"] += 1
    resultado = list(por_proyecto.values())
    for r in resultado:
        r["gasto"] = round(r["gasto"], 2)
    resultado.sort(key=lambda r: r["gasto"], reverse=True)
    return resultado


def _gasto_entre(desde, hasta):
    """USD por equipo de las llamadas con fecha en [desde, hasta)."""
    con = conectar()
    filas = con.execute(
        "SELECT * FROM llamadas WHERE fecha >= ? AND fecha < ?", (desde.isoformat(), hasta.isoformat())
    ).fetchall()
    con.close()
    gasto = {}
    for ll in map(_fila_a_dict, filas):
        gasto[ll["equipo"]] = gasto.get(ll["equipo"], 0) + ll["coste"]
    return gasto


def prevision_fin_de_mes(gasto_mes: float, dias_transcurridos: int, dias_del_mes: int) -> float:
    """Gasto previsto a fin de mes si se mantiene el ritmo diario actual."""
    if dias_transcurridos <= 0:
        return 0.0
    return gasto_mes / dias_transcurridos * dias_del_mes


def informe_semanal(fecha=None):
    """Gasto de la semana y del mes por equipo, con previsión a fin de mes.

    Ver specs/informe-semanal.md.
    """
    fecha = fecha or HOY
    manana = fecha + timedelta(days=1)
    inicio_mes = fecha.replace(day=1)
    dias_del_mes = calendar.monthrange(fecha.year, fecha.month)[1]

    gasto_semana = _gasto_entre(fecha - timedelta(days=6), manana)
    gasto_mes = _gasto_entre(inicio_mes, manana)

    informe = []
    for equipo, presupuesto in presupuestos().items():
        mes = gasto_mes.get(equipo, 0)
        prevision = prevision_fin_de_mes(mes, fecha.day, dias_del_mes)
        if mes >= presupuesto:
            estado = "superado"
        elif prevision > presupuesto:
            estado = "en riesgo"
        else:
            estado = "ok"
        informe.append({
            "equipo": equipo,
            "gasto_semana": round(gasto_semana.get(equipo, 0), 2),
            "gasto_mes": round(mes, 2),
            "presupuesto": presupuesto,
            "restante": round(presupuesto - mes, 2),
            "prevision_mes": round(prevision, 2),
            "estado": estado,
        })
    informe.sort(key=lambda r: r["prevision_mes"], reverse=True)
    return informe


def comprobar_presupuestos(mes):
    """Equipos que han pasado del UMBRAL_AVISO de su presupuesto."""
    alertas = []
    for g in gasto_por_equipo(mes):
        if g["gasto"] >= g["presupuesto"] * UMBRAL_AVISO:
            alertas.append({
                "equipo": g["equipo"],
                "gasto": g["gasto"],
                "presupuesto": g["presupuesto"],
                "nivel": "superado" if g["gasto"] >= g["presupuesto"] else "aviso",
            })
    return alertas


def llamadas_mas_caras(mes, n=10):
    llamadas = llamadas_del_mes(mes)
    llamadas.sort(key=lambda ll: ll["coste"], reverse=True)
    return llamadas[:n]


def resumen_semanal(equipo, fin=None):
    """Gasto por proyecto y modelo de los últimos 7 días frente a los 7 anteriores."""
    fin = fin or HOY + timedelta(days=1)
    con = conectar()
    filas = con.execute(
        "SELECT * FROM llamadas WHERE equipo = ? AND fecha >= ? AND fecha < ?",
        (equipo, (fin - timedelta(days=14)).isoformat(), fin.isoformat()),
    ).fetchall()
    con.close()
    corte = (fin - timedelta(days=7)).isoformat()
    semanas = {"anterior": {}, "actual": {}}
    for f in map(_fila_a_dict, filas):
        semana = "actual" if f["fecha"] >= corte else "anterior"
        clave = f"{f['proyecto']} ({f['modelo']})"
        semanas[semana][clave] = semanas[semana].get(clave, 0) + f["coste"]
    return semanas


def explicar_subida(equipo):
    """Explica en lenguaje natural por qué ha cambiado el gasto de un equipo.

    Usa la API de OpenAI. Necesita OPENAI_API_KEY y el paquete openai.
    Sin OPENAI_API_KEY, o con DERIVA_SIN_MODELO=1, devuelve los datos sin
    llamar al modelo.
    """
    semanas = resumen_semanal(equipo)
    lineas = []
    for clave in sorted(set(semanas["anterior"]) | set(semanas["actual"])):
        a = semanas["anterior"].get(clave, 0)
        b = semanas["actual"].get(clave, 0)
        lineas.append(f"- {clave}: semana anterior {a:.2f} USD, esta semana {b:.2f} USD")
    datos = "\n".join(lineas)

    if os.environ.get("DERIVA_SIN_MODELO") == "1" or not os.environ.get("OPENAI_API_KEY"):
        return f"[Modo sin modelo] Gasto de {equipo} por proyecto:\n{datos}"

    import openai

    openai.api_key = os.environ["OPENAI_API_KEY"]
    prompt = (
        f"Eres analista de costes. El equipo {equipo} gasta en modelos de lenguaje así:\n{datos}\n"
        "Explica en tres frases, para el responsable del equipo, qué ha cambiado y por qué puede ser."
    )
    respuesta = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
    )
    return respuesta["choices"][0]["message"]["content"]


def importar_csv(ruta):
    """Carga el export manual de uso de Abisal (CSV)."""
    con = conectar()
    n = 0
    with open(ruta, encoding="utf-8") as f:
        for fila in csv.DictReader(f):
            con.execute(
                "INSERT INTO llamadas (id_externo, fecha, equipo, proyecto, modelo, tokens_entrada, tokens_salida, tokens_cache, lote)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    fila["id_peticion"],
                    fila["fecha"],
                    fila["equipo"],
                    fila["proyecto"],
                    fila["modelo"],
                    int(fila["tokens_entrada"]),
                    int(fila["tokens_salida"]),
                    int(fila["tokens_cache"]),
                    1 if fila["lote"] == "si" else 0,
                ),
            )
            n += 1
    con.commit()
    con.close()
    return n


# ---------------------------------------------------------------- API


class Llamada(BaseModel):
    id_externo: Optional[str] = None
    fecha: Optional[str] = None
    equipo: str
    proyecto: str
    modelo: str
    tokens_entrada: int
    tokens_salida: int
    tokens_cache: Optional[int] = None
    lote: bool = False


@app.post("/llamadas")
def registrar_llamada(ll: Llamada):
    if ll.modelo not in TARIFAS:
        raise HTTPException(400, f"Modelo desconocido: {ll.modelo}")
    fecha = ll.fecha or datetime.now().isoformat(timespec="seconds")
    tokens_cache = ll.tokens_cache or 0  # algunos proveedores mandan null cuando no hay caché
    con = conectar()
    cur = con.execute(
        "INSERT INTO llamadas (id_externo, fecha, equipo, proyecto, modelo, tokens_entrada, tokens_salida, tokens_cache, lote)"
        " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (ll.id_externo, fecha, ll.equipo, ll.proyecto, ll.modelo, ll.tokens_entrada, ll.tokens_salida,
         tokens_cache, int(ll.lote)),
    )
    con.commit()
    id_nuevo = cur.lastrowid
    con.close()
    coste = calcular_coste(ll.modelo, ll.tokens_entrada, ll.tokens_salida, tokens_cache, ll.lote)
    return {"id": id_nuevo, "coste": coste}


@app.get("/gasto")
def api_gasto(mes: Optional[str] = None):
    return gasto_por_equipo(mes or mes_actual())


@app.get("/gasto/{equipo}")
def api_gasto_equipo(equipo: str, mes: Optional[str] = None):
    if equipo not in presupuestos():
        raise HTTPException(404, "Equipo no encontrado")
    return gasto_por_proyecto(equipo, mes or mes_actual())


@app.get("/informe-semanal")
def api_informe_semanal(fecha: Optional[str] = None):
    if fecha is None:
        return informe_semanal()
    try:
        dia = date.fromisoformat(fecha)
    except ValueError:
        raise HTTPException(400, "La fecha tiene que tener formato AAAA-MM-DD") from None
    return informe_semanal(dia)


@app.get("/alertas")
def api_alertas(mes: Optional[str] = None):
    return comprobar_presupuestos(mes or mes_actual())


@app.get("/llamadas/caras")
def api_caras(mes: Optional[str] = None, n: int = 10) -> List[dict]:
    return llamadas_mas_caras(mes or mes_actual(), n)


@app.get("/explicacion/{equipo}")
def api_explicacion(equipo: str):
    return {"equipo": equipo, "explicacion": explicar_subida(equipo)}


if __name__ == "__main__":
    # python main.py importar datos/uso_abisal_2026-11-10.csv
    if len(sys.argv) == 3 and sys.argv[1] == "importar":
        print(f"Importadas {importar_csv(sys.argv[2])} llamadas.")
    else:
        print("Uso: python main.py importar <fichero.csv>")
