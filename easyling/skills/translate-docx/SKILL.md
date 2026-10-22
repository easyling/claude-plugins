---
name: translate-docx
description: Use when a Word document (.docx) is to be translated with Easyling - load it before asking for or opening the file. Keeps bold, underline and other formatting; checks a translated .docx.
compatibility: Needs the Easyling MCP server and Python 3
---

# Translate a Word document

Translate a .docx with an Easyling project's own pipeline -- translation memory, machine
translation, the AI with the styleguide and the published glossary -- and write the translation
back into the same file, with every bit of formatting on the words that translate it. The Easyling
MCP takes text and HTML, not files, so the scripts in `scripts/` do the file work:

- `docx_tags.py` turns the document into one HTML field and writes the translation back;
- `docx_qa.py` checks the translation before it goes into the file;
- `docx_compare.py` measures the result against an approved translation.

They need Python 3 and nothing else. Run them where the file is: in Claude Code, or in a client
that runs code on uploaded files.

## When to use

- A Word document to translate with a project's glossary, memory and styleguide, formatting kept.
- A translated .docx to check against the approved translation of the same document.

Hand-offs. Why a term or a style rule is not followed, and changing the glossary, styleguide or AI
configuration, belong to the linguistic-quality skill. Website content belongs to the onboarding
skill. A .doc, .pdf or .odt file is converted to .docx first (Word: Save As).

## Intake

1. **The project** whose resources should apply (`projects list`), and **the target language**
   as the project lists it.
2. **The file(s)**, as paths you can read.
3. **An approved translation** of the same document, if there is one: it turns the run into a
   measurement.
4. **Budget**: the translation is paid like any other content of the project, and its words count.

## Formatting is preserved, never prescribed

The source document already formats what matters: bold headings, underlined warnings or
allergens, italic Latin names, superscript note marks. Each formatted stretch travels as an inline
tag and is written back onto the words that translate it, so no rule says what to bold.

- Do not add styleguide rules about what to bold, underline or italicise: they compete with the
  tags.
- The AI copies a styleguide example that shows tags literally. Make every such example exact:
  the tag around the translated word only, brackets and punctuation outside, as in
  `(<g>milk</g>)`, never `<g>(milk)</g>`.
- Test a styleguide change with `aiTranslationConfig testTranslate` on a real tagged paragraph and
  several runs before saving it.

How the tags are made and read back: [how formatting travels](references/how-formatting-travels.md).

## Steps

1. **Check that the project will translate.** `manageDocuments translate` obeys the project's
   auto pre-translate switches. Read `projectSettings get` (autoTranslateConfig.autoPretranslateEnabled,
   autoTranslateConfig.useAutomaticPostEditing), `aiTranslationConfig listSlots` (postEditingEnabled)
   and `linguisticResources listProjectResources` (publishedGlossaryTargets for the engine and
   language). If anything is off, say what, and hand the change to the linguistic-quality skill.
2. **Prepare and prove the round trip**, before anything is paid for:
   ```
   python3 scripts/docx_tags.py extract in.docx work/source.html
   python3 scripts/docx_tags.py build in.docx work/source.html work/identity.docx <source language>
   python3 scripts/docx_tags.py verify in.docx work/identity.docx
   ```
   `verify` must answer "identical". The body, tables, text boxes, headers, footers, footnotes and
   endnotes are translated; hyperlinks keep their link around the translated words; images, note
   marks, field codes and equations come back where the translation puts them. A warning names
   text that stays in the source language -- a tracked deletion, comments, text inside an equation
   or a field: tell the user (accepting tracked changes in Word first gives a clean result).
3. **Translate**, through the write gate: `manageDocuments translate` with one field, name `doc`,
   type `html`, the whole of `work/source.html` as its value, kind `file`, a path such as
   `/docx/<file-name>`, and the target language. A document of about a hundred paragraphs
   outlasts the client's request timeout while the server keeps going: wait about three minutes
   and send the identical call again; it comes back complete with origin `stored`, at no new
   cost. Save the field's value exactly as returned to `work/translated.html`.
4. **Check it**:
   ```
   python3 scripts/docx_qa.py work/source.html work/translated.html --lang <target language> \
       --source-decimal comma --decimal point --source-letters "…"
   ```
   with each side's decimal convention and letters only the source language uses. It reports
   missing paragraphs, changed tags, numbers lost (always read) or added (usually wording), the
   wrong decimal separator, leftover source letters and, where words are separated by spaces, tags
   glued to a word. For terms and style, use
   `linguisticResources lookupGlossary` and the `checkTranslations` prompt on the field's keys.
   Fix an entry with `manageEntries setTranslation`, `dryRun` first: read it with `entries get`
   and `includeSegments`, and keep every tag -- the paragraph itself is `<g id="_0">`. Then send
   the identical translate call again to fetch the corrected HTML.
5. **Write the file**:
   ```
   python3 scripts/docx_tags.py build in.docx work/translated.html out.docx <target language>
   ```
   A paragraph whose tags did not come back exactly is reported and left in the source language:
   fix it in step 4, never by editing tags in the HTML.
6. **Measure**, when there is an approved translation:
   `python3 scripts/docx_compare.py out.docx approved.docx work/compare.md`. Read differences as
   findings: the approved file can be the one that departs from its source.
7. **Review.** The Workbench lists the document's entries for review along the project's
   workflow. A document stored with kind `file` has no visual preview there.

## The write gate

Every change this skill makes goes through this gate.

<!-- write-gate:start -->
**Before any change**
1. Show what will change: run with `dryRun: true` where the tool has it; otherwise read the
   current value and show before and after.
2. Say what it costs when it re-crawls, re-translates, calls an AI service or deletes.
3. Wait for an explicit yes from the user.
4. Make the change, read it back, and report what is now stored.
<!-- write-gate:end -->

- `manageDocuments translate` has no dry run: it stores the document, counts its words and pays
  for its translation. Name the document, the project and the language, and wait for the yes.
- `manageEntries setTranslation` takes `dryRun`. `confirmed: true` lands a translation on the
  project's final workflow state and saves it to the memory: only on the user's word.
- `aiTranslationConfig testTranslate` stores nothing but pays for every run.

## Pitfalls

- **Word splits text into runs** for spell-checking and revision marks. The converter merges runs
  that look alike, so a document of hundreds of runs needs tens of tags; never count raw runs.
- **The file is not rebuilt.** Only the text of its paragraphs changes; styles, images, links,
  layout and every other part of the file are copied unchanged, and language attributes become the
  target language.
- **Glued tags.** When a tagged part of a source word becomes a word of its own, the tag must move
  onto that word. A tag glued to a neighbouring word is right for a compound in a compounding
  language and wrong almost everywhere else; QA flags it for a look.
- **Numbers are content.** A lost "1" can hide in a glossary entry that maps a phrase to wording
  without the number; QA compares the numbers of every paragraph.
- **Some numbers are fixed in place.** Easyling turns a number that stands alone ("2026" in
  "13 October 2026", a table value) into a placeholder the AI cannot edit, only move. A date or a
  quantity whose order changes in the target can come out in the source's order: read dates.
- **Confirmed over MCP means final**, skipping every review step.

## Report back

1. **Document:** the file, project, target language, paragraphs and tags.
2. **Checked:** the round trip, the pipeline switches, the translation call's status, the QA
   findings and each fix, the build result, the comparison when there was one.
3. **Delivered:** the output path, and what is left: refused paragraphs, untranslated headers or
   notes, and the decisions only the customer can make, in sentences they can be sent.
