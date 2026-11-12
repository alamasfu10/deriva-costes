"""Tarifas de los modelos y cálculo del coste de una llamada.

Es el único sitio donde se calcula un coste. tests/test_tarifas.py fija su
comportamiento: si cambias una regla, cambia también su test y explica por qué.
"""

from typing import Optional

# Precios en USD por millón de tokens. Los de contexto largo se aplican a
# toda la llamada cuando la entrada pasa de UMBRAL_CONTEXTO_LARGO.
TARIFAS = {
    "orca-large": {"entrada": 3.00, "salida": 15.00, "cache": 0.30, "entrada_largo": 6.00, "salida_largo": 22.50},
    "orca-mini": {"entrada": 0.25, "salida": 1.25, "cache": 0.025},
    "nautilus-flash": {"entrada": 0.30, "salida": 2.50, "cache": 0.075},
    "nautilus-pro": {"entrada": 1.25, "salida": 10.00, "cache": 0.3125, "entrada_largo": 2.50, "salida_largo": 15.00},
}
UMBRAL_CONTEXTO_LARGO = 200_000
DESCUENTO_LOTE = 0.5  # las llamadas por lotes pagan la mitad


def calcular_coste(
    modelo: str, tokens_entrada: int, tokens_salida: int, tokens_cache: Optional[int], lote: bool
) -> float:
    """Coste en USD de una llamada.

    tokens_entrada incluye los tokens en caché, que se cobran a su precio de
    caché, también en contexto largo. Un tokens_cache a None cuenta como 0.
    """
    if modelo not in TARIFAS:
        raise ValueError(f"Modelo sin tarifa: {modelo}")
    tarifa = TARIFAS[modelo]
    cache = tokens_cache or 0
    largo = tokens_entrada > UMBRAL_CONTEXTO_LARGO and "entrada_largo" in tarifa
    precio_entrada = tarifa["entrada_largo"] if largo else tarifa["entrada"]
    precio_salida = tarifa["salida_largo"] if largo else tarifa["salida"]

    coste = (tokens_entrada - cache) * precio_entrada
    coste += cache * tarifa["cache"]
    coste += tokens_salida * precio_salida
    coste /= 1_000_000
    if lote:
        coste *= DESCUENTO_LOTE
    return round(coste, 6)
