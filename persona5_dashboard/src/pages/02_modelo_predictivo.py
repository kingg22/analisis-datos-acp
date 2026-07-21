"""
Página de Modelo Predictivo — Canal de Panamá (anual)
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
    load_predicciones_2026,
    load_predicciones_test,
    load_metricas_modelos,
    load_importancia_features,
    load_resumen_entrenamiento,
    load_agregado_serie_total,
    get_figure_path,
)

st.set_page_config(page_title="Modelo Predictivo — Canal de Panamá", page_icon="🤖", layout="wide")
st.title("🤖 Modelo Predictivo")
st.caption("Pronóstico de tránsitos anuales del Canal de Panamá (año fiscal ACP)")

resumen = load_resumen_entrenamiento()
metricas = load_metricas_modelos()

ganador = resumen["modelo_ganador"]
met_ganador = resumen.get("metricas", {}).get(ganador, {})

st.info(
    "La serie de tránsitos es anual (un punto por año fiscal), por lo que se usa "
    "un modelo simple e interpretable, validado con **Leave-One-Out**."
)

st.subheader("🏆 Modelo Ganador")
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Modelo", ganador.replace("_", " "))
with col2:
    st.metric("MAPE (LOO)", f"{met_ganador.get('MAPE', 0):.2f}%")
with col3:
    st.metric("MAE (LOO)", f"{met_ganador.get('MAE', 0):,.0f}")
with col4:
    st.metric("Años fiscales", resumen.get("n_observaciones", "N/A"))

st.divider()

tab1, tab2, tab3, tab4 = st.tabs([
    "🔮 Pronóstico",
    "📊 Comparativa Modelos",
    "🎯 Coeficientes",
    "🖼️ Figuras del Modelo",
])

with tab1:
    st.subheader("Pronóstico de Tránsitos (próximos años fiscales)")
    serie = load_agregado_serie_total()
    pred = load_predicciones_2026()

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=serie["anio_fiscal"], y=serie["transitos_totales"],
        mode="lines+markers", name="Histórico", line=dict(color="#1f77b4", width=2),
    ))
    fig.add_trace(go.Scatter(
        x=pred["anio_fiscal"], y=pred["transitos_predichos"],
        mode="lines+markers", name="Pronóstico",
        line=dict(color="#ff7f0e", width=2, dash="dash"),
        marker=dict(size=10, symbol="diamond"),
    ))
    fig.update_layout(
        xaxis_title="Año fiscal", yaxis_title="Tránsitos",
        hovermode="x unified", height=500,
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("📋 Detalle de Predicciones")
    pred_display = pred.copy()
    pred_display["transitos_predichos"] = pred_display["transitos_predichos"].astype(int)
    st.dataframe(pred_display, hide_index=True, use_container_width=True)

with tab2:
    st.subheader("Comparativa de Modelos Evaluados (Leave-One-Out)")

    if not metricas.empty:
        col1, col2 = st.columns(2)
        with col1:
            fig_mape = px.bar(
                metricas, x="modelo", y="MAPE",
                title="MAPE en Leave-One-Out",
                color="modelo", color_discrete_sequence=px.colors.qualitative.Set2,
            )
            fig_mape.update_layout(height=350, showlegend=False)
            st.plotly_chart(fig_mape, use_container_width=True)
        with col2:
            fig_mae = px.bar(
                metricas, x="modelo", y="MAE",
                title="MAE en Leave-One-Out",
                color="modelo", color_discrete_sequence=px.colors.qualitative.Pastel,
            )
            fig_mae.update_layout(height=350, showlegend=False)
            st.plotly_chart(fig_mae, use_container_width=True)

        st.dataframe(metricas, hide_index=True, use_container_width=True)

    st.subheader("Validación: Reales vs Predichos (LOO)")
    test = load_predicciones_test()
    if not test.empty:
        fig_test = go.Figure()
        fig_test.add_trace(go.Scatter(
            x=test["anio_fiscal"], y=test["transitos_reales"],
            mode="lines+markers", name="Reales", line=dict(color="#1f77b4"),
        ))
        fig_test.add_trace(go.Scatter(
            x=test["anio_fiscal"], y=test["transitos_predichos"],
            mode="lines+markers", name="Predichos", line=dict(color="#ff7f0e", dash="dash"),
        ))
        fig_test.update_layout(height=400, hovermode="x unified",
                               xaxis_title="Año fiscal",
                               title="Leave-One-Out: Reales vs Predichos")
        st.plotly_chart(fig_test, use_container_width=True)

with tab3:
    st.subheader("¿Qué variables impulsan la predicción?")
    features = load_importancia_features()
    valor_col = features.columns[1] if features.shape[1] > 1 else None
    if not features.empty and valor_col:
        fig_imp = px.bar(
            features.sort_values(valor_col, ascending=True),
            x=valor_col, y="feature", orientation="h",
            title="Coeficientes (magnitud) del modelo ganador",
            color=valor_col, color_continuous_scale="Viridis",
        )
        fig_imp.update_layout(height=350)
        st.plotly_chart(fig_imp, use_container_width=True)
        st.dataframe(features, hide_index=True, use_container_width=True)
    else:
        st.info(
            "El modelo ganador es un baseline (media histórica) sin coeficientes: "
            "con tan pocos años, un promedio superó a los modelos de tendencia."
        )

with tab4:
    st.subheader("Visualizaciones del Modelo")
    figuras = [
        ("01_comparativa_modelos.png", "Comparativa de Modelos"),
        ("02_ajuste_loo.png", "Ajuste Leave-One-Out"),
        ("03_importancia_features.png", "Coeficientes"),
        ("04_pronostico_anual.png", "Pronóstico Anual"),
    ]
    cols = st.columns(2)
    for i, (fname, titulo) in enumerate(figuras):
        with cols[i % 2]:
            path = get_figure_path("persona4_modelo", fname)
            if path.exists():
                st.image(str(path), caption=titulo, use_container_width=True)
            else:
                st.warning(f"No disponible: {fname}")
