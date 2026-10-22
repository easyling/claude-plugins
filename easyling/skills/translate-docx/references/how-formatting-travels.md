# How formatting travels

What `scripts/docx_tags.py` does with a .docx, what Easyling stores, and what comes back.

## Out of the document

- **Parts.** The body (table cells and text boxes included), headers, footers, footnotes and
  endnotes are translated, paragraph by paragraph; `<p data-i="P.N">` names part P, paragraph N.
  Comments are not translated.
- **Runs merged.** Adjacent runs whose formatting is the same are joined first. Formatting is
  compared on the complete run properties -- font, size, colour, bold, italic, underline,
  highlight, shading, caps, sub- and superscript -- ignoring only language, proofing and revision
  ids.
- **Base and formatting tags.** In each paragraph the formatting that covers the most characters
  is the base and gets no tag. Every other stretch becomes `<span data-r="K">`, K naming that exact
  formatting for the whole document.
- **Containers.** A hyperlink, a content control, a smart tag or a tracked insertion becomes
  `<span data-c="C">` around its text; it is rebuilt, link and settings included, around the words
  that translate that text.
- **Objects.** Everything that is not text -- an image, a note mark, a field code, a tracked
  deletion, an equation, a symbol, a page break -- becomes `<img data-o="O">`. It is copied back
  unchanged wherever the translation puts it. A text box is an object too; its own paragraphs are
  translated as paragraphs.
- **Whitespace.** A stretch of spaces joins its neighbours when both share a formatting, or takes
  the base, unless it carries something visible on a space (underline, strike, highlight,
  shading, border).
- **Tabs and line breaks** become `<span data-t="tab">` and `<br>`. Bookmarks and comment ranges
  stay at the start or the end of their paragraph.

## In Easyling

- The whole document is one `html` field of `manageDocuments translate`. Each `<p>` becomes one
  block entry; in its stored markup the paragraph itself is `<g id="_0">`, spans and containers are
  further `<g>` tags, objects and line breaks `<x>` placeholders.
- Easyling also turns a number that stands alone (a year after a month name, a table value) into an
  `<x>` placeholder: the AI can move it but not change it.
- No translation is stored whose tags differ from the source's.
- The field comes back as the same HTML with every block translated and every span, container and
  object, attributes included, where the translation put it.

## Back into the document

- Each paragraph's content is rebuilt: text outside spans gets the paragraph's base formatting,
  text inside `data-r="K"` gets formatting K, copied from the source run, with its language set to
  the target language; containers and objects are put back as they were.
- Every part without a translated paragraph is copied byte for byte, and the namespace
  declarations of the rewritten parts are kept as written, so Word opens the file without repair.
- A paragraph whose tags did not come back exactly as sent is reported and left in the source
  language; the build never guesses where a tag belongs.

## What stays in the source language

`extract` warns about each of these: the text of a tracked deletion (accept or reject changes in
Word first for a clean result), comments, and text inside an equation or a field code. A field's
result -- a date, a page number -- is translated, and Word may recalculate it when it updates
fields.

## Checking the converter on a document

`extract`, then `build` with the extracted HTML itself, then `verify` against the original: the
text must be identical, every visible character formatted and contained as before, and every object
in the same order. A document that fails this would lose something in translation too; check it
before every paid run.
