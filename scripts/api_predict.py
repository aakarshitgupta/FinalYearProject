from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from fake_news_xai.inference import FakeNewsPredictor
from fake_news_xai.utils import load_json


_PREDICTOR_CACHE: dict[str, FakeNewsPredictor] = {}


def get_predictor(model_dir: str | None) -> FakeNewsPredictor:
    resolved_dir = Path(model_dir or PROJECT_ROOT / "artifacts" / "bert_fake_news_large").resolve()
    cache_key = str(resolved_dir)
    if cache_key not in _PREDICTOR_CACHE:
        _PREDICTOR_CACHE[cache_key] = FakeNewsPredictor(model_dir=resolved_dir)
    return _PREDICTOR_CACHE[cache_key]


def build_config(model_dir: str | None, data_path: str | None) -> dict:
    resolved_model_dir = Path(model_dir or PROJECT_ROOT / "artifacts" / "bert_fake_news_large").resolve()
    resolved_data_path = Path(data_path or PROJECT_ROOT / "data" / "synthetic_fake_news_large.csv").resolve()
    summary_path = resolved_model_dir / "training_summary.json"

    training_summary = load_json(summary_path) if summary_path.exists() else {}
    dataset_preview: list[dict] = []
    total_rows = 0

    if resolved_data_path.exists():
        dataset_df = pd.read_csv(resolved_data_path)
        total_rows = int(len(dataset_df))
        preview_columns = [column for column in ["text", "label"] if column in dataset_df.columns]
        dataset_preview = dataset_df[preview_columns].head(8).to_dict(orient="records")

    return {
        "modelReady": resolved_model_dir.exists(),
        "modelDir": str(resolved_model_dir),
        "trainingSummary": training_summary,
        "dataset": {
            "path": str(resolved_data_path),
            "totalRows": total_rows,
            "preview": dataset_preview,
        },
    }


def analyze(payload: dict) -> dict:
    predictor = get_predictor(payload.get("modelDir"))
    text = str(payload["text"])
    method = payload.get("method", "lime")
    top_k = int(payload.get("topK", 10))

    prediction = predictor.predict([text])[0]
    explanation = predictor.explain(text=text, method=method, top_k=top_k)
    return {
        "prediction": prediction,
        "explanation": explanation,
    }


def batch(payload: dict) -> dict:
    predictor = get_predictor(payload.get("modelDir"))
    texts = [str(item) for item in payload.get("texts", [])]
    predictions = predictor.predict(texts)
    items = [
        {
            "text": text,
            "prediction": prediction,
        }
        for text, prediction in zip(texts, predictions)
    ]
    return {"items": items}


def main() -> None:
    payload = json.loads(sys.stdin.read() or "{}")
    command = payload.get("command", "config")

    if command == "config":
        result = build_config(payload.get("modelDir"), payload.get("dataPath"))
    elif command == "analyze":
        result = analyze(payload)
    elif command == "batch":
        result = batch(payload)
    else:
        raise ValueError(f"Unsupported command: {command}")

    print(json.dumps(result))


if __name__ == "__main__":
    main()
