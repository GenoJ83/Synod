from app.nlp.summarizer import Summarizer
s = Summarizer()
with open("cleaned_lecture_text.txt", "r") as f:
    long_text = f.read()

print(f"Words in input: {len(long_text.split())}")
try:
    res = s.summarize(long_text, max_length=150)
    print(f"Words in summary: {len(res['summary'].split())}")
    print("\nSUMMARY:\n" + res['summary'])
except Exception as e:
    print("Error:", e)
