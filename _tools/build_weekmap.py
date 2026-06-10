"""Build a topic->week map from the vault folder structure for each course, and
inject it into the built master HTML at the WEEK_MAP sentinel.

Vault layout: 08 School/<Course>/Week N — Theme/<Topic>/...
The master's section `chapter` field == <Topic>, so the map keys are topics.
Courses/topics with no week folder are simply absent → template falls back to
flat chapter grouping for them (under an "Unscheduled" group).

Usage: python build_weekmap.py "<master.html>" "<Course>"
"""
import io
import json
import os
import re
import sys

MASTER, COURSE = sys.argv[1], sys.argv[2]
VAULT = r"C:\Users\izzyp\Documents\Iz0Vault\08 School"
course_dir = os.path.join(VAULT, COURSE)

week_map = {}   # topic -> {w: <week number>, label: "Week N — Theme"}
if os.path.isdir(course_dir):
    for name in os.listdir(course_dir):
        wd = os.path.join(course_dir, name)
        if not os.path.isdir(wd):
            continue
        m = re.match(r"\s*Week\s+0*(\d+)\b", name)
        if not m:
            continue
        wn = int(m.group(1))
        label = name.strip()
        for entry in os.listdir(wd):
            full = os.path.join(wd, entry)
            topic = None
            if os.path.isdir(full):
                topic = entry                                    # one-folder-per-topic layout
            elif entry.endswith(" - Study Guide.md"):
                topic = entry[: -len(" - Study Guide.md")]        # one-file-per-topic layout
            if topic:
                week_map[topic] = {"w": wn, "label": label}

html = io.open(MASTER, encoding="utf-8").read()
payload = json.dumps(week_map, ensure_ascii=False)
new = "/*WEEK_MAP*/" + payload + "/*/WEEK_MAP*/"
patched, n = re.subn(r"/\*WEEK_MAP\*/.*?/\*/WEEK_MAP\*/", lambda _: new, html, count=1, flags=re.DOTALL)
if n != 1:
    print(json.dumps({"course": COURSE, "error": "WEEK_MAP sentinel not found", "sentinels": html.count("/*WEEK_MAP*/")}))
    sys.exit(1)
io.open(MASTER, "w", encoding="utf-8", newline="\n").write(patched)
print(json.dumps({"course": COURSE, "topics_mapped": len(week_map), "weeks": sorted({v["w"] for v in week_map.values()})}))
