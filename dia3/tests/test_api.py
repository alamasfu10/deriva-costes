from fastapi.testclient import TestClient

import main

cliente = TestClient(main.app)

LLAMADA = {"equipo": "datos", "proyecto": "extraccion-tablas", "modelo": "nautilus-pro",
           "tokens_entrada": 1_000, "tokens_salida": 100}


def test_registrar_con_cache_nula(db):
    """El 500 del día 2: Coral manda cached_tokens a null."""
    r = cliente.post("/llamadas", json={**LLAMADA, "tokens_cache": None})
    assert r.status_code == 200
    assert r.json()["coste"] == 0.00225


def test_registrar_modelo_desconocido(db):
    r = cliente.post("/llamadas", json={**LLAMADA, "modelo": "modelo-inventado"})
    assert r.status_code == 400


def test_informe_semanal(db):
    informe = cliente.get("/informe-semanal", params={"fecha": "2026-11-11"}).json()
    assert informe[0]["equipo"] == "datos"
    assert informe[0]["estado"] == "superado"
