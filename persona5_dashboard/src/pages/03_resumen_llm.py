"""
Página de Resúmenes con LLM — Canal de Panamá
"""
from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

src_dir = str(Path(__file__).resolve().parent.parent)
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from utils.data_loader import (
    load_insights,
    load_resumen_entrenamiento,
    load_stats_totales,
    load_tendencia_anual,
    load_metricas_modelos,
    load_importancia_features,
    load_predicciones_2026,
    load_ranking_segmentos,
    load_agregado_por_periodo,
)

st.set_page_config(page_title="Resumen LLM — Canal de Panamá", page_icon="🧠", layout="wide")
st.title("🧠 Resúmenes Ejecutivos con IA")
st.caption("Genera reportes ejecutivos automatizados usando Inteligencia Artificial")

st.sidebar.subheader("⚙️ Configuración de IA")
api_provider = st.sidebar.selectbox(
    "Proveedor de LLM",
    ["OpenAI (GPT)", "Anthropic (Claude)", "Sin API (solo datos)"],
)

api_key = ""
if api_provider != "Sin API (solo datos)":
    api_key = st.sidebar.text_input("API Key", type="password")
    if api_key:
        st.sidebar.success("✅ API Key configurada")


def build_context() -> str:
    parts = []

    stats_df = load_stats_totales()
    stats_row = stats_df[stats_df["Unnamed: 0"] == "mean"].iloc[0]
    parts.append(f"## Estadísticas Generales\n- Promedio tránsitos/mes: {stats_row['transitos']:.0f}\n- Peajes promedio: ${stats_row['peajes_usd']:,.0f}\n- Calado promedio: {stats_row['calado_promedio_pies']:.1f} pies")

    insights = load_insights()
    parts.append("## Insights del Análisis\n" + "\n".join(f"- **{i['titulo']}**: {i['detalle']}" for i in insights))

    tendencia = load_tendencia_anual()
    parts.append(f"## Tendencia Anual\n{tendencia.to_string()}")

    ranking = load_ranking_segmentos()
    parts.append(f"## Ranking de Segmentos (Top 5)\n{ranking.head(5)[['segmento','transitos_total','participacion_pct']].to_string()}")

    periodos = load_agregado_por_periodo()
    periodos_agg = periodos.groupby("periodo")["transitos_promedio"].sum().reset_index()
    parts.append(f"## Comparativa de Períodos\n{periodos_agg.to_string()}")

    resumen_ml = load_resumen_entrenamiento()
    best_cv = resumen_ml["cross_validation"].get(resumen_ml["modelo_ganador"], {})
    parts.append(f"## Modelo ML\n- Ganador: {resumen_ml['modelo_ganador']}\n- MAPE CV: {best_cv.get('MAPE_cv', 0):.2f}%")

    pred = load_predicciones_2026()
    parts.append(f"## Predicciones 2026\n{pred[['fecha','transitos_predichos']].to_string(index=False)}")

    features = load_importancia_features()
    parts.append(f"## Importancia Features\n{features.to_string()}")

    return "\n\n".join(parts)


def generate_with_openai(context: str, prompt: str, api_key: str) -> str:
    try:
        import openai
        client = openai.OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Eres un analista de datos experto en logística marítima y el Canal de Panamá. Genera resúmenes ejecutivos claros en español latinoamericano. Usa markdown."},
                {"role": "user", "content": f"{prompt}\n\n---\n\nContexto:\n{context}"},
            ],
            temperature=0.3, max_tokens=1500,
        )
        return response.choices[0].message.content
    except ImportError:
        return "❌ Paquete `openai` no instalado. Ejecuta: `pip install openai`"
    except Exception as e:
        return f"❌ Error con OpenAI: {e}"


def generate_with_claude(context: str, prompt: str, api_key: str) -> str:
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-3-haiku-20240307", max_tokens=1500,
            messages=[{"role": "user", "content": f"Eres analista experto en Canal de Panamá. Genera resumen ejecutivo.\n\n{prompt}\n\n---\n{context}"}],
        )
        return response.content[0].text
    except ImportError:
        return "❌ Paquete `anthropic` no instalado. Ejecuta: `pip install anthropic`"
    except Exception as e:
        return f"❌ Error con Claude: {e}"


def generate_local_summary(context: str, prompt: str) -> str:
    stats_df = load_stats_totales()
    stats_row = stats_df[stats_df["Unnamed: 0"] == "mean"].iloc[0]
    insights = load_insights()
    pred = load_predicciones_2026()
    resumen_ml = load_resumen_entrenamiento()
    best_cv = resumen_ml["cross_validation"].get(resumen_ml["modelo_ganador"], {})

    summary = f"""# 📋 Resumen Ejecutivo — Canal de Panamá
*Generado automáticamente*

---

## 📊 Panorama General

- **Promedio tránsitos/mes:** {int(stats_row['transitos']):,}
- **Peajes promedio:** ${stats_row['peajes_usd']:,.0f}
- **Calado promedio:** {stats_row['calado_promedio_pies']:.1f} pies

---

## 💡 Hallazgos Principales

"""
    for insight in insights:
        summary += f"### {insight['titulo']}\n{insight['detalle']}\n\n"

    summary += f"""---

## 🤖 Modelo Predictivo

- **Modelo ganador:** {resumen_ml['modelo_ganador'].replace('_', ' ')}
- **MAPE (CV):** {best_cv.get('MAPE_cv', 0):.2f}%
- **Muestra entrenamiento:** {resumen_ml.get('n_train', 'N/A')} meses

---

## 🔮 Pronóstico 2026

| Mes | Tránsitos Predichos |
|-----|---------------------|
"""
    for _, row in pred.iterrows():
        fecha = row['fecha']
        mes = fecha.strftime('%B %Y') if hasattr(fecha, 'strftime') else str(fecha)
        summary += f"| {mes} | {int(row['transitos_predichos']):,} |\n"

    summary += """
---

## 📌 Recomendaciones

1. **Monitorear la recuperación** de segmentos afectados por la sequía 2023-2024
2. **Evaluar el impacto** del modelo predictivo en la planificación operativa
3. **Actualizar datos** periódicamente para mejorar la precisión del modelo

---

*Dashboard generado por Persona 5 — Grupo 8*
"""
    return summary


st.subheader("📝 Tipo de Reporte")
plantillas = {
    "Resumen Ejecutivo General": "Genera un resumen ejecutivo general del análisis de datos del Canal de Panamá.",
    "Análisis de Tendencias": "Enfócate en tendencias: estacionalidad, crecimiento, impacto de la sequía y recuperación.",
    "Evaluación del Modelo ML": "Analiza resultados del ML: comparativa, métricas, features y confiabilidad.",
    "Pronóstico 2026": "Presenta el pronóstico 2026: valores predichos, tendencias y riesgos.",
    "Reporte para Dirección": "Reporte de alto nivel: KPIs, impacto financiero y estrategias.",
}

plantilla_seleccionada = st.selectbox("Plantilla", list(plantillas.keys()))
st.text_area("Prompt personalizado", value=plantillas[plantilla_seleccionada], height=100, key="custom_prompt")

st.divider()

if st.button("🚀 Generar Resumen", type="primary", use_container_width=True):
    with st.spinner("Generando resumen ejecutivo..."):
        context = build_context()
        prompt = st.session_state.get("custom_prompt", plantillas[plantilla_seleccionada])

        if api_provider == "OpenAI (GPT)" and api_key:
            result = generate_with_openai(context, prompt, api_key)
        elif api_provider == "Anthropic (Claude)" and api_key:
            result = generate_with_claude(context, prompt, api_key)
        else:
            result = generate_local_summary(context, prompt)

        st.session_state["generated_summary"] = result

if "generated_summary" in st.session_state:
    st.subheader("📄 Resumen Generado")
    st.markdown(st.session_state["generated_summary"])
    st.download_button(
        "📥 Descargar Markdown",
        st.session_state["generated_summary"],
        "resumen_canal_panama.md", "text/markdown",
    )

with st.expander("📊 Ver datos utilizados"):
    tab1, tab2, tab3 = st.tabs(["Stats", "Insights", "Predicciones"])
    with tab1:
        st.dataframe(load_stats_totales(), use_container_width=True)
    with tab2:
        st.json(load_insights())
    with tab3:
        st.dataframe(load_predicciones_2026(), use_container_width=True)
