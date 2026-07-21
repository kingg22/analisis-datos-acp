"""
Página de Análisis de Tendencias — Canal de Panamá (anual)
"""
from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px

src_dir = str(Path(__file__).resolve().parent.parent)
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from utils.data_loader import (
    load_agregado_serie_total,
    load_agregado_por_segmento,
    load_ranking_segmentos,
    load_tendencia_anual,
    load_canal_unificado,
    get_figure_path,
)

st.set_page_config(page_title="Tendencias — Canal de Panamá", page_icon="📈", layout="wide")
st.title("📈 Análisis de Tendencias")
st.caption("Análisis exploratorio anual de tránsitos del Canal de Panamá (año fiscal ACP)")

tab1, tab2, tab3 = st.tabs([
    "📊 Serie Anual",
    "🚢 Por Segmento",
    "🖼️ Figuras EDA",
])

with tab1:
    st.subheader("Evolución Anual de Tránsitos")
    serie = load_agregado_serie_total()

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=serie["anio_fiscal"], y=serie["transitos_totales"],
        mode="lines+markers", name="Tránsitos",
        line=dict(color="#1f77b4", width=2), marker=dict(size=8),
    ))
    fig.update_layout(xaxis_title="Año fiscal", yaxis_title="Tránsitos Totales",
                      hovermode="x unified", height=450)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Tendencia Anual")
    tendencia = load_tendencia_anual()
    col1, col2 = st.columns([2, 1])
    with col1:
        fig_tend = go.Figure()
        fig_tend.add_trace(go.Bar(
            x=tendencia["anio_fiscal"], y=tendencia["transitos_anuales"],
            name="Tránsitos", marker_color="#1f77b4",
        ))
        fig_tend.update_layout(xaxis_title="Año fiscal", yaxis_title="Tránsitos", height=350)
        st.plotly_chart(fig_tend, use_container_width=True)
    with col2:
        st.dataframe(tendencia, hide_index=True, use_container_width=True)

with tab2:
    st.subheader("Distribución por Segmento de Buque")
    ranking = load_ranking_segmentos()
    segmentos = load_agregado_por_segmento()

    col1, col2 = st.columns(2)
    with col1:
        fig_rank = px.bar(
            ranking.head(10), x="transitos_total", y="segmento",
            orientation="h", title="Ranking de Segmentos",
            color="segmento", color_discrete_sequence=px.colors.qualitative.Set2,
        )
        fig_rank.update_layout(yaxis=dict(autorange="reversed"), height=400, showlegend=False)
        st.plotly_chart(fig_rank, use_container_width=True)
    with col2:
        fig_pie = px.pie(
            segmentos.groupby("segmento")["transitos"].sum().reset_index(),
            names="segmento", values="transitos",
            title="Composición por Segmento", hole=0.4,
        )
        fig_pie.update_layout(height=400)
        st.plotly_chart(fig_pie, use_container_width=True)

    st.subheader("Evolución por Segmento (por año fiscal)")
    unificado = load_canal_unificado()
    if "segmento" in unificado.columns:
        agg = unificado.groupby(["anio_fiscal", "segmento"])["transitos"].sum().reset_index()
        fig_evol = px.line(agg, x="anio_fiscal", y="transitos", color="segmento",
                           markers=True, title="Tránsitos por Segmento y Año Fiscal")
        fig_evol.update_layout(height=450, xaxis_title="Año fiscal")
        st.plotly_chart(fig_evol, use_container_width=True)

with tab3:
    st.subheader("Visualizaciones del Análisis Exploratorio")
    st.markdown("Figuras generadas por **Persona 3** en su pipeline de análisis (anual).")

    figuras = [
        ("01_serie_anual.png", "Serie Anual"),
        ("02_composicion_por_segmento.png", "Composición por Segmento"),
        ("03_ranking_segmentos.png", "Ranking de Segmentos"),
        ("04_comparativa_periodos.png", "Comparativa de Períodos"),
        ("05_heatmap_correlacion.png", "Heatmap de Correlación"),
        ("06_tendencia_anual.png", "Tendencia Anual"),
        ("07_precio_vs_transitos.png", "Precio vs Tránsitos"),
    ]

    cols = st.columns(2)
    for i, (fname, titulo) in enumerate(figuras):
        with cols[i % 2]:
            path = get_figure_path("persona3_analisis", fname)
            if path.exists():
                st.image(str(path), caption=titulo, use_container_width=True)
            else:
                st.warning(f"No disponible: {fname}")
