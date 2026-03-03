import os
import json
import random
from typing import List, Dict

def generate_noise(text: str) -> str:
    """Injects artificial noise (repetition, OCR errors, artifacts) into clean text."""
    words = text.split()
    if not words: return text
    
    # Repetition
    if random.random() < 0.3:
        idx = random.randint(0, len(words) - 1)
        words.insert(idx, words[idx])
        words.insert(idx, words[idx])
        
    # OCR hyphenation
    if random.random() < 0.3:
        idx = random.randint(0, len(words) - 1)
        if len(words[idx]) > 6:
            mid = len(words[idx]) // 2
            words[idx] = words[idx][:mid] + "- " + words[idx][mid:]
            
    # Institutional junk
    junk = ["Slide 1 of 12", "Back to page", "arXiv:2308.12345v1 [cs.CL]", "P.O. Box 4, Mukono"]
    if random.random() < 0.4:
        words.insert(0, random.choice(junk))
        
    return " ".join(words)

def create_expert_dataset():
    # 1. High Quality Core Samples (Lecture style)
    # These are the "Gold" summaries for various technical topics
    base_samples = [
        {
            "clean_text": "Big Data refers to massive datasets characterized by Volume, Velocity, Variety, and Veracity. Volume describes the sheer scale of information, Velocity the speed of generation, Variety the diverse formats, and Veracity the data quality. These attributes necessitate advanced distributed computing architectures like Hadoop and Spark for effective processing and insights.",
            "summary": "## Summary: Big Data Fundamentals\n* **Definition**: Extremely large datasets exceeding traditional processing limits, defined by the 4Vs: Volume, Velocity, Variety, and Veracity.\n* **Objective**: Leveraging heterogeneous data to support decision-making and drive innovations across domains like health, smart cities, and robotics.\n* **Tools**: Uses frameworks like Hadoop (HDFS/MapReduce) and Spark for scalable, distributed analytics."
        },
        {
            "clean_text": "Data preprocessing is a crucial step to prepare raw data for modeling. It includes cleaning (handling missing values and noise), integration (merging datasets), transformation (normalization and feature engineering), and reduction (dimensionality reduction and sampling). This ensures the dataset is high-quality and computationally efficient for downstream machine learning tasks.",
            "summary": "## Summary: Data Preprocessing\n* **Purpose**: Essential stage to transform raw data into a consistent, robust format suitable for predictive and descriptive modeling.\n* **Key Steps**:\n    1. **Cleaning**: Outlier removal and missing value imputation.\n    2. **Integration**: Standardizing formats and resolving duplicate entities.\n    3. **Transformation**: Normalization and creating engineered features.\n    4. **Reduction**: Optimizing feature sets via dimensionality reduction."
        },
        {
            "clean_text": "Clean code is software that is easy to read and maintain. It avoids technical debt, which is the long-term cost of choosing quick, easy solutions over sustainable architecture. Principles include using meaningful names, creating small and focused functions, and ensuring that the internal structure is understandable for other developers, thus preventing software rot.",
            "summary": "## Summary: Clean Coding Principles\n* **Core Concept**: Prioritizes readability and long-term maintainability over clever or complex implementations.\n* **Technical Debt**: The accumulated burden of quick fixes that eventually makes systems brittle and hard to change (software rot).\n* **Best Practices**: Focus on descriptive naming, function atomicity, and minimal complexity to ensure sustainable development."
        },
        {
            "clean_text": "The Transformer architecture relies on the self-attention mechanism to compute representations of its input and output without using sequence-aligned RNNs or convolution. This allows for significantly more parallelization and has led to state-of-the-art results in tasks like translation and summarization. The model uses multi-head attention to attend to information from different representation subspaces at different positions.",
            "summary": "## Summary: Transformer Architecture\n* **Key Innovation**: Self-attention mechanism that eliminates the need for recurrent or convolutional layers in sequence processing.\n* **Advantages**: Enables high degree of parallelization during training and superior performance on long-range dependencies.\n* **Core Components**: Multi-head attention (attending to multiple subspaces) and positional encodings to maintain sequence order."
        },
        {
            "clean_text": "Neural networks are inspired by the biological brain, consisting of layers of interconnected nodes or neurons. Each connection has a weight that is adjusted during training via backpropagation and gradient descent. Deep learning involves networks with many hidden layers, allowing the model to learn complex hierarchical features from raw data, such as edges in images or semantic patterns in text.",
            "summary": "## Summary: Neural Networks & Deep Learning\n* **Structure**: Composed of input, hidden, and output layers where weights determine the strength of signal transmission between neurons.\n* **Training**: Uses backpropagation to calculate error gradients and gradient descent to iteratively update weights for loss minimization.\n* **Deep Learning**: Specialized subsets using deep architectures to automatically extract high-level features from unstructured datasets."
        },
        {
            "clean_text": "Large Language Models (LLMs) are trained on massive corpora of text to predict the next token in a sequence. Through this objective, they develop emergent capabilities like reasoning, coding, and translation. Fine-tuning techniques like RLHF (Reinforcement Learning from Human Feedback) or PEFT (Parameter-Efficient Fine-Tuning) are used to align these models with human instructions and specialized domains.",
            "summary": "## Summary: Large Language Models (LLMs)\n* **Mechanism**: Statistical prediction models trained on global-scale datasets to master linguistic patterns and logical reasoning.\n* **Emergent Properties**: Capabilities beyond simple text prediction, including multi-step reasoning and complex problem solving.\n* **Alignment**: Processes like RLHF and LoRA (PEFT) ensure models follow specific instructions and maintain safety/utility across technical tasks."
        },
        {
            "clean_text": "Convolutional Neural Networks (CNNs) are the benchmark for computer vision tasks. They use filters to perform convolution operations, capturing spatial hierarchies of features. Pooling layers reduce dimensionality while preserving important spatial information. CNNs are translation-invariant, meaning they can recognize objects regardless of their position in an image, making them ideal for classification and detection.",
            "summary": "## Summary: Convolutional Neural Networks (CNNs)\n* **Application**: Primary architecture for image processing and spatial feature extraction.\n* **Key Layers**: Convolutional layers (feature detection via filters) and Pooling layers (spatial downsampling/reduction).\n* **Properties**: Translation invariance and hierarchical feature learning (from simple edges to complex object parts)."
        }
    ]
    
    # 2. Augment with Noise
    final_data = []
    for sample in base_samples:
        # Add clean pair
        final_data.append({"text": sample["clean_text"], "summary": sample["summary"]})
        # Add noised pair (5 variants per sample)
        for _ in range(5):
            noisy = generate_noise(sample["clean_text"])
            final_data.append({"text": noisy, "summary": sample["summary"]})
            
    # 3. Save to backend/training_data/expert_augmented.json
    output_path = "training_data/expert_augmented.json"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(final_data, f, indent=2)
        
    print(f"Generated {len(final_data)} high-quality training pairs.")

if __name__ == "__main__":
    create_expert_dataset()
