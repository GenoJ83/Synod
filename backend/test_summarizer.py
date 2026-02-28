from app.nlp.summarizer import Summarizer
s = Summarizer()
long_text = " ".join(["Sentence one is here. A very long text will follow."] * 100)
print(f"Words in input: {len(long_text.split())}")
res = s.summarize(long_text)
print(f"Words in summary: {len(res['summary'].split())}")
print(res['summary'])
