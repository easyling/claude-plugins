"""Compare a translated .docx with an approved translation of the same document, text and formatting.
Python 3 standard library only.

python3 docx_compare.py <ours.docx> <approved.docx> [report.md]

Paragraphs are aligned by text similarity, so the two files need not have the same paragraph count.
For each aligned pair the report says whether the text is identical and how each word both sides
share is formatted (bold, italic, underline, caps, sub/superscript, or plain). Differences are
findings to read, not verdicts: the approved file can be the one that departs from its source.
"""
import collections
import difflib
import re
import sys
import zipfile
import xml.etree.ElementTree as ET

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from docx_tags import WRAPPERS, holder, q, run_text  # noqa: E402


def on(rpr, tag):
    el = rpr.find(q(tag)) if rpr is not None else None
    return el is not None and el.get(q("val"), "true") not in ("0", "false", "none")


def emphasis(rpr):
    out = [name for name in ("b", "i", "u", "caps") if on(rpr, name)]
    if rpr is not None and rpr.find(q("vertAlign")) is not None:
        out.append(rpr.find(q("vertAlign")).get(q("val")))
    return " ".join(out) or "plain"


def runs(node, top):
    """The runs of a paragraph in order, inside hyperlinks and other wrappers too."""
    for c in (list(holder(node)) if node is not top else list(node)):
        if c.tag == q("r"):
            yield c
        elif c.tag in WRAPPERS:
            yield from runs(c, top)


def paragraphs(path):
    root = ET.fromstring(zipfile.ZipFile(path).read("word/document.xml"))
    out = []
    for p in root.iter(q("p")):
        words = collections.Counter()
        text = []
        for r in runs(p, p):
            t = run_text(r)
            text.append(t)
            for word in re.findall(r"\w[\w\-]*", t):
                words[(emphasis(r.find(q("rPr"))), word.lower())] += 1
        joined = re.sub(r"\s+", " ", "".join(text)).strip()
        if joined:
            out.append((joined, words))
    return out


def align(a, b):
    """Needleman-Wunsch over paragraphs: a pair scores its similarity (below 0.5 it costs), a gap 0."""
    n, m = len(a), len(b)
    sim = [[difflib.SequenceMatcher(None, a[i][0], b[j][0]).ratio() for j in range(m)] for i in range(n)]

    def gain(i, j):
        return sim[i][j] if sim[i][j] >= 0.5 else -1

    score = [[0.0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            score[i][j] = max(score[i - 1][j], score[i][j - 1], score[i - 1][j - 1] + gain(i - 1, j - 1))
    pairs, i, j = [], n, m
    while i > 0 and j > 0:
        if score[i][j] == score[i - 1][j - 1] + gain(i - 1, j - 1):
            pairs.append((i - 1, j - 1, sim[i - 1][j - 1]))
            i, j = i - 1, j - 1
        elif score[i][j] == score[i - 1][j]:
            pairs.append((i - 1, None, 0))
            i -= 1
        else:
            pairs.append((None, j - 1, 0))
            j -= 1
    pairs += [(k, None, 0) for k in range(i - 1, -1, -1)] + [(None, k, 0) for k in range(j - 1, -1, -1)]
    return list(reversed(pairs))


def main():
    ours, ref = paragraphs(sys.argv[1]), paragraphs(sys.argv[2])
    lines, exact, similar, fmt_same, fmt_diff = [], 0, 0, 0, 0
    for i, j, s in align(ours, ref):
        if i is None:
            lines.append("- **only in the approved file:** %s" % ref[j][0][:300])
            continue
        if j is None:
            lines.append("- **only in ours:** %s" % ours[i][0][:300])
            continue
        if ours[i][0] == ref[j][0]:
            exact += 1
        else:
            similar += 1
            lines.append("- **text differs** (%.2f)\n  - ours:     %s\n  - approved: %s" % (s, ours[i][0][:600], ref[j][0][:600]))
        shared = {w for _, w in ours[i][1]} & {w for _, w in ref[j][1]}
        mo = collections.Counter({k: v for k, v in ours[i][1].items() if k[1] in shared})
        mr = collections.Counter({k: v for k, v in ref[j][1].items() if k[1] in shared})
        if mo == mr:
            fmt_same += 1
        else:
            fmt_diff += 1
            lines.append("- **formatting differs** in \"%s\"\n  - only ours:     %s\n  - only approved: %s"
                         % (ours[i][0][:80], sorted((mo - mr).elements()), sorted((mr - mo).elements())))
    head = ["# %s vs %s" % (sys.argv[1].rsplit("/", 1)[-1], sys.argv[2].rsplit("/", 1)[-1]), "",
            "- paragraphs: ours %d, approved %d, aligned %d" % (len(ours), len(ref), exact + similar),
            "- text identical: %d of %d aligned" % (exact, exact + similar),
            "- formatting identical (every shared word formatted the same way): %d of %d aligned"
            % (fmt_same, fmt_same + fmt_diff), ""]
    if len(sys.argv) > 3:
        open(sys.argv[3], "w", encoding="utf-8").write("\n".join(head + lines) + "\n")
    print("\n".join(head))


if __name__ == "__main__":
    main()
