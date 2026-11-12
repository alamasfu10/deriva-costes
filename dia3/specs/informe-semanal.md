# Especificación · informe semanal por equipo

## Qué hace

Cada lunes, el CTO de Deriva quiere ver de un vistazo cómo va cada equipo:
cuánto gastó la última semana, cuánto lleva en el mes, cuánto le queda de
presupuesto y si, al ritmo actual, se va a pasar antes de fin de mes.

## Entradas

| Entrada | De dónde sale | Valores |
|---|---|---|
| `fecha` | Parámetro opcional | Fecha del informe. Por defecto, `HOY` |

## Salida

Una lista con un diccionario por equipo, ordenada de mayor a menor previsión:

| Campo | Qué es |
|---|---|
| `equipo` | Nombre del equipo |
| `gasto_semana` | USD de los 7 días que terminan en `fecha`, incluida |
| `gasto_mes` | USD desde el día 1 del mes de `fecha` hasta `fecha`, incluida |
| `presupuesto` | Presupuesto mensual del equipo |
| `restante` | `presupuesto - gasto_mes`. Puede ser negativo |
| `prevision_mes` | Gasto previsto a fin de mes al ritmo actual: `gasto_mes / dias_transcurridos * dias_del_mes` |
| `estado` | `superado` si `gasto_mes >= presupuesto`; `en riesgo` si no, pero `prevision_mes > presupuesto`; `ok` en el resto |

Importes redondeados a dos decimales.

## Dónde aparece

- Función `informe_semanal(fecha=None)` en `main.py`.
- Endpoint `GET /informe-semanal?fecha=AAAA-MM-DD`.
- Panel: sección «Informe semanal» al principio, con una fila por equipo.

## Criterios de aceptación

1. El coste de cada llamada sale de `calcular_coste()`, a través de las
   funciones que ya existen. La fórmula no se repite.
2. Con `fecha = 2026-11-11`, el equipo `datos` aparece primero, con
   `gasto_mes` de 128,35 y estado `superado`.
3. Con `fecha = 2026-10-15`, ningún equipo está `superado` y la previsión de
   `datos` es mayor que su `gasto_mes`.
4. `dias_transcurridos` es el día del mes de `fecha` (el 11 de noviembre, 11).
5. Un equipo sin llamadas en el periodo aparece con gasto 0 y estado `ok`.
6. Sin dependencias nuevas, sin ORM y sin pandas en `main.py`.
7. El endpoint responde 400 con un mensaje claro si `fecha` no tiene formato
   `AAAA-MM-DD`.

## Fuera de alcance

- Enviar el informe por correo.
- Previsiones que no sean lineales.
- Arreglar los avisos de presupuesto (se trata aparte).
