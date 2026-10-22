# Glossary

A glossary maps source terms to approved translations, per target language. It belongs to the
account that created it and is attached to projects. The AI and the machine translation engines
never read the glossary itself: they read its **published** copy, one per engine and language.

## Contents

1. What the project has, and what the engine sees
2. Attach and publish
3. Terms
4. Sentence entries are patterns, not noise
5. Data quality first
6. Access

## 1. What the project has, and what the engine sees

- `linguisticResources listProjectResources`: the attached glossaries (code, name, languages,
  `editable`) and `publishedGlossaryTargets`, the engine and language pairs that hold a published
  copy. A language missing there is translated without any glossary, however many terms are
  attached. `includeSharing` adds which other projects hold the same glossary: an edit reaches
  them too.
- `linguisticResources lookupGlossary` with a sentence and a language: the terms that apply. It
  reads the glossaries as they are now, not as last published, and uses a broader matcher than the
  engine. A hit with `matchedByEngine: false` is a term the AI cannot see even once published: the
  engine's matcher reads ASCII letters only, knows English plurals and does no stemming. Accented,
  non-Latin and inflected terms are the usual victims; add the form the source really uses, or a
  styleguide rule.
- A hit's description and example sentences tell apart entries that share a source term.
- `aiTranslationConfig testTranslate` with `includeUserPrompts` shows which pairs actually reached
  the AI for one sentence, and `includePublishedGlossary` the whole published copy (paid).
- The AI reads the published glossary only while the slot's `usePublishedGlossary` key is on
  (`aiTranslationConfig getSlot`).

## 2. Attach and publish

- Create a glossary: `createLinguisticResources createGlossary` with a `name`, `dryRun` first. It
  is created empty, in the project's source language, set up for the project's target languages
  (or only the `targetLanguages` named) and attached to the project in the same call, after every
  glossary the project already holds. Names are not unique, and a glossary can be neither deleted
  nor detached over MCP: read `listProjectResources` first and name it deliberately. Then add
  terms (section 3) and publish (below).
- Import or export a glossary's terms (CSV), add a target language to it later, change its default
  case sensitivity: Dashboard → Glossary *(no MCP tool)*. The same page detects term candidates
  and fills missing translations with AI.
- Attach an existing glossary: `manageLinguisticResources assignGlossary` with the code
  `listProjectResources` reports on a project that has it, `dryRun` first. Attaching is a
  disclosure: everyone who can reach the project can read the terms. A new attachment ranks after
  every glossary already there. Detaching and reordering: Dashboard → Glossary *(no MCP tool)*.
- **Copying a project's glossaries to another project**: read the source project's order with
  `listProjectResources` and assign the glossaries one per call in that order, so they keep their
  ranks among themselves. Glossaries the target already held keep the front of the list; if the
  source's order must win over them, reorder in Dashboard → Glossary *(no MCP tool)*. Then
  publish once (below).
- Publish: `manageLinguisticResources publishGlossary`, `dryRun` first. Without `glossaryCode` it
  publishes every attached glossary combined, in rank order, to every engine the project holds
  credentials for, in every language the glossaries hold. That is the safe default: an engine keeps
  one published copy per language and each publication replaces it, so publishing one glossary
  alone drops the others' terms. `publishOnlyConfirmed` leaves out unconfirmed terms;
  do-not-translate terms are published either way.
- Publishing runs in the background. Read `listProjectResources` until the target appears; until
  then `manageDocuments translate` reports the glossary as `assignedButUnpublished`.
- Publishing needs an engine that takes a glossary, with the project's own credentials: an AI
  engine with an API key, or an enabled machine translation engine. Without one the call refuses;
  credentials are set in Dashboard → MT engines *(no MCP tool)*.
- When two attached glossaries hold the same source term, rank decides; some engines accept only
  one entry per source term.
- The published copy is per engine. After the AI engine changes (`aiEngine`) or a new engine gets
  credentials, check `publishedGlossaryTargets` and publish again if the new engine is missing.

## 3. Terms

- One term per call: `manageGlossaryEntries add`, `manageGlossaryEntries update`,
  `manageGlossaryEntries delete`. Each takes `dryRun` and reports the entry before and after.
- **Nothing a term edit stores is live.** Publish once after the batch, then test.
- **Identity is source + description + example sentence.** The same source with another
  description is a second entry, and both are published, so the AI sees two contradicting
  `source => target` lines. One meaning, one entry. `update` and `delete` refuse to guess between
  entries of one source; `description` and `exampleSentence` select one.
- **Descriptions never reach the AI.** Example sentences reach it only when the slot's prompt
  template prints `{{exampleSentence}}`, which the stock template does not (templates are edited in
  the dashboard). Even printed, they did not make the AI choose reliably between two entries of one
  word in testing. Give the entry the wording the usual context needs, and handle the exception
  with a sentence entry or a styleguide rule.
- The source text cannot be changed: delete the term and add it again.
- `doNotTranslate` publishes the source as its own translation in every language: brand, product
  and company names. `caseSensitive` defaults to the glossary's setting.
- A term with no translation for a language matches nothing there, unless it is do-not-translate.
- **Short terms are a hazard.** A one- or two-letter term or a stopword matches nearly every
  sentence. Remove such entries.

## 4. Sentence entries are patterns, not noise

- Glossaries often hold whole phrases and sentences: approved wording for recurring sentences.
  They are deliberate, so never prune them as noise. The review prompts mark a near match with ≈
  and a score: the AI should adapt the pattern to the sentence in front of it, not copy it.
- **A concrete sentence mapping beats a general rule.** A sentence entry that lists fewer items
  than the source (ingredients, allergens, features) makes the AI drop the extra items, whatever
  the styleguide says three sections away. For list-bearing sentences, keep the items as separate
  terms and one wording skeleton, and check completeness when reviewing.
- Never tell the styleguide to copy glossary sentences verbatim. Say the pattern is adapted to
  what the source lists, and that the source wins where the two differ.
- Wording that is a legal matter belongs in the translation memory as an exact match, with human
  review, rather than in the glossary alone.

## 5. Data quality first

- A better matcher delivers bad data more faithfully: a typo in a target comes back in every
  translation. Before tuning anything else, read the terms the problem sentences hit and fix wrong
  targets, duplicates and contradicting entries.
- Then publish, then rerun `aiTranslationConfig testTranslate` on the same examples.
- Stored translations keep the old wording until they are re-translated or corrected (see
  [reviewing translations](reviewing-translations.md)).

## 6. Access

- Reading a project lets you read every glossary attached to it.
- Creating a glossary on a project needs the right to edit the project; the glossary then belongs
  to the account the MCP connection was authorised with.
- `manageGlossaryEntries` is authorised by the right to edit the project the glossary is attached
  to; a glossary the project does not hold cannot be reached through it.
