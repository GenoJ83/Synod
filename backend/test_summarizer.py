from app.nlp.summarizer import Summarizer
s = Summarizer()
with open("cleaned_lecture_text.txt", "r") as f:
    long_text = f.read()

try:
    res = s.summarize(long_text, max_length=150)
    with open("summary_output.txt", "w") as out:
        out.write(f"Input Words: {len(long_text.split())}\n")
        out.write(f"Summary Words: {len(res['summary'].split())}\n")
        out.write("SUMMARY:\n" + res['summary'])
except Exception as e:
    with open("summary_output.txt", "w") as out:
        out.write(str(e))
