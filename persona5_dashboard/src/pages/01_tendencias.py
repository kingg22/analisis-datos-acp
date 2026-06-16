"""
Página de Análisis de Tendencias — Canal de Panamá
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
    load_estacionalidad_fase_fiscal,
    load_descomposicion_serie,
    load_componente_estacional,
    load_ranking_segmentos,
    load_tendencia_anual,
    load_canal_unificado,
    get_figure_path,
)

st.set_page_config(page_title="Tendencias — Canal de Panamá", page_icon="📈", layout="wide")
st.title("📈 Análisis de Tendencias")
st.caption("Análisis exploratorio de tránsitos del Canal de Panamá")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Serie Temporal",
    "🚢 Por Segmento",
    "📅 Estacionalidad",
    "📉 Descomposición",
    "🖼️ Figuras EDA",
])

with tab1:
    st.subheader("Evolución Mensual de Tránsitos")
    serie = load_agregado_serie_total()

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=serie["fecha"], y=serie["transitos_totales"],
        mode="lines+markers", name="Tránsitos",
        line=dict(color="#1f77b4", width=2), marker=dict(size=4),
    ))
    fig.update_layout(xaxis_title="Fecha", yaxis_title="Tránsitos Totales",
                      hovermode="x unified", height=450)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Tendencia Anual")
    tendencia = load_tendencia_anual()
    col1, col2 = st.columns([2, 1])
    with col1:
        fig_tend = go.Figure()
        fig_tend.add_trace(go.Bar(
            x=tendencia["anio"], y=tendencia["transitos_anuales"],
            name="Tránsitos", marker_color="#1f77b4",
        ))
        fig_tend.update_layout(xaxis_title="Año", yaxis_title="Tránsitos", height=350)
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

    st.subheader("Evolución por Segmento")
    unificado = load_canal_unificado()
    if "segmento" in unificado.columns:
        agg = unificado.groupby(["fecha", "segmento"])["transitos"].sum().reset_index()
        fig_evol = px.line(agg, x="fecha", y="transitos", color="segmento",
                           title="Tránsitos por Segmento en el Tiempo")
        fig_evol.update_layout(height=450)
        st.plotly_chart(fig_evol, use_container_width=True)

with tab3:
    st.subheader("Patrones Estacionales")
    estacional = load_componente_estacional()

    meses = {1: "Ene", 2: "Feb", 3: "Mar", 4: "Abr", 5: "May", 6: "Jun",
             7: "Jul", 8: "Ago", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dic"}
    estacional["mes_nombre"] = estacional["fecha"].map(meses)

    fig_est = px.bar(
        estacional, x="mes_nombre", y="componente_estacional",
        title="Estacionalidad por Mes Calendario",
        color="componente_estacional", color_continuous_scale="Blues",
    )
    fig_est.update_layout(height=350, xaxis_title="Mes", yaxis_title="Componente Estacional")
    st.plotly_chart(fig_est, use_container_width=True)

    st.subheader("Estacionalidad por Fase Fiscal ACP")
    ff = load_estacionalidad_fase_fiscal()
    if not ff.empty:
        pivot = ff.pivot_table(
            index="fase_fiscal", columns="segmento",
            values="transitos_promedio", aggfunc="mean",
        )
        fig_heat = px.imshow(pivot, title="Heatmap: Fase Fiscal × Segmento",
                             color_continuous_scale="YlOrRd", aspect="auto")
        fig_heat.update_layout(height=400)
        st.plotly_chart(fig_heat, use_container_width=True)

with tab4:
    st.subheader("Descomposición de la Serie")
    descomp = load_descomposicion_serie()
    componentes = [c for c in ["observado", "tendencia", "estacional", "residuo"] if c in descomp.columns]

    if componentes:
        fig_descomp = go.Figure()
        for comp in componentes:
            fig_descomp.add_trace(go.Scatter(
                x=descomp["fecha"], y=descomp[comp],
                name=comp.capitalize(), mode="lines",
            ))
        fig_descomp.update_layout(height=600, hovermode="x unified",
                                  title="Componentes de la Serie Temporal")
        st.plotly_chart(fig_descomp, use_container_width=True)

with tab5:
    st.subheader("Visualizaciones del Análisis Exploratorio")
    st.markdown("Figuras generadas por **Persona 3** en su pipeline de análisis.")

    figuras = [
        ("01_serie_mensual.png", "Serie Mensual"),
        ("02_descomposicion_estacional.png", "Descomposición Estacional"),
        ("03_subserie_estacional.png", "Subserie Estacional"),
        ("04_composicion_por_segmento.png", "Composición por Segmento"),
        ("05_ranking_segmentos.png", "Ranking de Segmentos"),
        ("06_comparativa_periodos.png", "Comparativa de Períodos"),
        ("07_heatmap_correlacion.png", "Heatmap de Correlación"),
        ("08_estacionalidad_fase_fiscal.png", "Estacionalidad Fase Fiscal"),
        ("09_tendencia_anual.png", "Tendencia Anual"),
        ("10_precio_vs_transitos.png", "Precio vs Tránsitos"),
    ]

    cols = st.columns(2)
    for i, (fname, titulo) in enumerate(figuras):
        with cols[i % 2]:
            path = get_figure_path("persona3_analisis", fname)
            if path.exists():
                st.image(str(path), caption=titulo, use_container_width=True)
            else:
                st.warning(f"No disponible: {fname}")
