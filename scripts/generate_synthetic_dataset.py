from __future__ import annotations

import argparse
import csv
import random
from pathlib import Path


REAL_TEMPLATES = [
    "The {org} announced {policy} after reviewing reports from {place}.",
    "{count} researchers from {org} published a study about {topic} in {place}.",
    "Officials in {place} approved {policy} following a public consultation.",
    "The {org} released updated figures on {topic} for the month of {month}.",
    "A field team in {place} confirmed progress on {topic} with support from {org}.",
]

FAKE_TEMPLATES = [
    "A viral post claims that {topic} can instantly {effect} using {object}.",
    "An anonymous blog says {place} is hiding {object} that will {effect}.",
    "A fabricated report insists that {org} proved {topic} was created by {object}.",
    "Social media users falsely claim {policy} will let citizens {effect} overnight.",
    "A conspiracy article says {object} above {place} can secretly {effect}.",
]

ORGS = [
    "health ministry",
    "transport department",
    "climate research center",
    "education board",
    "city council",
    "agriculture institute",
    "public safety office",
    "national science agency",
]

PLACES = [
    "Delhi",
    "Mumbai",
    "Bengaluru",
    "Hyderabad",
    "Pune",
    "Chennai",
    "Kolkata",
    "Ahmedabad",
]

POLICIES = [
    "a flood relief package",
    "a school scholarship plan",
    "a bus modernization program",
    "a public health campaign",
    "a renewable energy guideline",
    "a crop insurance revision",
]

TOPICS = [
    "air quality",
    "vaccination coverage",
    "crop yields",
    "water conservation",
    "digital literacy",
    "public transport usage",
    "rainfall patterns",
    "waste management",
]

MONTHS = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
]

OBJECTS = [
    "radio towers",
    "silver water",
    "secret satellites",
    "magnetic bracelets",
    "hidden moon crystals",
    "mystery frequency boxes",
]

EFFECTS = [
    "change human DNA",
    "control the weather",
    "make people immortal",
    "erase memory in seconds",
    "cure every disease",
    "levitate heavy vehicles",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a larger synthetic fake news dataset.")
    parser.add_argument("--output", default="data/synthetic_fake_news_large.csv")
    parser.add_argument("--samples_per_class", type=int, default=100)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def build_real_example(rng: random.Random) -> str:
    template = rng.choice(REAL_TEMPLATES)
    return template.format(
        org=rng.choice(ORGS),
        policy=rng.choice(POLICIES),
        place=rng.choice(PLACES),
        count=rng.randint(12, 400),
        topic=rng.choice(TOPICS),
        month=rng.choice(MONTHS),
        object=rng.choice(OBJECTS),
        effect=rng.choice(EFFECTS),
    )


def build_fake_example(rng: random.Random) -> str:
    template = rng.choice(FAKE_TEMPLATES)
    return template.format(
        org=rng.choice(ORGS),
        policy=rng.choice(POLICIES),
        place=rng.choice(PLACES),
        count=rng.randint(12, 400),
        topic=rng.choice(TOPICS),
        month=rng.choice(MONTHS),
        object=rng.choice(OBJECTS),
        effect=rng.choice(EFFECTS),
    )


def main() -> None:
    args = parse_args()
    rng = random.Random(args.seed)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    rows: list[tuple[str, int]] = []
    seen: set[tuple[str, int]] = set()

    while len([row for row in rows if row[1] == 0]) < args.samples_per_class:
        row = (build_real_example(rng), 0)
        if row not in seen:
            rows.append(row)
            seen.add(row)

    while len([row for row in rows if row[1] == 1]) < args.samples_per_class:
        row = (build_fake_example(rng), 1)
        if row not in seen:
            rows.append(row)
            seen.add(row)

    rng.shuffle(rows)

    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["text", "label"])
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {output_path}")


if __name__ == "__main__":
    main()
