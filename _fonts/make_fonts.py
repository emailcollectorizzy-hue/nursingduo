"""Instance, subset, and base64-encode PULSE fonts (one-time tooling)."""
import base64
import io
from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

LATIN = "U+0020-007E,U+2013-2019,U+2026,U+00D7,U+2022"
DOTO = "U+0020-005F,U+00D7,U+2022"  # space..underscore: punct, digits, A-Z

def build(src, axes, unicodes, out_name):
    font = TTFont(src)
    instantiateVariableFont(font, axes, inplace=True)
    buf = io.BytesIO()
    font.save(buf)
    buf.seek(0)
    opts = subset.Options(flavor="woff2", layout_features=["kern", "liga"],
                          hinting=True, desubroutinize=True)
    ss = subset.Subsetter(opts)
    ss.populate(unicodes=subset.parse_unicodes(unicodes))
    f2 = subset.load_font(buf, opts)
    ss.subset(f2)
    out = io.BytesIO()
    subset.save_font(f2, out, opts)
    raw = out.getvalue()
    b64 = base64.b64encode(raw).decode()
    with open(out_name, "w") as fh:
        fh.write(b64)
    print(f"{out_name}: {len(raw)} bytes woff2, {len(b64)} chars base64")

build("SpaceGrotesk-var.ttf", {"wght": 500}, LATIN, "sg-500.b64")
build("SpaceGrotesk-var.ttf", {"wght": 700}, LATIN, "sg-700.b64")
build("Doto-var.ttf", {"wght": 700, "ROND": 0}, DOTO, "doto-700.b64")
