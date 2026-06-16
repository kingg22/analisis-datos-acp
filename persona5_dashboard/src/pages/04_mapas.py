"""
Página de Mapas — Canal de Panamá
"""
from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

src_dir = str(Path(__file__).resolve().parent.parent)
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from utils.data_loader import (
    load_canal_serie_mensual,
    load_ranking_segmentos,
    load_agregado_por_segmento,
)

st.title("🗺️ Mapas del Canal de Panamá")
st.caption("Visualización geográfica del tránsito marítimo")

# ── Coordenadas del Canal de Panamá ─────────────────────────────────────────
PANAMA_CENTER = {"lat": 9.1, "lon": -79.5}
PUNTOS_CANAL = {
    "Entrada Pacífico (Balboa)": {"lat": 8.955, "lon": -79.535},
    "Esclusa de Miraflores": {"lat": 8.992, "lon": -79.565},
    "Esclusa de Pedro Miguel": {"lat": 9.017, "lon": -79.581},
    "Lago Gatún": {"lat": 9.200, "lon": -79.850},
    "Esclusa de Gatún": {"lat": 9.270, "lon": -79.920},
    "Entrada Atlántico (Colón)": {"lat": 9.360, "lon": -79.970},
}

tab1, tab2, tab3 = st.tabs(["📍 Ubicación del Canal", "🚢 Ruta Marítima", "📊 Tránsitos por Zona"])

# ── Tab 1: Mapa de ubicación ────────────────────────────────────────────────
with tab1:
    st.subheader("Ubicación del Canal de Panamá")

    df_puntos = pd.DataFrame([
        {"nombre": k, **v} for k, v in PUNTOS_CANAL.items()
    ])

    fig_map = px.scatter_mapbox(
        df_puntos,
        lat="lat",
        lon="lon",
        hover_name="nombre",
        zoom=10,
        height=550,
        mapbox_style="carto-positron",
        title="Puntos Principales del Canal",
    )
    fig_map.update_layout(
        margin=dict(l=0, r=0, t=40, b=0),
    )
    st.plotly_chart(fig_map, use_container_width=True)

    st.markdown("""
    **El Canal de Panamá** conecta el océano Pacífico con el Atlántico a través de 80 km de vía navegable.
    Los puntos clave incluyen las esclusas de Miraflores, Pedro Miguel y Gatún, así como el Lago Gatún.
    """)

# ── Tab 2: Ruta marítima ───────────────────────────────────────────────────
with tab2:
    st.subheader("Ruta a través del Canal")

    # Ruta simplificada del canal (coordenadas)
    ruta_lat = [8.955, 8.970, 8.992, 9.017, 9.050, 9.100, 9.150, 9.200, 9.240, 9.270, 9.300, 9.340, 9.360]
    ruta_lon = [-79.535, -79.545, -79.565, -79.581, -79.620, -79.700, -79.780, -79.850, -79.890, -79.920, -79.940, -79.960, -79.970]

    fig_ruta = go.Figure()

    # Línea de ruta
    fig_ruta.add_trace(go.Scattermapbox(
        lat=ruta_lat,
        lon=ruta_lon,
        mode="lines",
        line=dict(width=4, color="#1f77b4"),
        name="Ruta del Canal",
    ))

    # Puntos de esclusas
    fig_ruta.add_trace(go.Scattermapbox(
        lat=[p["lat"] for p in PUNTOS_CANAL.values()],
        lon=[p["lon"] for p in PUNTOS_CANAL.values()],
        mode="markers+text",
        marker=dict(size=12, color="#ff7f0e"),
        text=list(PUNTOS_CANAL.keys()),
        textposition="top center",
        name="Esclusas",
    ))

    fig_ruta.update_layout(
        mapbox=dict(
            style="carto-positron",
            center=PANAMA_CENTER,
            zoom=10,
        ),
        height=550,
        margin=dict(l=0, r=0, t=40, b=0),
        showlegend=True,
    )
    st.plotly_chart(fig_ruta, use_container_width=True)

    st.markdown("""
    **La ruta** va desde Balboa (Pacífico) pasando por las esclusas de Miraflores y Pedro Miguel,
    cruza el Lago Gatún y termina en Colón (Atlántico). El recorrido toma aproximadamente 8-10 horas.
    """)

# ── Tab 3: Tránsitos por zona ──────────────────────────────────────────────
with tab3:
    st.subheader("Tránsitos Mensuales en el Tiempo")

    serie = load_canal_serie_mensual()

    fig_cantidad = px.line(
        serie, x="fecha", y="transitos_totales",
        title="Tránsitos Mensuales del Canal",
        labels={"fecha": "Fecha", "transitos_totales": "Tránsitos"},
    )
    fig_cantidad.update_traces(line=dict(color="#1f77b4", width=2))
    fig_cantidad.update_layout(height=400)
    st.plotly_chart(fig_cantidad, use_container_width=True)

    st.subheader("Distribución por Segmento (Top 5)")
    ranking = load_ranking_segmentos().head(5)

    fig_bars = px.bar(
        ranking, x="segmento", y="transitos_total",
        color="segmento",
        title="Top 5 Segmentos por Tránsitos Totales",
        color_discrete_sequence=px.colors.qualitative.Set2,
    )
    fig_bars.update_layout(height=350, showlegend=False)
    st.plotly_chart(fig_bars, use_container_width=True)

    # Mapa de calor por mes y segmento
    st.subheader("Mapa de Calor: Segmento × Mes")
    segmentos_df = load_agregado_por_segmento()
    if not segmentos_df.empty and "segmento" in segmentos_df.columns:
        pivot = segmentos_df.pivot_table(
            index="segmento", columns="anio",
            values="transitos", aggfunc="sum",
        )
        fig_heat = px.imshow(
            pivot, title="Tránsitos por Segmento y Año",
            color_continuous_scale="YlOrRd", aspect="auto",
            labels=dict(x="Año", y="Segmento", color="Tránsitos"),
        )
        fig_heat.update_layout(height=400)
        st.plotly_chart(fig_heat, use_container_width=True)
