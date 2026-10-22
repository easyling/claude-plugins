"""Round-trip a .docx through Easyling with its formatting carried as inline tags.
Python 3 standard library only.

python3 docx_tags.py extract <source.docx> <out.html>
    One <p data-i="P.N"> per paragraph with text: part P (0 is the body, then headers, footers,
    footnotes and endnotes), paragraph N of that part; table cells and text boxes included. Inside:
      - text formatted like most of the paragraph is plain; every other formatting is a
        <span data-r="K">, K naming that exact run formatting;
      - a hyperlink, content control, smart tag or tracked insertion is a <span data-c="C"> around
        its text, kept with its link or settings;
      - anything that is not text -- an image, a footnote mark, a field code, a tracked deletion,
        an equation, a symbol -- is an <img data-o="O">, copied back unchanged;
      - tabs are <span data-t="tab">, line breaks <br>.
    The output is the value of one manageDocuments html field. Comments are not translated; extract
    warns when they hold text.

python3 docx_tags.py build <source.docx> <translated.html> <out.docx> <lang>
    Writes the translation into a copy of the source. Each paragraph's content is rebuilt from the
    translated HTML: text gets the formatting of its span (or the paragraph's base formatting), each
    container is rebuilt around the text it wraps in the translation, each object goes back where the
    translation put it. Language attributes become <lang>. Every part of the file that holds no
    translated paragraph is copied byte for byte. Refuses rather than guesses: a paragraph whose tags
    did not come back exactly as sent is reported and left in the source language.

python3 docx_tags.py verify <a.docx> <b.docx>
    Same text, every visible character formatted alike and in the same containers, the same objects
    in the same order. Extract, build with the extracted HTML itself, then verify, to prove a
    document survives the round trip before paying for a translation.

python3 docx_tags.py show <file.docx> [text]
    Prints each paragraph (containing text, if given) with formatted stretches as [b u|word],
    containers as {hyperlink|words} and objects as <drawing>.

Formatting is compared on the complete run properties except w:lang, w:noProof and rsid attributes,
so fonts, sizes and colours are kept as well as bold, italic, underline and sub/superscript.
Bookmarks and comment ranges keep their place at the start or the end of their paragraph.
"""
import collections
import copy
import html
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from html.parser import HTMLParser

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
XML_NS = "http://www.w3.org/XML/1998/namespace"
TRANSLATED_PARTS = re.compile(r"word/(document|header\d*|footer\d*|footnotes|endnotes)\.xml$")
COMMENT_PARTS = re.compile(r"word/comments\w*\.xml$")


def q(tag):
    return "{%s}%s" % (W, tag)


def local(tag):
    return tag.split("}")[-1]


TEXT_CHILDREN = {q("t"), q("tab"), q("noBreakHyphen"), q("softHyphen")}
IGNORED_RUN_CHILDREN = {q("rPr"), q("lastRenderedPageBreak")}
WRAPPERS = {q(t) for t in ("hyperlink", "smartTag", "customXml", "ins", "moveTo", "sdt")}
MARKERS = {q(t) for t in ("bookmarkStart", "bookmarkEnd", "commentRangeStart", "commentRangeEnd",
                           "permStart", "permEnd", "moveFromRangeStart", "moveFromRangeEnd",
                           "moveToRangeStart", "moveToRangeEnd")}
DROPPED = {q("proofErr")}
VISIBLE_ON_WHITESPACE = {"u", "strike", "dstrike", "highlight", "shd", "bdr"}


def rpr_key(rpr):
    if rpr is None:
        return ()
    out = []
    for c in rpr:
        name = local(c.tag)
        if name in ("lang", "noProof"):
            continue
        attrs = tuple(sorted((local(k), v) for k, v in c.attrib.items() if "rsid" not in k and local(k) != "hint"))
        out.append((name, attrs))
    return tuple(sorted(out))


def holder(container):
    """Where a container keeps its content: a content control in its sdtContent, the rest in itself."""
    return container.find(q("sdtContent")) if container.tag == q("sdt") else container


def shell(container):
    """A copy of the container with its content removed and its properties kept."""
    s = copy.deepcopy(container)
    h = holder(s)
    for c in list(h):
        if not local(c.tag).endswith("Pr"):
            h.remove(c)
    return s


def run_items(r):
    """A run's content in order: ("t", text) and ("o", element) for everything that is not text."""
    out = []
    for c in r:
        if c.tag in IGNORED_RUN_CHILDREN:
            continue
        if c.tag == q("t"):
            out.append(("t", c.text or ""))
        elif c.tag == q("tab"):
            out.append(("t", "\t"))
        elif c.tag in (q("br"), q("cr")) and c.get(q("type")) in (None, "textWrapping"):
            out.append(("t", "\n"))
        elif c.tag == q("noBreakHyphen"):
            out.append(("t", "‑"))
        elif c.tag == q("softHyphen"):
            out.append(("t", "­"))
        else:
            out.append(("o", c))
    return out


def run_text(r):
    return "".join(x for kind, x in run_items(r) if kind == "t")


def has_text(el):
    return any((t.text or "").strip() for t in el.iter(q("t")))


def has_letters(el):
    return any(ch.isalpha() for tag in (q("t"), q("delText"), q("instrText")) for t in el.iter(tag) for ch in (t.text or ""))


class Paragraph:
    """One paragraph's content as a flat sequence of text and objects, each with its container chain."""

    def __init__(self, doc, p):
        self.p = p
        self.items = []          # ("t", key, rPr, chain, text) | ("o", [elements], chain)
        self.leading, self.trailing = [], []
        self.kept_untranslated = []
        self.walk(doc, p, ())
        texts = [it for it in self.items if it[0] == "t"]
        weight = collections.Counter()
        for _, k, _, _, t in texts:
            weight[k] += len(t)
        self.base = weight.most_common(1)[0][0] if weight else ()
        self.base_rpr = next((rpr for _, k, rpr, _, _ in texts if k == self.base and rpr is not None), None)
        self.fold()

    def walk(self, doc, node, chain):
        for c in list(holder(node)) if node is not self.p else list(node):
            if c.tag == q("pPr") or local(c.tag).endswith("Pr") and node is not self.p:
                continue
            if c.tag == q("r"):
                rpr = c.find(q("rPr"))
                for kind, x in run_items(c):
                    if kind == "t":
                        self.add_text(rpr_key(rpr), rpr, chain, x)
                    else:
                        placeholder = ET.Element(q("r"))
                        if rpr is not None:
                            placeholder.append(copy.deepcopy(rpr))
                        placeholder.append(x)
                        self.add_object(placeholder, chain)
            elif c.tag in WRAPPERS:
                self.walk(doc, c, chain + (doc.container(c),))
            elif c.tag in MARKERS:
                (self.trailing if any(it[0] == "t" for it in self.items) else self.leading).append(c)
            elif c.tag in DROPPED:
                continue
            else:
                if c.tag in (q("del"), q("moveFrom")):
                    self.kept_untranslated.append("tracked deletion")
                elif has_letters(c):
                    self.kept_untranslated.append("<%s>" % local(c.tag))
                self.add_object(c, chain)

    def add_text(self, key, rpr, chain, text):
        if not text:
            return
        last = self.items[-1] if self.items else None
        if last and last[0] == "t" and last[1] == key and last[3] == chain:
            self.items[-1] = ("t", key, last[2], chain, last[4] + text)
        else:
            self.items.append(("t", key, rpr, chain, text))

    def add_object(self, element, chain):
        last = self.items[-1] if self.items else None
        if last and last[0] == "o" and last[2] == chain:
            last[1].append(element)
        else:
            self.items.append(("o", [element], chain))

    def fold(self):
        """A whitespace-only stretch joins its neighbours when they share a formatting, else takes the
        base -- unless it carries something that shows on whitespace (underline, strike, highlight,
        shading, border)."""
        out = []
        for i, it in enumerate(self.items):
            if it[0] == "t":
                _, k, rpr, chain, t = it
                shows = any(name in VISIBLE_ON_WHITESPACE for name, _ in k)
                if not t.strip() and "\t" not in t and "\n" not in t and not shows:
                    prev = out[-1] if out else None
                    nxt = self.items[i + 1] if i + 1 < len(self.items) else None
                    if prev and nxt and prev[0] == nxt[0] == "t" and prev[1] == nxt[1] and prev[3] == nxt[3] == chain:
                        k, rpr = prev[1], prev[2]
                    else:
                        k, rpr = self.base, self.base_rpr
                if out and out[-1][0] == "t" and out[-1][1] == k and out[-1][3] == chain:
                    out[-1] = ("t", k, out[-1][2] if out[-1][2] is not None else rpr, chain, out[-1][4] + t)
                    continue
                it = ("t", k, rpr, chain, t)
            out.append(it)
        self.items = out

    def has_text(self):
        return any(it[0] == "t" and it[4].strip() for it in self.items)


class Doc:
    def __init__(self, path):
        self.path = path
        self.parts = []           # (name, raw, root, [paragraphs])
        self.formats = {}         # key -> (id, representative rPr)
        self.containers = []      # shells
        self.objects = []         # [elements] per object id
        self.plan = collections.OrderedDict()   # "P.N" -> Paragraph
        self.warnings = []
        with zipfile.ZipFile(path) as zf:
            names = zf.namelist()
            ordered = ["word/document.xml"] + sorted(n for n in names if TRANSLATED_PARTS.match(n) and n != "word/document.xml")
            for name in ordered:
                if name not in names:
                    continue
                raw = zf.read(name).decode("utf-8")
                register_namespaces(raw)
                root = ET.fromstring(raw)
                self.parts.append((name, raw, root, list(root.iter(q("p")))))
            for name in names:
                if COMMENT_PARTS.match(name) and has_text(ET.fromstring(zf.read(name))):
                    self.warnings.append("%s holds comments, which are not translated" % name)
        for pi, (name, _, _, paragraphs) in enumerate(self.parts):
            for ni, p in enumerate(paragraphs):
                para = Paragraph(self, p)
                if not para.has_text():
                    continue
                for tag in para.kept_untranslated:
                    self.warnings.append("%s paragraph %d: text of a %s is kept untranslated" % (name, ni, tag))
                for it in para.items:
                    if it[0] == "t":
                        if it[1] not in self.formats:
                            self.formats[it[1]] = (len(self.formats), it[2])
                        elif self.formats[it[1]][1] is None and it[2] is not None:
                            self.formats[it[1]] = (self.formats[it[1]][0], it[2])
                self.plan["%d.%d" % (pi, ni)] = para

    def container(self, element):
        self.containers.append(shell(element))
        return len(self.containers) - 1

    def html(self):
        self.objects = []
        blocks = []
        for key, para in self.plan.items():
            out, open_chain = [], ()
            for it in para.items:
                chain = it[3] if it[0] == "t" else it[2]
                while open_chain and open_chain != chain[:len(open_chain)]:
                    out.append("</span>")
                    open_chain = open_chain[:-1]
                for c in chain[len(open_chain):]:
                    out.append('<span data-c="%d">' % c)
                open_chain = chain
                if it[0] == "t":
                    body = encode_text(it[4])
                    out.append(body if it[1] == para.base else '<span data-r="%d">%s</span>' % (self.formats[it[1]][0], body))
                else:
                    self.objects.append(it[1])
                    out.append('<img data-o="%d">' % (len(self.objects) - 1))
            out.extend("</span>" for _ in open_chain)
            blocks.append('<p data-i="%s">%s</p>' % (key, "".join(out)))
        return "\n".join(blocks) + "\n"


def register_namespaces(raw):
    open_tag = re.search(r"<(?!\?)[\w:]+\b[^>]*>", raw).group(0)
    for prefix, uri in re.findall(r'xmlns:(\w+)="([^"]+)"', open_tag):
        ET.register_namespace(prefix, uri)


def encode_text(t):
    out = []
    for piece in re.split(r"(\t|\n)", t):
        if piece == "\t":
            out.append('<span data-t="tab">\t</span>')
        elif piece == "\n":
            out.append("<br>")
        elif piece:
            out.append(html.escape(piece, quote=False))
    return "".join(out)


class Translated(HTMLParser):
    """Reads a field back into {"P.N": [("t", format id or None, chain, text) | ("o", object id, chain)]}."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.paras = {}
        self.cur = None
        self.stack = []

    def chain(self):
        return tuple(int(v) for kind, v in self.stack if kind == "c")

    def fid(self):
        for kind, v in reversed(self.stack):
            if kind == "r":
                return int(v)
        return None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "p" and "data-i" in a:
            self.cur, self.stack = a["data-i"], []
            self.paras[self.cur] = []
        elif self.cur is None:
            return
        elif tag == "img":
            if "data-o" in a:
                self.paras[self.cur].append(("o", int(a["data-o"]), self.chain()))
        elif tag == "br":
            self.paras[self.cur].append(("t", self.fid(), self.chain(), "\n"))
        elif tag == "span" and a.get("data-t") == "tab":
            self.stack.append(("tab", None))
        elif tag == "span" and "data-c" in a:
            self.stack.append(("c", a["data-c"]))
        elif tag == "span" and "data-r" in a:
            self.stack.append(("r", a["data-r"]))
        else:
            self.stack.append(("other", tag))

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in ("br", "img", "p") and self.cur is not None and self.stack:
            self.stack.pop()

    def handle_endtag(self, tag):
        if tag == "p":
            self.cur = None
        elif self.cur is not None and tag not in ("br", "img") and self.stack:
            self.stack.pop()

    def handle_data(self, data):
        if self.cur is None:
            return
        text = "\t" if self.stack and self.stack[-1][0] == "tab" else data
        self.paras[self.cur].append(("t", self.fid(), self.chain(), text))


def parse(html_text):
    parser = Translated()
    parser.feed(html_text)
    return parser.paras


def signature(pieces):
    """The tags a paragraph carries: formatting spans, containers (each contiguous stretch), objects,
    tabs and line breaks."""
    sig = collections.Counter()
    prev_fid, prev_chain = None, ()
    for piece in pieces:
        chain = piece[2]
        for c in chain:
            if c not in prev_chain[:len(chain)] or prev_chain[:chain.index(c) + 1] != chain[:chain.index(c) + 1]:
                sig["c%d" % c] += 1
        if piece[0] == "o":
            sig["o%d" % piece[1]] += 1
            prev_fid = None
        else:
            _, fid, _, t = piece
            if fid is not None and (fid != prev_fid or chain != prev_chain):
                sig["r%d" % fid] += 1
            if t.strip() or fid is None:
                prev_fid = fid
            sig["tab"] += t.count("\t")
            sig["br"] += t.count("\n")
        prev_chain = chain
    return +sig


def make_run(rpr, text, lang):
    r = ET.Element(q("r"))
    if rpr is not None:
        new = copy.deepcopy(rpr)
        for el in new.iter(q("lang")):
            if el.get(q("val")):
                el.set(q("val"), lang)
        r.append(new)
    for piece in re.split(r"(\t|\n)", text):
        if piece == "\t":
            ET.SubElement(r, q("tab"))
        elif piece == "\n":
            ET.SubElement(r, q("br"))
        elif piece:
            t = ET.SubElement(r, q("t"))
            t.text = piece
            if piece != piece.strip():
                t.set("{%s}space" % XML_NS, "preserve")
    return r


def rebuild(doc, para, pieces, lang):
    p = para.p
    ppr = p.find(q("pPr"))
    for c in list(p):
        p.remove(c)
    if ppr is not None:
        p.append(ppr)
    for m in para.leading:
        p.append(m)
    by_id = {fid: rpr for _, (fid, rpr) in doc.formats.items()}
    merged = []
    for piece in pieces:
        if piece[0] == "t" and merged and merged[-1][0] == "t" and merged[-1][1] == piece[1] and merged[-1][2] == piece[2]:
            merged[-1] = ("t", piece[1], piece[2], merged[-1][3] + piece[3])
        else:
            merged.append(piece)
    stack = []   # (container id, element whose holder takes content)
    for piece in merged:
        chain = piece[2]
        while stack and tuple(c for c, _ in stack) != chain[:len(stack)]:
            stack.pop()
        for c in chain[len(stack):]:
            el = copy.deepcopy(doc.containers[c])
            (holder(stack[-1][1]) if stack else p).append(el)
            stack.append((c, el))
        target = holder(stack[-1][1]) if stack else p
        if piece[0] == "o":
            for el in doc.objects[piece[1]]:
                target.append(el)
        else:
            target.append(make_run(para.base_rpr if piece[1] is None else by_id[piece[1]], piece[3], lang))
    for m in para.trailing:
        p.append(m)


def serialize(raw, root):
    body = ET.tostring(root, encoding="unicode")
    original = re.search(r"<(?!\?)[\w:]+\b[^>]*>", raw).group(0)
    written = re.match(r"<[\w:]+\b[^>]*>", body).group(0)
    declared = set(re.findall(r'xmlns:(\w+)=', original))
    extra = [d for d in re.findall(r'xmlns:\w+="[^"]*"', written) if d.split("=")[0][6:] not in declared]
    opening = original[:-1].rstrip("/") + "".join(" " + d for d in extra) + ">"
    body = opening + body[len(written):]
    return raw[:raw.index(original)] + body


def build(source, translated_html, out_path, lang):
    doc = Doc(source)
    sent = parse(doc.html())
    got = parse(open(translated_html, encoding="utf-8").read())
    report, problems, touched = collections.Counter(), [], set()
    for key, para in doc.plan.items():
        if key not in got:
            problems.append("paragraph %s: missing from the translation; kept in the source language" % key)
            report["missing"] += 1
            continue
        if signature(sent[key]) != signature(got[key]):
            problems.append("paragraph %s: tags sent %s, returned %s; kept in the source language"
                            % (key, dict(signature(sent[key])), dict(signature(got[key]))))
            report["tag mismatch"] += 1
            continue
        rebuild(doc, para, got[key], lang)
        touched.add(int(key.split(".")[0]))
        report["written"] += 1
    replaced = {doc.parts[i][0]: serialize(doc.parts[i][1], doc.parts[i][2]) for i in touched}
    with zipfile.ZipFile(source) as zin, zipfile.ZipFile(out_path, "w") as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename in replaced:
                data = replaced[item.filename].encode("utf-8")
            zout.writestr(item, data)
    return report, problems


def shape(path):
    """Per part and paragraph: the characters with their formatting and containers, and the objects."""
    out = []
    with zipfile.ZipFile(path) as zf:
        for name in sorted(n for n in zf.namelist() if TRANSLATED_PARTS.match(n)):
            root = ET.fromstring(zf.read(name))
            for p in root.iter(q("p")):
                chars, objects = [], []

                def walk(node, ctx):
                    for c in (list(holder(node)) if node is not p else list(node)):
                        if c.tag == q("r"):
                            k = rpr_key(c.find(q("rPr")))
                            for kind, x in run_items(c):
                                if kind == "t":
                                    chars.extend((ch, k, ctx) for ch in x)
                                else:
                                    objects.append(local(x.tag))
                        elif c.tag in WRAPPERS:
                            walk(c, ctx + ((local(c.tag), tuple(sorted(c.attrib.items()))),))
                        elif c.tag not in MARKERS and c.tag not in DROPPED and not local(c.tag).endswith("Pr"):
                            objects.append(local(c.tag))
                walk(p, ())
                out.append((name, chars, objects))
    return out


def verify(a_path, b_path):
    a, b = shape(a_path), shape(b_path)
    if len(a) != len(b):
        return ["paragraph count %d vs %d" % (len(a), len(b))]
    problems = []
    for n, ((name, ca, oa), (_, cb, ob)) in enumerate(zip(a, b)):
        if "".join(c for c, _, _ in ca) != "".join(c for c, _, _ in cb):
            problems.append("%s paragraph %d: text differs" % (name, n))
            continue
        if oa != ob:
            problems.append("%s paragraph %d: objects %s vs %s" % (name, n, oa, ob))
        for i, ((c, ka, xa), (_, kb, xb)) in enumerate(zip(ca, cb)):
            if not c.strip():
                ka = tuple(x for x in ka if x[0] in VISIBLE_ON_WHITESPACE)
                kb = tuple(x for x in kb if x[0] in VISIBLE_ON_WHITESPACE)
            if ka != kb or xa != xb:
                problems.append("%s paragraph %d char %d %r: %s %s vs %s %s" % (name, n, i, c, ka, xa, kb, xb))
                break
    return problems


EMPHASIS = (("b", "b"), ("i", "i"), ("u", "u"), ("strike", "strike"), ("caps", "caps"), ("highlight", "highlight"))


def show(path, needle):
    doc = Doc(path)
    for key, para in doc.plan.items():
        parts = []
        for it in para.items:
            label = "".join("{%s|" % local(doc.containers[c].tag) for c in (it[3] if it[0] == "t" else it[2]))
            close = "}" * label.count("{")
            if it[0] == "o":
                parts.append(label + "".join("<%s>" % local(x.tag if x.tag != q("r") else x[-1].tag) for x in it[1]) + close)
                continue
            _, k, _, _, t = it
            if k == para.base:
                parts.append(label + t + close)
            else:
                names = dict(k)
                tags = [short for name, short in EMPHASIS if name in names]
                if "vertAlign" in names:
                    tags.append(dict(names["vertAlign"]).get("val", "vertAlign"))
                tags += sorted(n for n in names if n not in dict(EMPHASIS) and n != "vertAlign" and n not in dict(para.base))
                parts.append("%s[%s|%s]%s" % (label, " ".join(tags) or "other", t, close))
        text = "".join(parts)
        if not needle or needle in text:
            print("%s: %s" % (key, text.replace("\n", "⏎").replace("\t", "⇥")))


def main():
    cmd = sys.argv[1]
    if cmd == "verify":
        problems = verify(sys.argv[2], sys.argv[3])
        print("\n".join(problems) if problems else "identical: text, formatting, containers and objects")
        sys.exit(1 if problems else 0)
    if cmd == "show":
        show(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "")
    elif cmd == "extract":
        doc = Doc(sys.argv[2])
        text = doc.html()
        open(sys.argv[3], "w", encoding="utf-8").write(text)
        sig = collections.Counter()
        for pieces in parse(text).values():
            sig.update(signature(pieces))
        print("%d paragraphs, %d formats, %d tags (%d formatting, %d container, %d object) -> %s"
              % (len(doc.plan), len(doc.formats), sum(sig.values()),
                 sum(v for k, v in sig.items() if k[0] == "r"), sum(v for k, v in sig.items() if k[0] == "c"),
                 sum(v for k, v in sig.items() if k[0] == "o"), sys.argv[3]))
        for w in doc.warnings:
            print("WARNING: " + w)
    elif cmd == "build":
        report, problems = build(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])
        for line in problems:
            print(line)
        print(dict(report), "->", sys.argv[4])


if __name__ == "__main__":
    main()
