"""Panel de gasto en IA de Deriva. Arrancar con: streamlit run panel.py"""

import streamlit as st

import main

st.set_page_config(page_title="Deriva · gasto en IA", layout="wide")
st.title("Gasto en IA por equipo")

mes = st.sidebar.text_input("Mes (AAAA-MM)", main.mes_actual())
st.sidebar.caption(f"Datos hasta el {main.HOY:%d/%m/%Y}")

st.subheader("Informe semanal")
st.dataframe(main.informe_semanal(), width="stretch", hide_index=True)

alertas = main.comprobar_presupuestos(mes)
if alertas:
    for a in alertas:
        texto = f"{a['equipo']}: {a['gasto']:.2f} de {a['presupuesto']:.0f} USD"
        if a["nivel"] == "superado":
            st.error(f"Presupuesto superado · {texto}")
        else:
            st.warning(f"Cerca del presupuesto · {texto}")
else:
    st.success("Ningún equipo cerca de su presupuesto")

gasto = main.gasto_por_equipo(mes)
st.subheader("Este mes")
columnas = st.columns(len(gasto))
for col, g in zip(columnas, gasto):
    col.metric(g["equipo"], f"{g['gasto']:.2f} USD", f"{g['porcentaje']}% del presupuesto", delta_color="off")

st.subheader("Por proyecto")
equipo = st.selectbox("Equipo", [g["equipo"] for g in gasto])
st.dataframe(main.gasto_por_proyecto(equipo, mes), width="stretch", hide_index=True)

if st.button(f"Explicar el gasto de {equipo}"):
    with st.spinner("Preguntando al modelo..."):
        try:
            st.write(main.explicar_subida(equipo))
        except Exception as e:
            st.error(f"No se pudo generar la explicación: {e}")

st.subheader("Las 10 llamadas más caras del mes")
caras = main.llamadas_mas_caras(mes)
st.dataframe(
    [{k: c[k] for k in ("fecha", "equipo", "proyecto", "modelo", "tokens_entrada", "tokens_salida", "coste")} for c in caras],
    width="stretch",
    hide_index=True,
)
