"""Tests de caracterización de calcular_coste().

Fijan lo que hacía el código heredado ANTES del refactor: los valores
esperados salen de ejecutar la versión original, no de una hoja de cálculo.
Si un refactor cambia uno de estos números, el refactor está mal (o la regla
ha cambiado a propósito, y entonces se cambia el test y se explica por qué).
"""

import pytest

from tarifas import calcular_coste


@pytest.mark.parametrize(
    "modelo, entrada, salida, cache, lote, esperado",
    [
        # caso normal, sin caché ni lote
        ("orca-mini", 1_000, 500, 0, False, 0.000875),
        # la caché se cobra a su precio, no al de entrada
        ("orca-large", 30_000, 1_000, 18_000, False, 0.0564),
        # contexto largo: toda la llamada a precio largo, la caché a precio de caché
        ("orca-large", 250_000, 2_000, 75_000, False, 1.1175),
        # el umbral es estricto: 200.000 justos no es contexto largo
        ("orca-large", 200_000, 2_000, 0, False, 0.63),
        # un modelo sin precio largo no cambia de precio aunque pase del umbral
        ("orca-mini", 250_000, 1_000, 0, False, 0.06375),
        # lote: la mitad de todo
        ("nautilus-flash", 5_000, 5_000, 0, True, 0.007),
        # contexto largo, caché y lote a la vez
        ("nautilus-pro", 210_000, 1_000, 100_000, True, 0.160625),
    ],
)
def test_coste_de_una_llamada(modelo, entrada, salida, cache, lote, esperado):
    assert calcular_coste(modelo, entrada, salida, cache, lote) == pytest.approx(esperado)


def test_cache_nula_cuenta_como_cero():
    assert calcular_coste("orca-mini", 1_000, 500, None, False) == calcular_coste("orca-mini", 1_000, 500, 0, False)


def test_modelo_sin_tarifa():
    with pytest.raises(ValueError):
        calcular_coste("modelo-inventado", 1_000, 500, 0, False)
