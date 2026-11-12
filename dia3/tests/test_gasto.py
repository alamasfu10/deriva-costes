"""Caracterización sobre el histórico: el gasto de cada equipo por mes.

Valores de la versión heredada con datos/deriva.db tal como se entrega.
"""

import pytest

import main

GASTO_OCTUBRE = {"producto": 121.77, "datos": 62.70, "plataforma": 23.63, "marketing": 11.45}
GASTO_NOVIEMBRE = {"datos": 128.35, "producto": 31.08, "plataforma": 6.17, "marketing": 3.42}


@pytest.mark.parametrize("mes, esperado", [("2026-10", GASTO_OCTUBRE), ("2026-11", GASTO_NOVIEMBRE)])
def test_gasto_por_equipo_del_historico(db, mes, esperado):
    gasto = {g["equipo"]: g["gasto"] for g in main.gasto_por_equipo(mes)}
    assert gasto == pytest.approx(esperado, abs=0.01)


def test_aviso_de_datos_en_noviembre(db):
    """El fallo del aviso: Datos va al 107 % y antes no salía ningún aviso."""
    alertas = {a["equipo"]: a for a in main.comprobar_presupuestos("2026-11")}
    assert alertas["datos"]["nivel"] == "superado"
    assert alertas["datos"]["gasto"] == pytest.approx(128.35, abs=0.01)


def test_sin_avisos_en_octubre(db):
    assert main.comprobar_presupuestos("2026-10") == []


def test_el_aviso_cuadra_con_el_gasto(db):
    """Aviso y gasto salen del mismo cálculo: no pueden contar cosas distintas."""
    gasto = {g["equipo"]: g["gasto"] for g in main.gasto_por_equipo("2026-11")}
    for alerta in main.comprobar_presupuestos("2026-11"):
        assert alerta["gasto"] == gasto[alerta["equipo"]]
