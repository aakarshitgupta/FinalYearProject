from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import shap
import torch
from lime.lime_text import LimeTextExplainer
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from fake_news_xai.utils import LABEL_NAMES, load_json


class FakeNewsPredictor:
    def __init__(self, model_dir: str | Path) -> None:
        self.model_dir = Path(model_dir)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_dir)
        self.model = AutoModelForSequenceClassification.from_pretrained(self.model_dir).to(self.device)
        self.model.eval()
        self.training_summary = load_json(self.model_dir / "training_summary.json")
        self.class_names = [LABEL_NAMES[0], LABEL_NAMES[1]]
        mpl_dir = self.model_dir.parent / ".mplconfig"
        mpl_dir.mkdir(parents=True, exist_ok=True)
        os.environ.setdefault("MPLCONFIGDIR", str(mpl_dir))

    @staticmethod
    def _normalize_texts(texts: str | list[str] | np.ndarray) -> list[str]:
        if isinstance(texts, str):
            return [texts]
        normalized: list[str] = []
        for item in texts:
            if isinstance(item, str):
                normalized.append(item)
            elif isinstance(item, (list, tuple, np.ndarray)):
                normalized.append(" ".join(str(part) for part in item))
            else:
                normalized.append(str(item))
        return normalized

    def predict_proba(self, texts: list[str]) -> np.ndarray:
        texts = self._normalize_texts(texts)
        encoded = self.tokenizer(
            texts,
            padding=True,
            truncation=True,
            max_length=int(self.training_summary["max_length"]),
            return_tensors="pt",
        )
        encoded = {key: value.to(self.device) for key, value in encoded.items()}

        with torch.no_grad():
            logits = self.model(**encoded).logits
            probabilities = torch.softmax(logits, dim=-1).cpu().numpy()
        return probabilities

    def predict(self, texts: list[str]) -> list[dict]:
        probabilities = self.predict_proba(texts)
        outputs = []
        for probs in probabilities:
            label_idx = int(np.argmax(probs))
            outputs.append(
                {
                    "label": label_idx,
                    "label_name": LABEL_NAMES[label_idx],
                    "confidence": float(probs[label_idx]),
                    "probabilities": {
                        LABEL_NAMES[i]: float(prob) for i, prob in enumerate(probs)
                    },
                }
            )
        return outputs

    def explain(self, text: str, method: str = "lime", top_k: int = 10) -> list[dict]:
        if method == "lime":
            return self._explain_with_lime(text=text, top_k=top_k)
        if method == "shap":
            return self._explain_with_shap(text=text, top_k=top_k)
        raise ValueError("method must be either 'lime' or 'shap'")

    def _explain_with_lime(self, text: str, top_k: int) -> list[dict]:
        explainer = LimeTextExplainer(class_names=self.class_names)
        explanation = explainer.explain_instance(
            text_instance=text,
            classifier_fn=self.predict_proba,
            num_features=top_k,
            num_samples=128,
        )
        predicted_label = self.predict([text])[0]["label"]
        label_to_use = predicted_label if predicted_label in explanation.local_exp else next(iter(explanation.local_exp))
        return [
            {"feature": feature, "importance": float(weight), "method": "lime"}
            for feature, weight in explanation.as_list(label=label_to_use)
        ]

    def _explain_with_shap(self, text: str, top_k: int) -> list[dict]:
        masker = shap.maskers.Text(self.tokenizer)
        explainer = shap.Explainer(self.predict_proba, masker, output_names=self.class_names)
        shap_values = explainer([text])
        predicted_label = self.predict([text])[0]["label"]

        tokens = list(shap_values.data[0])
        importances = shap_values.values[0, :, predicted_label]
        rows = [
            {"feature": token, "importance": float(score), "method": "shap"}
            for token, score in zip(tokens, importances)
            if str(token).strip()
        ]
        rows.sort(key=lambda item: abs(item["importance"]), reverse=True)
        return rows[:top_k]
