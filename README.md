# UCU Conclave: Intelligent Lecture and Course Content Assistant

## Project Overview
**UCU Conclave** is an advanced NLP-based assistant designed to streamline the analysis of university lecture materials. The system helps both lecturers and students by automatically extracting key concepts, generating concise summaries, and producing high-quality revision questions from slides and documents.

## Group Details
- **Group Members:** Geno Joshua, Mokili Promise Pierre, Pouch Mabor Makuei, Calvin Diego
- **Course:** Natural Language Processing and Text Analytics
- **Project Duration:** 8 Weeks (Starting Feb 10, 2026)

## Key Features
- **Multi-format Ingestion:** Supports PDF, PPTX, and Plain Text.
- **Concept Extraction & Ranking:** Identifies and ranks the most important topics using S-BERT and TextRank.
- **Automated Summarization:** Generates abstractive summaries using state-of-the-art transformer models (T5/BART).
- **Quiz Generation:** Creates Multiple Choice and Fill-in-the-blank questions for revision.
- **Importance Explanations:** Provides insights into why certain content is highlighted using attention mechanisms.
- **Interactive Web App:** Deployed via Streamlit for a user-friendly experience.

## Project Structure
```
├── app/                  # Main application source code
│   ├── ingestion/        # File parsing modules (PDF, PPTX)
│   ├── processing/       # Text normalization and cleaning
│   ├── nlp/              # Core NLP models and logic
│   └── ui/               # Streamlit interface components
├── data/                 # Sample datasets and lecture materials
├── models/               # Fine-tuning scripts and model configurations
├── tests/                # Automated verification tests
├── main.py               # Streamlit entry point
├── requirements.txt      # Project dependencies
└── README.md             # Project documentation
```

## Getting Started

### Prerequisites
- Python 3.8+
- [Optional] GPU for faster model inference

### Installation
1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd "Lecture Assistant"
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Running the App
```bash
streamlit run main.py
```

## Implementation Pipeline
1. **Data Ingestion:** Text extraction using PyMuPDF and python-pptx.
2. **Preprocessing:** Sentence segmentation and noise removal with NLTK/spaCy.
3. **NLP Pipeline:** 
   - Feature extraction using Transformers.
   - Ranking via TF-IDF/TextRank.
   - Summarization and QG via Seq2Seq models.
4. **Evaluation:** Quantitative metrics (ROUGE) and human evaluation.

## License
MIT License
