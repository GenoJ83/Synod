#!/usr/bin/env python3
"""
Model Evaluation Script for Synod Lecture Assistant
Measures accuracy, precision, recall, and F1-score for NLP models
"""

import os
import sys
import json
import time
import numpy as np
from typing import List, Dict, Tuple
from dataclasses import dataclass
from collections import defaultdict

# Add app to path
sys.path.insert(0, os.path.dirname(__file__))

try:
    from rouge_score import rouge_scorer
    from sklearn.metrics import precision_score, recall_score, f1_score, accuracy_score
    from sentence_transformers import SentenceTransformer, util
    HAS_METRICS = True
except ImportError:
    HAS_METRICS = False
    print("Installing required packages...")
    os.system("pip3 install rouge-score scikit-learn")
    from rouge_score import rouge_scorer
    from sklearn.metrics import precision_score, recall_score, f1_score, accuracy_score

from app.nlp.summarizer import Summarizer
from app.nlp.extractor import ConceptExtractor


@dataclass
class EvaluationResult:
    model_name: str
    metric: str
    score: float
    details: Dict


class ModelEvaluator:
    def __init__(self):
        # Use fine-tuned models if they exist, otherwise fallback to defaults
        summarizer_path = "trained_models/summarizer"
        extractor_path = "trained_models/concept_extractor"
        
        sm_model = summarizer_path if os.path.exists(summarizer_path) else "sshleifer/distilbart-cnn-12-6"
        ce_model = extractor_path if os.path.exists(extractor_path) else "all-MiniLM-L6-v2"
        
        self.summarizer = Summarizer(model_name=sm_model)
        self.extractor = ConceptExtractor(model_name=ce_model)
        self.rouge_scorer = rouge_scorer.RougeScorer(['rouge1', 'rouge2', 'rougeL'], use_stemmer=True)
        
    def evaluate_summarizer(self, test_cases: List[Dict]) -> List[EvaluationResult]:
        """
        Evaluate summarization model using ROUGE scores and accuracy metrics.
        """
        print("\n" + "="*60)
        print("EVALUATING SUMMARIZATION MODEL")
        print("="*60)
        
        results = []
        rouge1_scores = []
        rouge2_scores = []
        rougeL_scores = []
        inference_times = []
        
        for i, test_case in enumerate(test_cases, 1):
            text = test_case['text']
            reference_summary = test_case['reference_summary']
            
            # Generate summary
            start_time = time.time()
            summary_result = self.summarizer.summarize(text)
            # The summarize method returns a dict: {"summary": text, "metrics": {...}}
            generated_summary = summary_result.get("summary", "") if isinstance(summary_result, dict) else summary_result
            inference_time = time.time() - start_time
            inference_times.append(inference_time)
            
            # Calculate ROUGE scores
            scores = self.rouge_scorer.score(reference_summary, generated_summary)
            rouge1_scores.append(scores['rouge1'].fmeasure)
            rouge2_scores.append(scores['rouge2'].fmeasure)
            rougeL_scores.append(scores['rougeL'].fmeasure)
            
            print(f"\nTest Case {i}:")
            print(f"  Reference: {reference_summary[:100]}...")
            print(f"  Generated: {generated_summary[:100]}...")
            print(f"  ROUGE-1: {scores['rouge1'].fmeasure:.4f}")
            print(f"  ROUGE-2: {scores['rouge2'].fmeasure:.4f}")
            print(f"  ROUGE-L: {scores['rougeL'].fmeasure:.4f}")
            print(f"  Time: {inference_time:.2f}s")
        
        # Calculate averages
        avg_rouge1 = np.mean(rouge1_scores)
        avg_rouge2 = np.mean(rouge2_scores)
        avg_rougeL = np.mean(rougeL_scores)
        avg_time = np.mean(inference_times)
        
        results.append(EvaluationResult(
            model_name="distilbart-cnn-12-6",
            metric="ROUGE-1",
            score=avg_rouge1,
            details={"scores": rouge1_scores, "avg_time": avg_time}
        ))
        results.append(EvaluationResult(
            model_name="distilbart-cnn-12-6",
            metric="ROUGE-2",
            score=avg_rouge2,
            details={"scores": rouge2_scores}
        ))
        results.append(EvaluationResult(
            model_name="distilbart-cnn-12-6",
            metric="ROUGE-L",
            score=avg_rougeL,
            details={"scores": rougeL_scores}
        ))
        
        print(f"\n{'='*60}")
        print("SUMMARIZATION RESULTS")
        print(f"{'='*60}")
        print(f"Average ROUGE-1: {avg_rouge1:.4f} ({avg_rouge1*100:.2f}%)")
        print(f"Average ROUGE-2: {avg_rouge2:.4f} ({avg_rouge2*100:.2f}%)")
        print(f"Average ROUGE-L: {avg_rougeL:.4f} ({avg_rougeL*100:.2f}%)")
        print(f"Average Inference Time: {avg_time:.2f}s")
        
        return results
    
    def evaluate_concept_extractor(self, test_cases: List[Dict]) -> List[EvaluationResult]:
        """
        Evaluate concept extraction using precision, recall, and F1-score.
        """
        print("\n" + "="*60)
        print("EVALUATING CONCEPT EXTRACTION MODEL")
        print("="*60)
        
        results = []
        precision_scores = []
        recall_scores = []
        f1_scores = []
        inference_times = []
        
        for i, test_case in enumerate(test_cases, 1):
            text = test_case['text']
            expected_concepts = set([c.lower() for c in test_case['expected_concepts']])
            
            # Extract concepts
            start_time = time.time()
            extracted_concepts = self.extractor.extract_concepts(text, top_n=15)
            inference_time = time.time() - start_time
            inference_times.append(inference_time)
            
            # The extractor method returns a list of dicts: [{"term": ..., "relevance": ...}]
            extracted_concepts = set([c.get("term", "").lower() if isinstance(c, dict) else c.lower() for c in extracted_concepts])
            
            # Calculate metrics
            true_positives = len(extracted_concepts & expected_concepts)
            false_positives = len(extracted_concepts - expected_concepts)
            false_negatives = len(expected_concepts - extracted_concepts)
            
            precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
            recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
            f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
            
            precision_scores.append(precision)
            recall_scores.append(recall)
            f1_scores.append(f1)
            
            print(f"\nTest Case {i}:")
            print(f"  Expected: {sorted(expected_concepts)}")
            print(f"  Extracted: {sorted(extracted_concepts)}")
            print(f"  Precision: {precision:.4f}")
            print(f"  Recall: {recall:.4f}")
            print(f"  F1-Score: {f1:.4f}")
            print(f"  Time: {inference_time:.2f}s")
        
        # Calculate averages
        avg_precision = np.mean(precision_scores)
        avg_recall = np.mean(recall_scores)
        avg_f1 = np.mean(f1_scores)
        avg_time = np.mean(inference_times)
        
        results.append(EvaluationResult(
            model_name="all-MiniLM-L6-v2",
            metric="Precision",
            score=avg_precision,
            details={"scores": precision_scores, "avg_time": avg_time}
        ))
        results.append(EvaluationResult(
            model_name="all-MiniLM-L6-v2",
            metric="Recall",
            score=avg_recall,
            details={"scores": recall_scores}
        ))
        results.append(EvaluationResult(
            model_name="all-MiniLM-L6-v2",
            metric="F1-Score",
            score=avg_f1,
            details={"scores": f1_scores}
        ))
        
        print(f"\n{'='*60}")
        print("CONCEPT EXTRACTION RESULTS")
        print(f"{'='*60}")
        print(f"Average Precision: {avg_precision:.4f} ({avg_precision*100:.2f}%)")
        print(f"Average Recall: {avg_recall:.4f} ({avg_recall*100:.2f}%)")
        print(f"Average F1-Score: {avg_f1:.4f} ({avg_f1*100:.2f}%)")
        print(f"Average Inference Time: {avg_time:.2f}s")
        
        return results
    
    def generate_report(self, all_results: List[EvaluationResult], output_file: str = "evaluation_report.json"):
        """
        Generate a comprehensive evaluation report.
        """
        report = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "models": {}
        }
        
        for result in all_results:
            if result.model_name not in report["models"]:
                report["models"][result.model_name] = {}
            report["models"][result.model_name][result.metric] = {
                "score": round(result.score, 4),
                "percentage": round(result.score * 100, 2),
                "details": result.details
            }
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n[OK] Report saved to: {output_file}")
        return report


def get_test_data():
    """
    Provide test cases for evaluation.
    """
    summarization_tests = [
        {
            "text": """
            Machine learning is a subset of artificial intelligence that enables computers to learn and improve 
            from experience without being explicitly programmed. Deep learning is a type of machine learning 
            based on artificial neural networks. Natural language processing allows computers to understand 
            and generate human language. Computer vision enables machines to interpret and analyze visual 
            information from the world. These technologies are transforming industries from healthcare to finance.
            """,
            "reference_summary": "Machine learning and deep learning enable computers to learn from experience. Natural language processing and computer vision allow machines to understand language and visual information."
        },
        {
            "text": """
            Photosynthesis is the process by which plants use sunlight, water, and carbon dioxide to create 
            oxygen and energy in the form of sugar. The process occurs in the chloroplasts, specifically using 
            chlorophyll, the green pigment involved in photosynthesis. Photosynthesis is the primary source 
            of energy for nearly all life on Earth. It is also responsible for the oxygen in the atmosphere.
            """,
            "reference_summary": "Photosynthesis is the process where plants convert sunlight, water, and carbon dioxide into oxygen and sugar energy, occurring in chloroplasts using chlorophyll."
        },
        {
            "text": """
            The water cycle, also known as the hydrologic cycle, describes the continuous movement of water 
            on, above, and below the surface of the Earth. Water changes state between liquid, vapor, and ice 
            at various places in the water cycle. The main processes involved are evaporation, condensation, 
            precipitation, infiltration, runoff, and subsurface flow. The water cycle is essential for all life 
            on Earth and plays a major role in weather and climate patterns.
            """,
            "reference_summary": "The water cycle describes water's continuous movement on Earth, involving evaporation, condensation, precipitation, and other processes as water changes between liquid, vapor, and ice states."
        }
    ]
    
    concept_extraction_tests = [
        {
            "text": """
            Machine learning is a subset of artificial intelligence that enables computers to learn and improve 
            from experience without being explicitly programmed. Deep learning is a type of machine learning 
            based on artificial neural networks. Natural language processing allows computers to understand 
            and generate human language. Computer vision enables machines to interpret and analyze visual 
            information from the world.
            """,
            "expected_concepts": [
                "machine learning",
                "artificial intelligence",
                "deep learning",
                "artificial neural networks",
                "natural language processing",
                "computer vision",
                "human language",
                "visual information"
            ]
        },
        {
            "text": """
            Photosynthesis is the process by which plants use sunlight, water, and carbon dioxide to create 
            oxygen and energy in the form of sugar. The process occurs in the chloroplasts, specifically using 
            chlorophyll, the green pigment involved in photosynthesis.
            """,
            "expected_concepts": [
                "photosynthesis",
                "plants",
                "sunlight",
                "water",
                "carbon dioxide",
                "oxygen",
                "sugar",
                "chloroplasts",
                "chlorophyll"
            ]
        },
        {
            "text": """
            The water cycle involves evaporation, condensation, and precipitation. Water evaporates from oceans 
            and lakes, forms clouds through condensation, and falls as rain or snow through precipitation. 
            This continuous movement is essential for all life on Earth.
            """,
            "expected_concepts": [
                "water cycle",
                "evaporation",
                "condensation",
                "precipitation",
                "oceans",
                "lakes",
                "clouds",
                "rain",
                "snow"
            ]
        }
    ]
    
    return summarization_tests, concept_extraction_tests


def main():
    print("="*60)
    print("SYNOD MODEL EVALUATION")
    print("="*60)
    
    evaluator = ModelEvaluator()
    
    # Get test data
    summarization_tests, concept_extraction_tests = get_test_data()
    
    # Run evaluations
    all_results = []
    
    summarization_results = evaluator.evaluate_summarizer(summarization_tests)
    all_results.extend(summarization_results)
    
    concept_results = evaluator.evaluate_concept_extractor(concept_extraction_tests)
    all_results.extend(concept_results)
    
    # Generate report
    report = evaluator.generate_report(all_results)
    
    # Print summary
    print("\n" + "="*60)
    print("EVALUATION COMPLETE")
    print("="*60)
    print("\nOverall Model Performance:")
    for model_name, metrics in report["models"].items():
        print(f"\n{model_name}:")
        for metric, data in metrics.items():
            print(f"  {metric}: {data['percentage']:.2f}%")
    
    return report


if __name__ == "__main__":
    main()
