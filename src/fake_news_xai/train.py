from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from sklearn.metrics import accuracy_score, f1_score
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    DataCollatorWithPadding,
    Trainer,
    TrainingArguments,
)

from fake_news_xai.data import build_dataset
from fake_news_xai.utils import ensure_dir, save_json


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train a BERT fake news classifier.")
    parser.add_argument("--data_path", required=True, help="Path to CSV dataset")
    parser.add_argument("--model_name", default="bert-base-uncased", help="Hugging Face model name")
    parser.add_argument("--output_dir", default="artifacts/bert_fake_news", help="Directory to save artifacts")
    parser.add_argument("--epochs", type=int, default=2)
    parser.add_argument("--batch_size", type=int, default=8)
    parser.add_argument("--learning_rate", type=float, default=2e-5)
    parser.add_argument("--max_length", type=int, default=256)
    parser.add_argument("--test_size", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_dir = ensure_dir(args.output_dir)

    data_bundle = build_dataset(data_path=args.data_path, test_size=args.test_size, seed=args.seed)
    tokenizer = AutoTokenizer.from_pretrained(args.model_name)

    def tokenize(batch: dict) -> dict:
        return tokenizer(batch["text"], truncation=True, max_length=args.max_length)

    tokenized_dataset = data_bundle.dataset.map(tokenize, batched=True)
    tokenized_dataset = tokenized_dataset.remove_columns(["text"])
    tokenized_dataset.set_format("torch")

    model = AutoModelForSequenceClassification.from_pretrained(args.model_name, num_labels=2)
    data_collator = DataCollatorWithPadding(tokenizer=tokenizer)

    def compute_metrics(eval_pred: tuple[np.ndarray, np.ndarray]) -> dict:
        logits, labels = eval_pred
        predictions = np.argmax(logits, axis=-1)
        return {
            "accuracy": accuracy_score(labels, predictions),
            "f1": f1_score(labels, predictions, average="binary", zero_division=0),
        }

    training_args = TrainingArguments(
        output_dir=str(output_dir),
        eval_strategy="epoch",
        save_strategy="epoch",
        logging_strategy="epoch",
        learning_rate=args.learning_rate,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        num_train_epochs=args.epochs,
        weight_decay=0.01,
        load_best_model_at_end=True,
        metric_for_best_model="f1",
        report_to="none",
        seed=args.seed,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_dataset["train"],
        eval_dataset=tokenized_dataset["test"],
        processing_class=tokenizer,
        data_collator=data_collator,
        compute_metrics=compute_metrics,
    )

    trainer.train()
    metrics = trainer.evaluate()
    trainer.save_model(str(output_dir))
    tokenizer.save_pretrained(str(output_dir))

    summary = {
        "model_name": args.model_name,
        "data_path": str(Path(args.data_path)),
        "label_counts": data_bundle.label_counts,
        "epochs": args.epochs,
        "batch_size": args.batch_size,
        "learning_rate": args.learning_rate,
        "max_length": args.max_length,
        "test_size": args.test_size,
        "seed": args.seed,
        "metrics": {key: float(value) for key, value in metrics.items() if isinstance(value, (int, float))},
    }
    save_json(summary, output_dir / "training_summary.json")

    print("Training complete.")
    print(summary)


if __name__ == "__main__":
    main()
