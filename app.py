from __future__ import annotations

from pathlib import Path
import sys

import altair as alt
import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from fake_news_xai.inference import FakeNewsPredictor
from fake_news_xai.utils import load_json


st.set_page_config(
    page_title="Fake News XAI Studio",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_resource(show_spinner=False)
def load_predictor(model_dir: str) -> FakeNewsPredictor:
    return FakeNewsPredictor(model_dir=model_dir)


@st.cache_data(show_spinner=False)
def load_training_summary(model_dir: str) -> dict:
    summary_path = Path(model_dir) / "training_summary.json"
    if not summary_path.exists():
        return {}
    return load_json(summary_path)


@st.cache_data(show_spinner=False)
def load_dataset_preview(data_path: str) -> pd.DataFrame:
    csv_path = Path(data_path)
    if not csv_path.exists():
        return pd.DataFrame()
    return pd.read_csv(csv_path)


def make_probability_frame(prediction: dict) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"label": label.title(), "probability": probability}
            for label, probability in prediction["probabilities"].items()
        ]
    )


def make_explanation_chart(explanation_df: pd.DataFrame, method: str) -> alt.Chart:
    chart_data = explanation_df.copy()
    chart_data["direction"] = chart_data["importance"].apply(
        lambda value: "Supports fake" if value >= 0 else "Supports real"
    )
    chart_data["importance_abs"] = chart_data["importance"].abs()

    return (
        alt.Chart(chart_data)
        .mark_bar(cornerRadiusEnd=6)
        .encode(
            x=alt.X("importance:Q", title=f"{method.upper()} importance"),
            y=alt.Y("feature:N", sort="-x", title="Token / phrase"),
            color=alt.Color(
                "direction:N",
                scale=alt.Scale(domain=["Supports fake", "Supports real"], range=["#b91c1c", "#0f766e"]),
                legend=alt.Legend(title="Contribution"),
            ),
            tooltip=[
                alt.Tooltip("feature:N", title="Feature"),
                alt.Tooltip("importance:Q", title="Importance", format=".4f"),
                alt.Tooltip("direction:N", title="Direction"),
            ],
        )
        .properties(height=max(260, len(chart_data) * 28))
    )


def make_probability_chart(probability_df: pd.DataFrame) -> alt.Chart:
    return (
        alt.Chart(probability_df)
        .mark_arc(innerRadius=55, outerRadius=95)
        .encode(
            theta=alt.Theta("probability:Q"),
            color=alt.Color(
                "label:N",
                scale=alt.Scale(domain=["Fake", "Real"], range=["#ef4444", "#10b981"]),
                legend=alt.Legend(title="Class"),
            ),
            tooltip=[
                alt.Tooltip("label:N", title="Class"),
                alt.Tooltip("probability:Q", title="Probability", format=".2%"),
            ],
        )
    )


def render_prediction_card(prediction: dict) -> None:
    label = prediction["label_name"].title()
    confidence = prediction["confidence"]
    verdict_color = "#b91c1c" if prediction["label_name"] == "fake" else "#0f766e"
    st.markdown(
        f"""
        <div style="padding: 1.2rem 1.25rem; border-radius: 18px; background: linear-gradient(135deg, {verdict_color}12, #ffffff); border: 1px solid {verdict_color}33;">
            <div style="font-size: 0.9rem; color: #475569; margin-bottom: 0.35rem;">Predicted verdict</div>
            <div style="font-size: 2rem; font-weight: 700; color: {verdict_color};">{label}</div>
            <div style="font-size: 1rem; color: #334155;">Confidence: {confidence:.2%}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_overview(training_summary: dict, dataset_df: pd.DataFrame, model_dir: Path) -> None:
    st.markdown("## Project overview")
    overview_left, overview_mid, overview_right = st.columns(3)

    metrics = training_summary.get("metrics", {})
    overview_left.metric("Model directory", model_dir.name if model_dir.exists() else "Missing")
    overview_mid.metric("Eval accuracy", f"{metrics.get('eval_accuracy', 0):.2%}" if metrics else "N/A")
    overview_right.metric("Eval F1", f"{metrics.get('eval_f1', 0):.2%}" if metrics else "N/A")

    info_col, data_col = st.columns([1.2, 1])
    with info_col:
        st.markdown(
            """
            This app turns the project into an interactive explainability studio:

            - classify a single article or claim
            - inspect class probabilities and explanation weights
            - upload a CSV for batch screening
            - review dataset balance and training settings
            """
        )
        if training_summary:
            st.json(
                {
                    "model_name": training_summary.get("model_name"),
                    "epochs": training_summary.get("epochs"),
                    "batch_size": training_summary.get("batch_size"),
                    "max_length": training_summary.get("max_length"),
                }
            )
        else:
            st.info("No training summary found yet. Train the model to unlock live inference.")

    with data_col:
        st.markdown("### Dataset snapshot")
        if dataset_df.empty:
            st.warning("Dataset preview unavailable.")
        elif "label" not in dataset_df.columns:
            st.info("Dataset loaded, but no `label` column was found for balance visualization.")
        else:
            label_counts = dataset_df["label"].value_counts().rename(index={0: "Real", 1: "Fake"}).reset_index()
            label_counts.columns = ["label", "count"]
            st.altair_chart(
                alt.Chart(label_counts)
                .mark_bar(cornerRadiusTopLeft=8, cornerRadiusTopRight=8)
                .encode(
                    x=alt.X("label:N", title="Label"),
                    y=alt.Y("count:Q", title="Samples"),
                    color=alt.Color(
                        "label:N",
                        scale=alt.Scale(domain=["Fake", "Real"], range=["#ef4444", "#10b981"]),
                        legend=None,
                    ),
                    tooltip=["label", "count"],
                )
                .properties(height=260),
                use_container_width=True,
            )


def render_single_analysis(predictor: FakeNewsPredictor, method: str) -> None:
    st.markdown("## Single article analysis")
    sample_text = (
        "A viral post claims that scientists discovered a secret cure hidden from the public for years."
    )
    text = st.text_area(
        "Paste a headline, article excerpt, or social media claim",
        value=sample_text,
        height=220,
    )
    top_k = st.slider("Top explanation features", min_value=5, max_value=20, value=10)

    if st.button("Analyze text", type="primary", use_container_width=True):
        if not text.strip():
            st.warning("Enter some text before running analysis.")
            return

        with st.spinner("Running fake news detection and explanation..."):
            prediction = predictor.predict([text])[0]
            explanation = predictor.explain(text=text, method=method, top_k=top_k)

        explanation_df = pd.DataFrame(explanation)
        probability_df = make_probability_frame(prediction)

        result_col, chart_col = st.columns([0.9, 1.1])
        with result_col:
            render_prediction_card(prediction)
            st.markdown("### Probability split")
            st.altair_chart(make_probability_chart(probability_df), use_container_width=True)
            st.dataframe(
                probability_df.assign(
                    probability=probability_df["probability"].map(lambda value: f"{value:.2%}")
                ),
                use_container_width=True,
                hide_index=True,
            )

        with chart_col:
            st.markdown(f"### {method.upper()} explanation")
            if explanation_df.empty:
                st.warning("No explanation features were returned for this prediction.")
            else:
                st.altair_chart(make_explanation_chart(explanation_df, method), use_container_width=True)
                st.dataframe(explanation_df, use_container_width=True, hide_index=True)


def render_batch_analysis(predictor: FakeNewsPredictor) -> None:
    st.markdown("## Batch screening")
    uploaded_file = st.file_uploader(
        "Upload a CSV with a `text` column to score multiple rows",
        type=["csv"],
    )

    if uploaded_file is None:
        st.caption("Tip: upload a newsroom export or manually prepared CSV to screen multiple claims at once.")
        return

    batch_df = pd.read_csv(uploaded_file)
    if "text" not in batch_df.columns:
        st.error("The uploaded CSV must include a `text` column.")
        return

    run_batch = st.button("Run batch analysis", use_container_width=True)
    if not run_batch:
        st.dataframe(batch_df.head(10), use_container_width=True)
        return

    texts = batch_df["text"].fillna("").astype(str).tolist()
    with st.spinner(f"Scoring {len(texts)} records..."):
        predictions = predictor.predict(texts)

    results_df = batch_df.copy()
    results_df["predicted_label"] = [row["label_name"] for row in predictions]
    results_df["confidence"] = [row["confidence"] for row in predictions]
    results_df["real_probability"] = [row["probabilities"]["real"] for row in predictions]
    results_df["fake_probability"] = [row["probabilities"]["fake"] for row in predictions]

    summary_col, table_col = st.columns([0.8, 1.2])
    with summary_col:
        label_summary = (
            results_df["predicted_label"]
            .value_counts()
            .rename_axis("label")
            .reset_index(name="count")
        )
        st.altair_chart(
            alt.Chart(label_summary)
            .mark_bar(cornerRadiusTopLeft=8, cornerRadiusTopRight=8)
            .encode(
                x=alt.X("label:N", title="Predicted label"),
                y=alt.Y("count:Q", title="Rows"),
                color=alt.Color(
                    "label:N",
                    scale=alt.Scale(domain=["fake", "real"], range=["#ef4444", "#10b981"]),
                    legend=None,
                ),
                tooltip=["label", "count"],
            )
            .properties(height=280),
            use_container_width=True,
        )
        st.metric("Average fake probability", f"{results_df['fake_probability'].mean():.2%}")

    with table_col:
        st.dataframe(results_df, use_container_width=True)
        st.download_button(
            "Download results CSV",
            data=results_df.to_csv(index=False).encode("utf-8"),
            file_name="fake_news_screening_results.csv",
            mime="text/csv",
            use_container_width=True,
        )


def main() -> None:
    st.title("Fake News XAI Studio")
    st.caption("Explainable fake news detection with Transformer inference, LIME, and SHAP")

    default_model_dir = PROJECT_ROOT / "artifacts" / "bert_fake_news"
    default_data_path = PROJECT_ROOT / "data" / "sample_fake_news.csv"

    st.sidebar.header("Workspace")
    model_dir = Path(st.sidebar.text_input("Model directory", str(default_model_dir)))
    data_path = Path(st.sidebar.text_input("Dataset path", str(default_data_path)))
    method = st.sidebar.selectbox("Explanation method", ["lime", "shap"], index=0)
    st.sidebar.markdown("---")
    st.sidebar.write("Recommended for demos:")
    st.sidebar.write("- `lime` for faster CPU explanations")
    st.sidebar.write("- `shap` for deeper but slower token-level analysis")

    training_summary = load_training_summary(str(model_dir))
    dataset_df = load_dataset_preview(str(data_path))

    hero_left, hero_right = st.columns([1.35, 1])
    with hero_left:
        st.markdown(
            """
            This web app helps present the final-year project as a complete applied AI system,
            not just a notebook or command-line pipeline. It combines model inference, explainability,
            and batch review in one place for demonstrations and evaluation.
            """
        )
    with hero_right:
        ready = model_dir.exists() and (model_dir / "training_summary.json").exists()
        status_label = "Ready" if ready else "Model artifacts missing"
        st.info(f"System status: {status_label}")

    render_overview(training_summary, dataset_df, model_dir)

    if not model_dir.exists():
        st.error(
            f"Model directory not found at `{model_dir}`. Train the model first, then refresh the app."
        )
        st.code(
            "python -m fake_news_xai.train --data_path data\\sample_fake_news.csv --output_dir artifacts\\bert_fake_news",
            language="powershell",
        )
        return

    try:
        predictor = load_predictor(str(model_dir))
    except Exception as exc:
        st.error(f"Unable to load the model from `{model_dir}`.")
        st.exception(exc)
        return

    render_single_analysis(predictor, method)
    render_batch_analysis(predictor)

    if not dataset_df.empty:
        st.markdown("## Dataset preview")
        preview_columns = [column for column in ["text", "label"] if column in dataset_df.columns]
        st.dataframe(dataset_df[preview_columns].head(12), use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()
