"""Convert the source question file (.docx) into questions.json and embed them in index.html.
Usage: python build_questions.py [source.docx]   (needs pandoc)"""
import json, re, subprocess, sys

src = sys.argv[1] if len(sys.argv) > 1 else "source_questions.docx"
text = subprocess.run(["pandoc", src, "-t", "plain", "--wrap=none"],
                      capture_output=True, text=True, check=True).stdout
text = re.sub(r"Alternate version of Question \d+:.*?(?=\n\s*Question \d+\s*\n|\Z)", "", text, flags=re.S)

WORDS = {"two": 2, "three": 3, "four": 4}
blocks = re.split(r"\n\s*Question (\d+)\s*\n", "\n" + text)
questions, seen = [], {}
for i in range(1, len(blocks), 2):
    src_no, body = int(blocks[i]), blocks[i + 1]
    body = re.sub(r"\n\s*Part \d+:.*", "", body)
    stem = re.search(r"Question:\s*(.+)", body).group(1).strip()
    pre, rest = body.split("Options:", 1)
    steps = [re.sub(r"^\s*(?:\d+\.|[-•*])\s*", "", l).strip() for l in pre.splitlines()[1:] if l.strip() and not l.startswith("Question:")]
    opts = [{"id": m.group(1), "text": m.group(2).strip()}
            for m in (re.match(r"^\W*([A-E])\.\s+(.*)", l) for l in rest.splitlines()) if m]
    ans = re.search(r"Answer:\s*([A-E](?:\s*(?:and|,)\s*[A-E])*)", rest).group(1)
    answer = re.findall(r"[A-E]", ans)
    sel = re.search(r"\(Select (\w+)\.\)", stem)
    q = {"src": src_no, "stem": re.sub(r"\s*\(Select \w+\.\)", "", stem), "steps": steps,
         "options": opts, "answer": answer, "select": WORDS[sel.group(1)] if sel else 1,
         "type": "ordering" if steps else ("multi" if sel else "single")}
    key = json.dumps([q["stem"], steps, opts])
    if key in seen:
        print(f"Skipped Q{src_no}: duplicate of Q{seen[key]}"); continue
    seen[key] = src_no
    assert len(answer) == q["select"], (src_no, answer)
    questions.append(q)

for n, q in enumerate(questions, 1): q["id"] = n
json.dump(questions, open("questions.json", "w"), indent=1, ensure_ascii=False)
html = open("index.html", encoding="utf-8").read()
block = "<!--QDATA--><script>window.QUESTIONS = " + json.dumps(questions, ensure_ascii=False).replace("</", "<\\/") + ";</script><!--/QDATA-->"
html = re.sub(r"<!--QDATA-->.*?<!--/QDATA-->", lambda m: block, html, flags=re.S)
open("index.html", "w", encoding="utf-8").write(html)
from collections import Counter
print(len(questions), "questions", dict(Counter(q["type"] for q in questions)))
