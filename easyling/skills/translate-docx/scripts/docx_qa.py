"""Mechanical QA of a translated document, paragraph by paragraph, before it is written into the .docx.
Python 3 standard library only.

python3 docx_qa.py <source.html> <translated.html> [--lang CODE] [--source-decimal point|comma]
                   [--decimal point|comma] [--source-letters LETTERS]

source.html is what docx_tags.py extract wrote; translated.html is the manageDocuments field value;
--lang is the target language code.

- missing: a paragraph of the source that did not come back;
- tags: not the same formatting spans, containers, objects, tabs and line breaks as the source
  (docx_tags.py build refuses such a paragraph and leaves it in the source language);
- numbers lost: a number of the source that is not in the translation -- the dangerous direction;
- numbers added: a number of the translation the source lacks, often a word the target writes in
  digits ("two" -> 2) or a localised date (October -> 10): read it, it is rarely an error.
  Numbers are compared by value: digit grouping (1 000, 1,000, 1.000) and the decimal separator are
  read with each side's convention (--source-decimal, --decimal; without them a separator followed by
  exactly three digits counts as grouping), and digits of any script count as the same digits;
- decimal: with --decimal point, a digit-comma-digit decimal in the translation; with --decimal comma,
  a digit-point-digit one. Grouping (1,000) is not reported;
- source letters: with --source-letters, any of those letters left in the translation (letters the
  source language has and the target does not, e.g. "őű" for Hungarian into English);
- glued tag: a formatted stretch or a container that runs straight into a letter outside it, as in
  "milk</g>whey" -- a misplaced tag in a language that separates words with spaces. Not checked for
  languages written without spaces (Chinese, Japanese, Thai, Lao, Khmer, Burmese, Tibetan, Dzongkha);
  in compounding languages (German, Dutch, Hungarian, Finnish...) read it, it can be right.

Exits 1 when there is a finding.
"""
import argparse
import collections
import re
import sys
import unicodedata

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from docx_tags import parse, signature  # noqa: E402

NUMBER = re.compile(r"\d+(?:[   .,'’]\d+)*")
SEPARATOR = re.compile(r"[   .,'’]")
DECIMAL_CHAR = {"point": ".", "comma": ","}
NO_SPACES = {"zh", "ja", "th", "lo", "km", "my", "bo", "dz"}


def ascii_digits(t):
    return "".join(str(unicodedata.decimal(ch)) if unicodedata.decimal(ch, None) is not None else ch for ch in t)


def value(token, decimal):
    """'1 000' -> '1000', '80,5' with a decimal comma -> '80.5'."""
    groups = SEPARATOR.split(token)
    seps = SEPARATOR.findall(token)
    if not seps:
        return token
    last = seps[-1]
    if decimal:
        is_fraction = (last == DECIMAL_CHAR[decimal])
    else:
        is_fraction = last in ".," and len(groups[-1]) != 3
    if is_fraction:
        return "".join(groups[:-1]) + "." + groups[-1]
    return "".join(groups)


def numbers(t, decimal):
    return collections.Counter(value(n, decimal) for n in NUMBER.findall(ascii_digits(t)))


def text(pieces):
    return "".join(p[3] for p in pieces if p[0] == "t")


def wrong_decimal(t, decimal):
    """A digit-separator-digit decimal written with the other convention's separator."""
    other = "," if decimal == "point" else "."
    for token in NUMBER.findall(ascii_digits(t)):
        seps = SEPARATOR.findall(token)
        groups = SEPARATOR.split(token)
        if seps and seps[-1] == other and len(groups[-1]) != 3:
            return token
    return None


def glued(pieces):
    texts = [p for p in pieces if p[0] == "t"]
    out = []
    for a, b in zip(texts, texts[1:]):
        if (a[1], a[2]) != (b[1], b[2]) and a[3][-1:].isalpha() and b[3][:1].isalpha():
            out.append(a[3][-12:] + "|" + b[3][:12])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("source")
    ap.add_argument("translated")
    ap.add_argument("--lang", default="")
    ap.add_argument("--source-decimal", choices=sorted(DECIMAL_CHAR))
    ap.add_argument("--decimal", choices=sorted(DECIMAL_CHAR))
    ap.add_argument("--source-letters", default="")
    args = ap.parse_args()
    src = parse(open(args.source, encoding="utf-8").read())
    tgt = parse(open(args.translated, encoding="utf-8").read())
    leftover = re.compile("[%s]" % re.escape(args.source_letters), re.I) if args.source_letters else None
    check_glue = args.lang.split("-")[0].lower() not in NO_SPACES
    findings = []
    for key, pieces in src.items():
        if key not in tgt:
            findings.append((key, "missing", text(pieces)[:80]))
            continue
        t = text(tgt[key])
        if signature(tgt[key]) != signature(pieces):
            findings.append((key, "tags", "sent %s, returned %s" % (dict(signature(pieces)), dict(signature(tgt[key])))))
        ns, nt = numbers(text(pieces), args.source_decimal), numbers(t, args.decimal)
        if ns - nt:
            findings.append((key, "numbers lost", "%s in %r" % (dict(ns - nt), t[:120])))
        if nt - ns:
            findings.append((key, "numbers added", "%s in %r" % (dict(nt - ns), t[:120])))
        if args.decimal and wrong_decimal(t, args.decimal):
            findings.append((key, "decimal", repr(wrong_decimal(t, args.decimal)) + " in " + repr(t[:120])))
        if leftover and leftover.search(t):
            findings.append((key, "source letters", repr(leftover.search(t).group(0)) + " in " + repr(t[:120])))
        if check_glue:
            for g in glued(tgt[key]):
                findings.append((key, "glued tag", repr(g)))
    for key, kind, detail in findings:
        print("paragraph %-6s %-14s %s" % (key, kind, detail))
    print("%d findings in %d paragraphs" % (len(findings), len(src)))
    sys.exit(1 if findings else 0)


if __name__ == "__main__":
    main()
