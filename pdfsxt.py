"""PDF Workbench: a local PDF editor.  Run:  python app.py [file.pdf]
Everything stays on this computer; the server only listens on 127.0.0.1."""
import io, json, os, sys, threading, webbrowser
try:
    import pymupdf as fitz  # PyMuPDF (new name)
except ImportError:
    import fitz
from flask import Flask, jsonify, request, send_file, send_from_directory

HERE = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__)
import glob


def setup_ocr():
    """OCR needs Tesseract language data (PyMuPDF bundles the engine itself)."""
    paths = [os.environ.get("TESSDATA_PREFIX", ""), os.path.join(HERE, "tessdata"),
             r"C:\Program Files\Tesseract-OCR\tessdata", r"C:\Program Files (x86)\Tesseract-OCR\tessdata",
             "/opt/homebrew/share/tessdata", "/usr/local/share/tessdata", "/usr/share/tessdata"]
    paths += glob.glob("/usr/share/tesseract-ocr/*/tessdata")
    for c in paths:
        if c and glob.glob(os.path.join(c, "*.traineddata")):
            os.environ["TESSDATA_PREFIX"] = c
            return True
    return False

S = {"hist": [], "name": "document.pdf", "v": 0}  # undo history = list of PDF bytes


# ---------- helpers ----------
def cur():
    if not S["hist"]:
        raise ValueError("Open a PDF first.")
    return fitz.open(stream=S["hist"][-1], filetype="pdf")


def commit(d):
    S["hist"] = (S["hist"] + [d.tobytes(garbage=3, deflate=True)])[-30:]
    S["v"] += 1
    d.close()


def load(data, name):
    d = fitz.open(stream=data, filetype="pdf")
    if d.needs_pass:
        raise ValueError("This PDF is password-protected. Remove the password first.")
    S.update(hist=[data], name=name, v=S["v"] + 1)


def state():
    if not S["hist"]:
        return {"open": False}
    d = cur()
    return {"open": True, "name": S["name"], "v": S["v"], "undo": len(S["hist"]) > 1,
            "pages": [[p.rect.width, p.rect.height] for p in d]}


def rect(p, r):  # display coords -> page coords (handles rotated pages)
    return (fitz.Rect(*r) * p.derotation_matrix).normalize()


def rgb(h):
    return tuple(int(h[i:i + 2], 16) / 255 for i in (1, 3, 5))


def pick_font(flags, name):
    n, b, i = name.lower(), bool(flags & 16) or "bold" in name.lower(), bool(flags & 2) or "italic" in name.lower()
    k = int(b) + 2 * int(i)
    if flags & 8 or "courier" in n or "mono" in n:
        return ["cour", "cobo", "coit", "cobi"][k]
    if flags & 4 or "times" in n or ("serif" in n and "sans" not in n):
        return ["tiro", "tibo", "tiit", "tibi"][k]
    return ["helv", "hebo", "heit", "hebi"][k]


def parse_pages(s, n):
    out = []
    for part in s.split(","):
        a, _, b = part.partition("-")
        out += range(int(a) - 1, int(b or a))
    return [i for i in dict.fromkeys(out) if 0 <= i < n]


@app.errorhandler(Exception)
def oops(e):
    code = getattr(e, "code", None)
    return jsonify(error=str(e)), code if isinstance(code, int) else 400


# ---------- routes ----------
@app.get("/")
def index():
    return send_from_directory(HERE, "index.html")


@app.get("/api/state")
def api_state():
    return jsonify(state())


@app.post("/api/open")
def api_open():
    f = request.files["file"]
    load(f.read(), f.filename or "document.pdf")
    return jsonify(state())


@app.post("/api/merge")
def api_merge():
    d = cur()
    d.insert_pdf(fitz.open(stream=request.files["file"].read(), filetype="pdf"))
    commit(d)
    return jsonify(state())


@app.post("/api/image")
def api_image():
    d = cur()
    p = d[int(request.form["page"])]
    p.insert_image(rect(p, json.loads(request.form["rect"])), stream=request.files["file"].read(), rotate=p.rotation)
    commit(d)
    return jsonify(state())


@app.get("/api/page/<int:n>.png")
def api_page(n):
    z = float(request.args.get("z", 1.5))
    pix = cur()[n].get_pixmap(matrix=fitz.Matrix(z, z))
    r = send_file(io.BytesIO(pix.tobytes("png")), mimetype="image/png")
    r.headers["Cache-Control"] = "max-age=3600"
    return r


@app.get("/api/span")
def api_span():
    p = cur()[int(request.args["page"])]
    pt = fitz.Point(float(request.args["x"]), float(request.args["y"])) * p.derotation_matrix
    for b in p.get_text("dict")["blocks"]:
        for l in b.get("lines", []):
            for s in l["spans"]:
                if s["text"].strip() and fitz.Rect(s["bbox"]).contains(pt):
                    m = p.rotation_matrix
                    o = fitz.Point(s["origin"]) * m
                    return jsonify(found=True, text=s["text"], size=s["size"], color="#%06x" % s["color"],
                                   font=pick_font(s["flags"], s["font"]),
                                   bbox=list((fitz.Rect(s["bbox"]) * m).normalize()), origin=[o.x, o.y])
    return jsonify(found=False)


@app.get("/api/find")
def api_find():
    q, out = request.args.get("q", ""), []
    for i, p in enumerate(cur()):
        hits = [list((r * p.rotation_matrix).normalize()) for r in p.search_for(q)] if q else []
        if hits:
            out.append({"page": i, "rects": hits})
    return jsonify(out)


@app.get("/api/fields")
def api_fields():
    p, out = cur()[int(request.args["page"])], []
    for w in p.widgets():
        t = w.field_type_string
        if t not in ("Text", "CheckBox", "RadioButton", "ComboBox", "ListBox"):
            continue
        v = w.field_value
        if t in ("CheckBox", "RadioButton"):
            v = bool(v) and str(v).lower() not in ("off", "false", "0")
        out.append(dict(xref=w.xref, name=w.field_name, type=t, rect=list((w.rect * p.rotation_matrix).normalize()),
                        value=v if t in ("CheckBox", "RadioButton") else (v or ""),
                        choices=[c if isinstance(c, str) else c[-1] for c in (w.choice_values or [])]))
    return jsonify(out)


@app.get("/api/text")
def api_text():
    return jsonify(text=cur()[int(request.args["page"])].get_text())


@app.get("/api/export")
def api_export():
    d, pages, pw = cur(), request.args.get("pages", ""), request.args.get("pw", "")
    if pages:
        d.select(parse_pages(pages, len(d)))
    kw = dict(garbage=4, deflate=True)
    if pw:
        kw.update(encryption=fitz.PDF_ENCRYPT_AES_256, user_pw=pw, owner_pw=pw)
    stem = os.path.splitext(S["name"])[0]
    tag = "pages" if pages else ("protected" if pw else "edited")
    return send_file(io.BytesIO(d.tobytes(**kw)), mimetype="application/pdf", as_attachment=True,
                     download_name=f"{stem}-{tag}.pdf")


@app.post("/api/op")
def api_op():
    j = request.get_json()
    k, pg, d = j["op"], j.get("pages", []), cur()
    n = len(d)
    if k == "undo":
        if len(S["hist"]) > 1:
            S["hist"].pop()
            S["v"] += 1
        return jsonify(state())
    if k == "rotate":
        for i in pg:
            d[i].set_rotation((d[i].rotation + j["deg"]) % 360)
    elif k == "delete":
        keep = [i for i in range(n) if i not in pg]
        if not keep:
            raise ValueError("A PDF needs at least one page.")
        d.select(keep)
    elif k == "move":
        i, to = j["i"], j["to"]
        d.move_page(i, (to + 1 if to + 1 < n else -1) if to > i else to)
    elif k == "duplicate":
        for i in sorted(pg, reverse=True):
            d.fullcopy_page(i, i + 1 if i + 1 < n else -1)
    elif k == "blank":
        i = pg[0]
        d.new_page(i + 1, width=d[i].rect.width, height=d[i].rect.height)
    elif k == "text":
        p, s, x, y, t = d[j["page"]], float(j["size"]), j["x"], j["y"], j["text"]
        w = max(60, min(380, p.rect.width - x - 8))
        h = s * 1.5 * (t.count("\n") + 1 + len(t) // 45) + 8
        for _ in range(4):  # grow the box until the text fits
            if p.insert_textbox(rect(p, [x, y, x + w, y + h]), t, fontsize=s, fontname="helv",
                                color=rgb(j["color"]), rotate=p.rotation) >= 0:
                break
            h *= 2
    elif k == "edit":  # replace one line of existing text
        p = d[j["page"]]
        r = rect(p, j["bbox"])
        r.y0 += r.height * .12
        r.y1 -= r.height * .12
        p.add_redact_annot(r, fill=(1, 1, 1))
        p.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE)
        if j["text"].strip():
            p.insert_text(fitz.Point(*j["origin"]) * p.derotation_matrix, j["text"], fontsize=float(j["size"]),
                          fontname=j["font"], color=rgb(j["color"]), rotate=p.rotation)
    elif k == "ocr":
        if not setup_ocr():
            raise ValueError("OCR needs language data. Download eng.traineddata from "
                             "github.com/tesseract-ocr/tessdata_fast and put it in a folder named tessdata next to app.py.")
        out = fitz.open()
        for i in range(n):
            if i in pg:
                pix = d[i].get_pixmap(dpi=300)
                out.insert_pdf(fitz.open("pdf", pix.pdfocr_tobytes(language=j.get("lang", "eng"))))
            else:
                out.insert_pdf(d, from_page=i, to_page=i)
        d = out
    elif k == "fill":
        for f in j["fields"]:
            for w in d[f["page"]].widgets():
                if w.xref == f["xref"]:
                    w.field_value = f["value"]
                    w.update()
    elif k in ("whiteout", "highlight", "redact"):
        p = d[j["page"]]
        r = rect(p, j["rect"])
        if k == "whiteout":
            p.draw_rect(r, color=None, fill=(1, 1, 1))
        elif k == "highlight":
            p.draw_rect(r, color=None, fill=(1, .92, .2), fill_opacity=.4)
        else:
            p.add_redact_annot(r, fill=(0, 0, 0))
            p.apply_redactions()
    else:
        raise ValueError(f"Unknown action: {k}")
    commit(d)
    return jsonify(state())


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    if args:
        load(open(args[0], "rb").read(), os.path.basename(args[0]))
    port = int(os.environ.get("PORT", 5173))
    threading.Timer(.8, lambda: webbrowser.open(f"http://127.0.0.1:{port}")).start()
    app.run("127.0.0.1", port)


if __name__ == "__main__":
    main()
