import os
import re
import json
import time
from typing import List, Dict
from app.nlp.summarizer import Summarizer

def get_rouge_simple(pred: str, target: str):
    """Simple word-overlap ROUGE-1 approximation for quick diagnosis."""
    if not pred or not target:
        return 0.0
    p_words = set(re.findall(r'\w+', pred.lower()))
    t_words = set(re.findall(r'\w+', target.lower()))
    if not t_words:
        return 0.0
    overlap = len(p_words.intersection(t_words))
    return overlap / len(t_words)

def diagnose():
    summarizer = Summarizer()
    
    # Sample Case 1: Big Data Lecture (Noisy)
    # This imitates the raw noise seen in lecture_text.txt
    noisy_sample = """
    A Complete Education for A Complete Person
    P.O. Box 4, Mukono, Uganda, Plot 67-173, Bishop Tucker Road, Mukono Hill | Tel: +256 (0) 312 350 800 Email: info@ucu.ac.ug Web: https://ucu.ac.ug
    Founded by the Province of the Church of Uganda. Chartered by the Government of Uganda
    Topic: Fundamentals of Big Data
    Dr. Daphne Nyachaki Bitalo
    Department of Computing & Technology
    Introduction to Big Data
    ●Big Data can bring “big values” to our life in almost every aspect.
    ●Technologically, Big Data is bringing about changes in our lives because it allows diverse and heterogeneous data to be fully integrated and analyzed to help us make decisions.
    ●Today, with the Big Data technology, thousands of data from seemingly unrelated areas can help support important decisions. This is the power of Big Data.
    Volume: The sheer amount of data generated is massive.
    Velocity: Data is generated at a high speed, often in real-time.
    Variety: Data comes in various formats, including structured and unstructured data.
    Veracity: Quality and robustness of data
    Back to the page. Back to Mail Online. Slide 1.
    """
    
    target_summary = "Big Data leverages massive, high-speed, and diverse datasets (Volume, Velocity, Variety, Veracity) to provide deep insights and support informed decision-making across various domains."

    print("--- Running Diagnosis ---")
    start_time = time.time()
    result = summarizer.summarize(noisy_sample)
    duration = time.time() - start_time
    
    summary_text = result["summary"]
    rouge_score = get_rouge_simple(summary_text, target_summary)
    
    noise_patterns = [
        r"Mukono", r"P\.O\. Box", r"Uganda", r"Back to", r"Slide \d+", r"Tel:"
    ]
    noise_count = sum(1 for p in noise_patterns if re.search(p, summary_text, re.IGNORECASE))
    
    report = {
        "input_len": len(noisy_sample.split()),
        "output_len": len(summary_text.split()),
        "duration": duration,
        "summary": summary_text,
        "metrics": {
            "approx_rouge_1": round(rouge_score, 3),
            "residual_noise_markers": noise_count
        }
    }
    
    print(json.dumps(report, indent=2))
    
    # Log failure points
    issues = []
    if noise_count > 0:
        issues.append("Still contains institutional noise (headers/footers)")
    if "big data" not in summary_text.lower():
        issues.append("Missing core subject matter")
    if len(summary_text.split()) < 30:
        issues.append("Output is too short/skimming")
        
    print("\nIdentified Issues:")
    for issue in issues:
        print(f" - {issue}")

if __name__ == "__main__":
    diagnose()
