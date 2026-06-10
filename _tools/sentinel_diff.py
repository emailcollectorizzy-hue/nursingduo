"""Drift check: PULSE CORE + PULSE MOTION sentinel blocks must be byte-identical
between template-v2.html (source of truth) and the hub index.html."""
import io


def block(path, start, end):
    s = io.open(path, encoding="utf-8").read()
    return s[s.index(start):s.index(end) + len(end)]


TPL = r"C:\Users\izzyp\.claude\skills\quizpage\template-v2.html"
HUB = r"C:\Users\izzyp\src\nursingduo\index.html"
core_t = block(TPL, "/* ═══ PULSE CORE v1", "/* ═══ /PULSE CORE ═══ */")
core_h = block(HUB, "/* ═══ PULSE CORE v1", "/* ═══ /PULSE CORE ═══ */")
pm_t = block(TPL, "/* ═══ PULSE MOTION v1", "/* ═══ /PULSE MOTION ═══ */")
pm_h = block(HUB, "/* ═══ PULSE MOTION v1", "/* ═══ /PULSE MOTION ═══ */")
print("CORE identical:", core_t == core_h, "| PM identical:", pm_t == pm_h)
assert core_t == core_h and pm_t == pm_h
