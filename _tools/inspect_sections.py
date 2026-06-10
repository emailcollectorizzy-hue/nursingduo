import io
import json
import os

d = json.load(io.open(os.path.join(os.environ["TEMP"], "qp-final-NS250MedSurg", "parsed.json"), encoding="utf-8"))
secs = d["sections"]
print("fields:", sorted(secs[0].keys()))
print("fm:", json.dumps(d.get("fm", {}), ensure_ascii=False)[:300])
chs = []
for s in secs:
    c = s.get("chapter")
    if c not in chs:
        chs.append(c)
print("chapters:", len(chs))
print(json.dumps(chs, ensure_ascii=False))
# any week-ish field?
print("sample section keys/values (minus html):")
s0 = {k: v for k, v in secs[0].items() if k != "html"}
print(json.dumps(s0, ensure_ascii=False)[:400])
