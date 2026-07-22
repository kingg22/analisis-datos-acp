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

met_base = resumen.get("metricas", {}).get("Media_Historica", {})

st.info(
    f"El modelo predice los tránsitos de **cada segmento de mercado** "
    f"({resumen.get('n_segmentos', 10)} segmentos × {resumen.get('n_anios', 6)} años fiscales "
    f"= **{resumen.get('n_observaciones', 60)} observaciones reales** de la ACP); el volumen anual "
    "total es la suma de los segmentos. Validación **Leave-One-Year-Out**: se deja fuera un año "
    "fiscal completo, se entrena con el resto y se predice el año excluido."
)

st.subheader("🏆 Modelo Ganador")
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Modelo", ganador.replace("_", " "))
with col2:
    st.metric(
        "R² (LOYO)", f"{met_ganador.get('R2', 0):+.3f}",
        delta=f"{met_ganador.get('R2', 0) - met_base.get('R2', 0):+.3f} vs baseline",
    )
with col3:
    st.metric(
        "MAE (LOYO)", f"{met_ganador.get('MAE', 0):,.0f}",
        delta=f"-{resumen.get('mejora_vs_baseline_pct', 0):.1f}% vs baseline",
        delta_color="inverse",
    )
with col4:
    st.metric("MAPE (total anual)", f"{met_ganador.get('MAPE_total_anual', 0):.2f}%")

st.caption(
    "ℹ️ El **MAPE se reporta sobre el total anual agregado** porque a nivel de segmento se "
    "distorsiona con denominadores pequeños (p. ej. 'Pasajeros' cayó a 17 tránsitos en FY2021 "
    "por la pandemia). La selección del modelo se hizo por **MAE**, que no sufre ese sesgo."
)

st.divider()

tab1, tab2, tab3, tab4 = st.tabs([
    "🔮 Pronóstico",
    "📊 Comparativa Modelos",
    "🎯 Importancia de Features",
    "🖼️ Figuras del Modelo",
])

with tab1:
    st.subheader("Pronóstico de Tránsitos · FY2026")
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
    st.subheader("Comparativa de Modelos Evaluados (Leave-One-Year-Out)")
    st.caption(
        "**Media histórica** es el baseline sin aprendizaje: predice siempre el promedio. "
        "Que los demás modelos lo superen con holgura es la evidencia de que el modelo "
        "efectivamente aprende de los datos y no solo memoriza un promedio."
    )

    if not metricas.empty:
        col1, col2 = st.columns(2)
        with col1:
            fig_mae = px.bar(
                metricas.sort_values("MAE"), x="modelo", y="MAE",
                title="MAE por modelo — menor es mejor",
                color="modelo", color_discrete_sequence=px.colors.qualitative.Set2,
            )
            fig_mae.update_layout(height=350, showlegend=False)
            st.plotly_chart(fig_mae, use_container_width=True)
        with col2:
            fig_r2 = px.bar(
                metricas.sort_values("R2"), x="modelo", y="R2",
                title="R² por modelo — mayor es mejor",
                color="modelo", color_discrete_sequence=px.colors.qualitative.Pastel,
            )
            fig_r2.add_hline(y=0, line_dash="dot", line_color="grey")
            fig_r2.update_layout(height=350, showlegend=False)
            st.plotly_chart(fig_r2, use_container_width=True)

        st.dataframe(metricas, hide_index=True, use_container_width=True)

    st.subheader("Validación: Reales vs Predichos (LOYO)")
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
            features.sort_values(valor_col, ascending=True).tail(12),
            x=valor_col, y="feature", orientation="h",
            title="Importancia de features del modelo ganador",
            color=valor_col, color_continuous_scale="Viridis",
        )
        fig_imp.update_layout(height=450)
        st.plotly_chart(fig_imp, use_container_width=True)
        st.caption(
            "La identidad del **segmento de mercado** concentra la mayor parte de la "
            "importancia: cada segmento opera en una escala distinta (portacontenedores "
            "≈2,800 tránsitos/año vs. pasajeros ≈200). El régimen de **sequía** y el "
            "**precio del crudo** aportan el ajuste coyuntural."
        )
        st.dataframe(features, hide_index=True, use_container_width=True)
    else:
        st.info("El modelo ganador no expone importancias de features.")

with tab4:
    st.subheader("Visualizaciones del Modelo")
    figuras = [
        ("01_comparativa_modelos.png", "Comparativa de Modelos"),
        ("02_ajuste_loo.png", "Ajuste Leave-One-Year-Out"),
        ("03_importancia_features.png", "Importancia de Features"),
        ("04_pronostico_anual.png", "Pronóstico Anual"),
        ("05_ajuste_por_segmento.png", "Ajuste por Segmento"),
    ]
    cols = st.columns(2)
    for i, (fname, titulo) in enumerate(figuras):
        with cols[i % 2]:
            path = get_figure_path("persona4_modelo", fname)
            if path.exists():
                st.image(str(path), caption=titulo, use_container_width=True)
            else:
                st.warning(f"No disponible: {fname}")
