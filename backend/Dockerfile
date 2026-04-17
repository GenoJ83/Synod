# Use a Python 3.10 base image (needed for newer Spacy versions)
FROM python:3.10-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=7860 \
    HOME=/home/user \
    HF_HOME=/home/user/.cache/huggingface

# Create home directory for the user
RUN useradd -m -u 1000 user
WORKDIR /home/user/app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Pre-download models to speed up Space startup
RUN python3 -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
RUN python3 -m spacy download en_core_web_sm

# Copy the rest of the backend code
COPY --chown=user:user . .

# Ensure data directory exists and is writable
RUN mkdir -p data/uploads && chown -R user:user data

# Switch to the non-root user
USER user

# Expose the port used by Hugging Face Spaces
EXPOSE 7860

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
