# Translation memory

A translation memory holds approved source and target pairs. It belongs to the account that
created it, can hold several target locales, and can be attached to any number of projects.
Keeping and looking up a memory costs nothing extra; machine translation and AI calls do.

## 1. What the project has

- `linguisticResources listProjectResources`: the attached memories, and which one the project
  writes its confirmed translations into. A project has at most one write memory; lookups and
  pre-translation read every attached memory whose locales fit.
- `linguisticResources lookupMemory` with one sentence and a language: the same fuzzy lookup the
  Workbench uses for its suggestions, with the project's penalties: score, source, target and the
  memory's name. `strictLocale` (default true) accepts the exact locale only; false also takes
  related locales, so `de-AT` translations can match `de-DE`.
- `linguisticResources prepareTranslation`: memory matches sentence by sentence, glossary hits and
  the styleguide in one call, for translating a text yourself the project's way.

## 2. Attach

- Create a memory, import a TMX file, export, populate it from the project, clean it up, or search
  it and correct or delete a pair: Dashboard → Translation memory *(no MCP tool)*.
- Attach an existing memory: `manageLinguisticResources assignMemory`, `dryRun` first. Its source
  language must match the project's on the language part (`en-US` and `en-GB` match).
- `makeDefault` decides writes: true makes it the write memory and demotes the current one; false
  attaches it for lookup only; omitted, it becomes the write memory only when the project has none.
- An attached memory is live for lookups and writes at once. Attaching discloses its contents to
  everyone who can reach the project; detaching is in Dashboard → Translation memory
  *(no MCP tool)*.
- On a project served through crest, attaching changes nothing a visitor sees until the content is
  pre-translated again and `manageCrest startExport` has rebuilt the script.

## 3. Match scores

- Matches from 99 to 102 % are reliable; above 100 % the context matches too.
- 98 % ignores tags: the text is right, but the tags may need placing.
- Below 98 % the lookup becomes a word search with stemming. Use such matches with care.

## 4. The memory step of auto pre-translate

Read with `projectSettings get` and `category` `autoPretranslate`; change with
`manageProjectSettings update`, `dryRun` first. None of these is retroactive.

| Setting | Decides |
|---|---|
| `autoTranslateConfig.useMemory` | Whether the memory step runs at all. |
| `autoTranslateConfig.scoreLimitForMemory` | The lowest score used, 0 to 102. |
| `autoTranslateConfig.confirmThresholdEnabled` and `autoTranslateConfig.confirmThresholdForMemory` | Matches at or above the threshold are confirmed with nobody reviewing them. |
| `autoTranslateConfig.strictLocale` | Exact locale only, or every regional variant. |
| `autoTranslateConfig.passUnconfirmedMemory` | Unconfirmed memory fills still go to people for review. |
| `memoryTagAlignHeuristics` | Guesses tag placement from punctuation. |

- **The two thresholds move each other.** Raising the score limit above the confirm threshold
  silently raises the threshold while auto-confirm is on. Set both in one call and read both back.
- An auto-confirmed match with guessed tags goes live unreviewed.

## 5. The memory in AI translation

- With the slot's `memoryTranslationAllowed` on, a memory match goes into the AI's prompt as the
  best translation available, for the AI to adopt and re-tag; the AI's output is what is stored.
- By default (`memoryTranslationMinimumScore` 99) only a near-exact match of the whole entry is
  offered, so fuzzy matches never reach the AI. Lowering it below 98 switches to the slower
  search-based lookup. Read and change it with `aiTranslationConfig getSlot` and
  `manageAiTranslationConfig updateSlot` (see [AI translation](ai-translation.md)).
- `skipMemoryTranslations` on leaves memory-filled entries alone; off, the AI rewrites them and
  each costs an AI call.

## 6. What feeds the memory, and what does not

| Feeds the write memory | Does not |
|---|---|
| Confirming a segment in the Workbench | A draft, saved but not confirmed |
| `manageEntries setTranslation` with `confirmed: true` | `manageEntries setWorkflowState`, whatever state it writes |
| A TMX import, and populating from the project | Search and replace in translations (populate afterwards) |
| | Confirming in the Workbench with its save-to-memory dropdown set to not save |

- **Edits that must not be reused** (SEO keywords, a one-off legal wording): confirm them in the
  Workbench with the save-to-memory dropdown set to not save. Nothing marks such a translation,
  so populating the memory from the project later stores it anyway. Populate deliberately (a new, empty memory, or after a bulk search and replace), not as a routine.

- A wrong translation once confirmed stays in the memory and comes back with the next match.
  Correct the stored translation, confirm the corrected text, then check with
  `linguisticResources lookupMemory` which version the memory offers; remove a bad pair in
  Dashboard → Translation memory *(no MCP tool)*.

## 7. Pitfalls

- **The right project.** One site often has several projects (staging, an older copy). A memory
  attached to or populated in the project that does not serve the live site changes nothing there.
- **A memory is not retroactive.** Attaching or improving one changes future pre-translation only;
  stored translations stay until re-translated.
- **Locales at both ends.** A memory without the project's target locale offers nothing for it.
  Add the locale to the memory before populating or importing: Dashboard → Translation memory
  *(no MCP tool)*.
