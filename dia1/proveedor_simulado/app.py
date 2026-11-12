"""API de uso de Abisal, simulada para clase.

Sirve el histórico de llamadas a los modelos orca-* de Deriva, igual que lo
haría la API real de un proveedor: paginada, con clave y con límite de
peticiones.

Arrancar con: uvicorn proveedor_simulado.app:app --port 8100
Contrato: proveedor_simulado/openapi.json (o http://localhost:8100/docs)
"""

import json
from pathlib import Path
from typing import Annotated, Optional

from fastapi import FastAPI, Header, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

CLAVE_PRUEBA = "abisal-clave-de-prueba"
PETICIONES_ANTES_DE_LIMITE = 4  # la quinta petición seguida responde 429

_DATOS = json.loads((Path(__file__).parent / "uso_abisal.json").read_text(encoding="utf-8"))
_contador = {"peticiones": 0}

app = FastAPI(
    title="Abisal Usage API (simulada)",
    version="1.0.0",
    description=(
        "Uso de los modelos de Abisal por organización. Simulación para el Tema 12 del MID de EBIS. "
        "Autenticación con la cabecera X-Abisal-Key. Paginación por cursor: repite la petición con "
        "`cursor=next_cursor` hasta que `next_cursor` sea null. Si superas el límite de peticiones, "
        "responde 429 con la cabecera Retry-After en segundos."
    ),
)


class Usage(BaseModel):
    input_tokens: int = Field(description="Tokens de entrada, incluidos los servidos desde caché")
    output_tokens: int
    cached_input_tokens: int = Field(description="Parte de input_tokens servida desde caché")


class Metadata(BaseModel):
    team: str
    project: str


class UsageRecord(BaseModel):
    request_id: str
    created_at: str = Field(description="Fecha y hora en UTC, ISO 8601")
    metadata: Metadata
    model: str
    usage: Usage
    batch: bool


class UsagePage(BaseModel):
    data: list[UsageRecord]
    next_cursor: Optional[str] = Field(description="Cursor de la página siguiente, o null si no hay más")


class ErrorBody(BaseModel):
    error: str


@app.get(
    "/v1/usage",
    response_model=UsagePage,
    responses={401: {"model": ErrorBody}, 429: {"model": ErrorBody}},
    summary="Lista el uso entre dos fechas",
)
def listar_uso(
    start_date: Annotated[str, Query(description="Fecha inicial incluida, AAAA-MM-DD")],
    end_date: Annotated[str, Query(description="Fecha final incluida, AAAA-MM-DD")],
    x_abisal_key: Annotated[Optional[str], Header()] = None,
    cursor: Optional[str] = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
):
    if x_abisal_key != CLAVE_PRUEBA:
        return JSONResponse({"error": "invalid_api_key"}, status_code=401)

    _contador["peticiones"] += 1
    if _contador["peticiones"] > PETICIONES_ANTES_DE_LIMITE:
        _contador["peticiones"] = 0
        return JSONResponse({"error": "rate_limited"}, status_code=429, headers={"Retry-After": "1"})

    seleccion = [r for r in _DATOS if start_date <= r["created_at"][:10] <= end_date]
    inicio = int(cursor) if cursor else 0
    pagina = seleccion[inicio : inicio + limit]
    siguiente = str(inicio + limit) if inicio + limit < len(seleccion) else None
    return {"data": pagina, "next_cursor": siguiente}
