from __future__ import annotations

import argparse
import json

from fake_news_xai.inference import FakeNewsPredictor


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Explain a fake news prediction with LIME or SHAP.")
    parser.add_argument("--model_dir", required=True, help="Path to a trained model directory")
    parser.add_argument("--text", required=True, help="Text to analyze")
    parser.add_argument("--method", choices=["lime", "shap"], default="lime")
    parser.add_argument("--top_k", type=int, default=10)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    predictor = FakeNewsPredictor(model_dir=args.model_dir)
    prediction = predictor.predict([args.text])[0]
    explanation = predictor.explain(text=args.text, method=args.method, top_k=args.top_k)

    output = {
        "prediction": prediction,
        "explanation": explanation,
    }
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
