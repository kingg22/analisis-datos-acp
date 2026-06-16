"""
Página de Modelo Predictivo — Canal de Panamá
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
st.caption("Pronóstico de tránsitos mensuales del Canal de Panamá")

resumen = load_resumen_entrenamiento()
metricas = load_metricas_modelos()

st.subheader("🏆 Modelo Ganador")

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Modelo", resumen["modelo_ganador"].replace("_", " "))
with col2:
    best = resumen["cross_validation"].get(resumen["modelo_ganador"], {})
    st.metric("MAPE CV", f"{best.get('MAPE_cv', 0):.2f}%")
with col3:
    st.metric("Muestra Train", resumen.get("n_train", "N/A"))
with col4:
    st.metric("Muestra Test", resumen.get("n_test", "N/A"))

st.divider()

tab1, tab2, tab3, tab4 = st.tabs([
    "🔮 Pronóstico 2026",
    "📊 Comparativa Modelos",
    "🎯 Importancia Features",
    "🖼️ Figuras del Modelo",
])

with tab1:
    st.subheader("Pronóstico de Tránsitos 2026")
    serie = load_agregado_serie_total()
    pred = load_predicciones_2026()

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=serie["fecha"], y=serie["transitos_totales"],
        mode="lines", name="Histórico", line=dict(color="#1f77b4", width=2),
    ))
    fig.add_trace(go.Scatter(
        x=pred["fecha"], y=pred["transitos_predichos"],
        mode="lines+markers", name="Pronóstico 2026",
        line=dict(color="#ff7f0e", width=2, dash="dash"),
        marker=dict(size=8, symbol="diamond"),
    ))
    fig.update_layout(
        xaxis_title="Fecha", yaxis_title="Tránsitos",
        hovermode="x unified", height=500,
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("📋 Detalle de Predicciones")
    pred_display = pred.copy()
    pred_display["transitos_predichos"] = pred_display["transitos_predichos"].astype(int)
    st.dataframe(pred_display, hide_index=True, use_container_width=True)

    prom_pred = pred["transitos_predichos"].mean()
    max_pred = pred["transitos_predichos"].max()
    min_pred = pred["transitos_predichos"].min()

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.metric("Promedio Predicho", f"{prom_pred:,.0f}")
    with col_b:
        st.metric("Máximo Predicho", f"{max_pred:,.0f}")
    with col_c:
        st.metric("Mínimo Predicho", f"{min_pred:,.0f}")

with tab2:
    st.subheader("Comparativa de Modelos Evaluados")

    if not metricas.empty:
        col1, col2 = st.columns(2)
        with col1:
            fig_mape = px.bar(
                metricas, x="modelo", y="MAPE_cv",
                title="MAPE en Validación Cruzada",
                color="modelo", color_discrete_sequence=px.colors.qualitative.Set2,
            )
            fig_mape.update_layout(height=350, showlegend=False)
            st.plotly_chart(fig_mape, use_container_width=True)
        with col2:
            fig_mae = px.bar(
                metricas, x="modelo", y="MAE_cv",
                title="MAE en Validación Cruzada",
                color="modelo", color_discrete_sequence=px.colors.qualitative.Pastel,
            )
            fig_mae.update_layout(height=350, showlegend=False)
            st.plotly_chart(fig_mae, use_container_width=True)

        st.dataframe(metricas, hide_index=True, use_container_width=True)

    st.subheader("Validación: Reales vs Predichos")
    test = load_predicciones_test()
    if not test.empty:
        fig_test = go.Figure()
        fig_test.add_trace(go.Scatter(
            x=test["fecha"], y=test["transitos_reales"],
            mode="lines+markers", name="Reales", line=dict(color="#1f77b4"),
        ))
        fig_test.add_trace(go.Scatter(
            x=test["fecha"], y=test["transitos_predichos"],
            mode="lines+markers", name="Predichos", line=dict(color="#ff7f0e", dash="dash"),
        ))
        fig_test.update_layout(height=400, hovermode="x unified", title="Hold-out: Reales vs Predichos")
        st.plotly_chart(fig_test, use_container_width=True)

with tab3:
    st.subheader("¿Qué variables impulsan la predicción?")
    features = load_importancia_features()
    if not features.empty:
        fig_imp = px.bar(
            features.sort_values("importancia", ascending=True),
            x="importancia", y="feature", orientation="h",
            title="Importancia de Features",
            color="importancia", color_continuous_scale="Viridis",
        )
        fig_imp.update_layout(height=400)
        st.plotly_chart(fig_imp, use_container_width=True)

        col1, col2 = st.columns(2)
        with col1:
            st.dataframe(features, hide_index=True, use_container_width=True)
        with col2:
            top_feat = features.iloc[0]["feature"]
            top_imp = features.iloc[0]["importancia"]
            st.info(f"**Feature más importante:** {top_feat} ({top_imp:.1%})")

with tab4:
    st.subheader("Visualizaciones del Modelo")
    figuras = [
        ("01_comparativa_modelos.png", "Comparativa de Modelos"),
        ("02_ajuste_test.png", "Ajuste en Hold-out"),
        ("03_importancia_features.png", "Importancia de Features"),
        ("04_pronostico_2026.png", "Pronóstico 2026"),
    ]
    cols = st.columns(2)
    for i, (fname, titulo) in enumerate(figuras):
        with cols[i % 2]:
            path = get_figure_path("persona4_modelo", fname)
            if path.exists():
                st.image(str(path), caption=titulo, use_container_width=True)
            else:
                st.warning(f"No disponible: {fname}")
