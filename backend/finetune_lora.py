import os
import torch
from datasets import Dataset
from transformers import (
    AutoModelForSeq2SeqLM, 
    AutoTokenizer, 
    TrainingArguments, 
    Trainer, 
    DataCollatorForSeq2Seq
)
from peft import LoraConfig, get_peft_model, TaskType

# Configuration
MODEL_NAME = "sshleifer/distilbart-cnn-12-6"
RICH_DATA_PATH = "training_data/rich_summarization.json"   # Preferred — built by build_rich_dataset.py
FALLBACK_DATA_PATH = "training_data/final_training_set.json"  # Legacy fallback
OUTPUT_DIR = "trained_models/summarizer_lora"

def train():
    print(f"Loading tokenizer and model: {MODEL_NAME}")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)
    
    # PEFT / LoRA Configuration
    peft_config = LoraConfig(
        task_type=TaskType.SEQ_2_SEQ_LM, 
        inference_mode=False, 
        r=64, 
        lora_alpha=128, 
        lora_dropout=0.05,
        target_modules=["q_proj", "k_proj", "v_proj", "out_proj", "fc1", "fc2"] # Target more linear layers
    )
    
    model = get_peft_model(model, peft_config)
    model.print_trainable_parameters()
    
    # Load Data — prefer the rich dataset, merge with legacy if both exist
    import json

    def _load_json(path):
        with open(path, 'r') as f:
            return json.load(f)

    rich_exists    = os.path.exists(RICH_DATA_PATH)
    legacy_exists  = os.path.exists(FALLBACK_DATA_PATH)

    if rich_exists and legacy_exists:
        print(f"Loading rich dataset + legacy dataset (merged)...")
        rich_data   = _load_json(RICH_DATA_PATH)
        legacy_data = [d for d in _load_json(FALLBACK_DATA_PATH) if len(d.get('summary','').split()) > 8]
        data = rich_data + legacy_data
    elif rich_exists:
        print(f"Loading rich dataset: {RICH_DATA_PATH}")
        data = _load_json(RICH_DATA_PATH)
    elif legacy_exists:
        print(f"Rich dataset not found. Falling back to: {FALLBACK_DATA_PATH}")
        print("  → Run 'python3 build_rich_dataset.py' once to build the rich dataset.")
        data = _load_json(FALLBACK_DATA_PATH)
    else:
        raise FileNotFoundError("No training data found. Run build_rich_dataset.py first.")

    print(f"Total training samples: {len(data)}")
    dataset = Dataset.from_list(data)
    
    def preprocess_function(examples):
        inputs = ["Clean and summarize this noisy lecture/academic text: " + doc for doc in examples["text"]]
        model_inputs = tokenizer(inputs, max_length=512, truncation=True, padding="max_length")
        
        with tokenizer.as_target_tokenizer():
            labels = tokenizer(examples["summary"], max_length=128, truncation=True, padding="max_length")
            
        model_inputs["labels"] = labels["input_ids"]
        return model_inputs

    print("Tokenizing dataset...")
    tokenized_dataset = dataset.map(preprocess_function, batched=True)
    
    # Training Arguments
    training_args = TrainingArguments(
        output_dir=OUTPUT_DIR,
        per_device_train_batch_size=1,
        gradient_accumulation_steps=16,
        learning_rate=2e-4,
        num_train_epochs=15,
        logging_steps=10,
        eval_strategy="no",
        save_strategy="epoch",
        fp16=False, # Mac MPS doesn't support fp16 training well in transformers yet
        push_to_hub=False,
        report_to="none"
    )
    
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_dataset,
        data_collator=DataCollatorForSeq2Seq(tokenizer, model=model)
    )
    
    print("Starting training on MPS...")
    # Transformers Trainer handles device placement automatically
    trainer.train()
    
    # Save the adapter
    model.save_pretrained(os.path.join(OUTPUT_DIR, "final_adapter"))
    print(f"Training complete. Adapter saved to {OUTPUT_DIR}/final_adapter")

if __name__ == "__main__":
    train()
