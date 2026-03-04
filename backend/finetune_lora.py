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
DATA_PATH = "training_data/final_training_set.json"
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
    
    # Load Data
    import json
    with open(DATA_PATH, 'r') as f:
        data = json.load(f)
    
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
