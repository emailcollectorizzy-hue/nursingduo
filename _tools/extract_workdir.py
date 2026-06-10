"""Reconstruct a _build.py work dir from an existing built master's inline JSON blocks.

Usage: python extract_workdir.py "<master.html>" "<work_dir>"

Lets us rebuild any master against a new template even when the source study
guides / course cache are no longer on disk. Does not touch the frozen scripts.
"""
import io
import json
import os
import re
import sys

SRC, WORK = sys.argv[1], sys.argv[2]
os.makedirs(WORK, exist_ok=True)
html = io.open(SRC, encoding="utf-8").read()


def block(bid):
    m = re.search(
        r'<script type="application/json" id="%s">(.*?)</script>' % bid, html, re.DOTALL
    )
    if not m:
        return None
    return json.loads(m.group(1).replace("<\\/script>", "</script>"))


study = block("study-data") or []
exam = ""
m = re.search(r'data-exam-date="([^"]*)"', html)
if not m:
    m = re.search(r'const EXAM_DATE = "([^"]*)"', html)
if m:
    exam = m.group(1)

out = {
    "parsed.json": {"fm": ({"exam-date": exam} if exam else {}), "sections": study},
    "quiz.json": block("quiz-data") or [],
    "refs_out.json": block("ref-data") or {},
    "drills_why.json": [],
    "quickcheck.json": block("quickcheck-data") or [],
    "flash.json": block("flashcard-data") or [],
    "scen.json": block("scenario-data") or [],
}
for name, data in out.items():
    with io.open(os.path.join(WORK, name), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(data, fh, ensure_ascii=False)

print(
    json.dumps(
        {
            "work": WORK,
            "sections": len(study),
            "quiz": len(out["quiz.json"]),
            "qc": len(out["quickcheck.json"]),
            "flash": len(out["flash.json"]),
            "scen": len(out["scen.json"]),
            "refs": len(out["refs_out.json"]),
            "exam_date": exam,
        }
    )
)
