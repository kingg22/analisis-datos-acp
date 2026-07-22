"""
Página Principal — Canal de Panamá
"""
from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

src_dir = str(Path(__file__).resolve().parent)
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from utils.data_loader import (
    load_agregado_por_periodo,
    load_agregado_serie_total,
    load_insights,
    load_predicciones_2026,
    load_resumen_entrenamiento,
    load_tendencia_anual,
)

st.set_page_config(
    page_title="Canal de Panamá — Dashboard",
    page_icon="🚢",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .block-container { padding-top: 1rem; }
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
        border-radius: 10px; padding: 12px 16px; color: white;
    }
    div[data-testid="stMetric"] label { color: #a0c4ff; }
    div[data-testid="stMetric"] [data-testid="stMetricValue"] { color: #ffffff; }
    </style>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("# 🚢 Canal de Panamá")
    st.caption("Dashboard Interactivo — Grupo 8")
    st.divider()
    st.markdown("**Navegación**")
    st.page_link("app.py", label="🏠 Inicio", icon="🏠")
    st.page_link("pages/01_tendencias.py", label="📈 Tendencias", icon="📈")
    st.page_link("pages/02_modelo_predictivo.py", label="🤖 Modelo Predictivo", icon="🤖")
    st.page_link("pages/04_mapas.py", label="🗺️ Mapas", icon="🗺️")
    st.page_link("pages/03_resumen_llm.py", label="🧠 Resumen LLM", icon="🧠")
    st.divider()
    st.caption("Segundo Parcial — Semanas 9-11")

st.title("🏠 Panorama General — Canal de Panamá")

try:
    serie = load_agregado_serie_total()
    pred = load_predicciones_2026()
    resumen = load_resumen_entrenamiento()
    insights = load_insights()
    periodos = load_agregado_por_periodo()
    tendencia = load_tendencia_anual()
except Exception as e:
    st.error(f"Error cargando datos: {e}")
    st.stop()

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Tránsitos/Año (prom)", f"{serie['transitos_totales'].mean():,.0f}")
with col2:
    st.metric("Peajes/Año (prom)", f"${serie['peajes_totales_usd'].mean():,.0f}")
with col3:
    calado_promedio = serie["calado_promedio_pies"].mean()
    calado_texto = (
        f"{calado_promedio:.1f} pies" if pd.notna(calado_promedio) else "No disponible"
    )
    st.metric("Calado Promedio", calado_texto)
with col4:
    modelo = resumen.get("modelo_ganador", "N/A").replace("_", " ")
    st.metric("Modelo ML", modelo)

st.divider()

st.subheader("📈 Evolución Anual de Tránsitos")

fig = go.Figure()
fig.add_trace(
    go.Scatter(
        x=serie["anio_fiscal"],
        y=serie["transitos_totales"],
        mode="lines+markers",
        name="Histórico",
        line=dict(color="#1f77b4", width=2),
    )
)
fig.add_trace(
    go.Scatter(
        x=pred["anio_fiscal"],
        y=pred["transitos_predichos"],
        mode="lines+markers",
        name="Pronóstico",
        line=dict(color="#ff7f0e", width=2, dash="dash"),
    )
)
fig.update_layout(
    xaxis_title="Año fiscal",
    yaxis_title="Tránsitos",
    hovermode="x unified",
    height=400,
    margin=dict(l=0, r=0, t=30, b=0),
)
st.plotly_chart(fig, use_container_width=True)

st.subheader("💡 Insights Clave del Análisis")
cols = st.columns(3)
for i, insight in enumerate(insights):
    with cols[i % 3]:
        with st.expander(f"**{insight['titulo']}**", expanded=True):
            st.write(insight["detalle"])

st.subheader("📊 Tendencia Anual")
fig_tend = go.Figure()
fig_tend.add_trace(
    go.Bar(
        x=tendencia["anio_fiscal"],
        y=tendencia["transitos_anuales"],
        name="Tránsitos",
        marker_color="#1f77b4",
    )
)
fig_tend.update_layout(xaxis_title="Año fiscal", yaxis_title="Tránsitos", height=350, showlegend=False)
st.plotly_chart(fig_tend, use_container_width=True)

st.subheader("📊 Comparativa de Períodos")
periodos_agg = periodos.groupby("periodo").agg({
    "transitos_promedio": "sum",
    "peajes_promedio_usd": "sum",
}).reset_index()

col_a, col_b = st.columns(2)
with col_a:
    st.dataframe(
        periodos_agg.style.format("{:,.0f}", subset=["transitos_promedio", "peajes_promedio_usd"]),
        use_container_width=True,
        hide_index=True,
    )
with col_b:
    fig_bar = px.bar(
        periodos_agg,
        x="periodo",
        y="transitos_promedio",
        color="periodo",
        title="Tránsitos Promedio por Período",
        color_discrete_sequence=px.colors.qualitative.Set2,
    )
    fig_bar.update_layout(showlegend=False, height=350, margin=dict(l=0, r=0, t=40, b=0))
    st.plotly_chart(fig_bar, use_container_width=True)

st.divider()
st.caption(
    "Grupo 8 — Análisis de Datos del Canal de Panamá | "
    "Segundo Parcial · Pipeline + Visualización | Persona 5: Dashboard"
)
