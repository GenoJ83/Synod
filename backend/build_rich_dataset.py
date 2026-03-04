#!/usr/bin/env python3
"""
Rich Dataset Builder for Synod Lecture Assistant
Downloads and preprocesses high-quality datasets from HuggingFace to improve model performance.

Datasets used:
  Summarization:
    - xsum       : BBC news, ~225k pairs (short, abstractive - good for lecture summaries)
    - billsum    : US bill text + summaries (educational/technical domain)
    - cnn_dailymail: Long newspaper articles with bullet-style highlights

  Concept Extraction:
    - midas/inspec : Academic keyphrases from scientific abstracts
"""

import json
import os
import re

OUTPUT_DIR = "training_data"
SUMMATION_LIMIT = 500   # Max samples per dataset (keep training time reasonable on CPU/MPS)
CONCEPT_LIMIT = 800     # Max concept samples


def clean_text(text: str) -> str:
    """Remove common PDF/slide artefacts before storing."""
    text = re.sub(r"\b(Back to page|Slide \d+ of \d+|arXiv:\S+)\b", "", text)
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip()


def build_summarization_dataset() -> list:
    from datasets import load_dataset

    pairs = []

    # --- 1. XSum (BBC: short abstractive summaries, ~1 sentence) ---
    print(f"[xsum] Loading {SUMMATION_LIMIT} samples...")
    try:
        ds = load_dataset("EdinburghNLP/xsum", split=f"train[:{SUMMATION_LIMIT}]")
        for item in ds:
            text = clean_text(item["document"])
            summary = item["summary"].strip()
            if len(text.split()) > 30 and len(summary.split()) > 5:
                pairs.append({"text": text[:1200], "summary": summary})
        print(f"[xsum] Added {len(pairs)} pairs.")
    except Exception as e:
        print(f"[xsum] Failed: {e}")

    # --- 2. BillSum (US legislation: formal, educational, domain-specific) ---
    print(f"[billsum] Loading {SUMMATION_LIMIT} samples...")
    before = len(pairs)
    try:
        ds = load_dataset("billsum", split=f"train[:{SUMMATION_LIMIT}]")
        for item in ds:
            text = clean_text(item["text"])
            summary = item["summary"].strip()
            if len(text.split()) > 40 and len(summary.split()) > 10:
                pairs.append({"text": text[:1200], "summary": summary[:300]})
        print(f"[billsum] Added {len(pairs)-before} pairs.")
    except Exception as e:
        print(f"[billsum] Failed: {e}")

    # --- 3. CNN / DailyMail (news with bullet-point highlights) ---
    print(f"[cnn_dailymail] Loading {SUMMATION_LIMIT} samples...")
    before = len(pairs)
    try:
        ds = load_dataset("abisee/cnn_dailymail", "3.0.0", split=f"train[:{SUMMATION_LIMIT}]")
        for item in ds:
            text = clean_text(item["article"])
            # Highlights are newline-separated bullet points — join them
            summary = " ".join(item["highlights"].split("\n")).strip()
            if len(text.split()) > 40 and len(summary.split()) > 5:
                pairs.append({"text": text[:1200], "summary": summary[:300]})
        print(f"[cnn_dailymail] Added {len(pairs)-before} pairs.")
    except Exception as e:
        print(f"[cnn_dailymail] Failed: {e}")

    # --- 4. Keep existing local fine-tuning data (domain-specific lecture content) ---
    for local_file in ["training_data/final_training_set.json", "training_data/expert_augmented.json"]:
        if os.path.exists(local_file):
            with open(local_file) as f:
                local_data = json.load(f)
            # Only keep pairs with a meaningful summary (not just a header like "Hadoop" or "Use Cases:")
            filtered = [d for d in local_data if d.get("summary") and len(d["summary"].split()) > 8]
            pairs.extend(filtered)
            print(f"[local] Added {len(filtered)} pairs from {local_file}")

    print(f"\nTotal summarization pairs: {len(pairs)}")
    return pairs


def build_concept_dataset() -> list:
    from datasets import load_dataset

    samples = []

    # --- 1. midas/inspec (scientific keyphrases from engineering/CS abstracts) ---
    print(f"[midas/inspec] Loading {CONCEPT_LIMIT} samples...")
    try:
        ds = load_dataset("midas/inspec", "raw", split=f"train[:{CONCEPT_LIMIT}]")
        positives = []
        for item in ds:
            text = " ".join(item["document"]) if isinstance(item["document"], list) else item["document"]
            text = text[:600]
            phrases = list(set(
                item.get("unassigned_keyphrases", []) + item.get("assigned_keyphrases", [])
            ))
            for phrase in phrases[:4]:
                positives.append({"text": text, "concept": phrase.lower(), "label": 1.0})

        # Build an equal number of negatives (concept from a random other document)
        import random
        all_phrases = [s["concept"] for s in positives]
        all_texts   = [s["text"]    for s in positives]
        negatives = []
        for _ in range(len(positives)):
            text    = random.choice(all_texts)
            concept = random.choice(all_phrases)
            # Ensure it's actually negative
            if concept.lower() not in text.lower():
                negatives.append({"text": text, "concept": concept, "label": 0.0})

        samples = positives + negatives
        random.shuffle(samples)
        print(f"[midas/inspec] Added {len(positives)} positive + {len(negatives)} negative concept samples.")
    except Exception as e:
        print(f"[midas/inspec] Failed: {e}")

    # --- 2. Merge existing local concept data ---
    local_concept = "training_data/concepts_augmented.json"
    if os.path.exists(local_concept):
        with open(local_concept) as f:
            local_data = json.load(f)
        samples.extend(local_data)
        print(f"[local] Added {len(local_data)} concept pairs from {local_concept}")

    print(f"\nTotal concept samples: {len(samples)}")
    return samples


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("=" * 60)
    print("PHASE 1: Building Summarization Dataset")
    print("=" * 60)
    sum_data = build_summarization_dataset()
    out_path = os.path.join(OUTPUT_DIR, "rich_summarization.json")
    with open(out_path, "w") as f:
        json.dump(sum_data, f, indent=2)
    print(f"\n✓ Saved {len(sum_data)} summarization pairs → {out_path}")

    print("\n" + "=" * 60)
    print("PHASE 2: Building Concept Extraction Dataset")
    print("=" * 60)
    concept_data = build_concept_dataset()
    out_path = os.path.join(OUTPUT_DIR, "rich_concepts.json")
    with open(out_path, "w") as f:
        json.dump(concept_data, f, indent=2)
    print(f"\n✓ Saved {len(concept_data)} concept samples → {out_path}")

    print("\n✅ Dataset build complete. Run finetune_lora.py to start training.")


if __name__ == "__main__":
    main()
