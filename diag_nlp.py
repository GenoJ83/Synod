try:
    from transformers import pipeline
    print("Transformers imported successfully.")
    print("Attempting to load t5-small summarization pipeline...")
    summarizer = pipeline("summarization", model="t5-small")
    print("Pipeline loaded successfully.")
    result = summarizer("This is a test document to verify the summarization pipeline works as expected.", max_length=20, min_length=5)
    print(f"Test Result: {result}")
except Exception as e:
    import traceback
    print("An error occurred:")
    traceback.print_exc()
