---
name: linguistic-quality
description: Use when the wording of Easyling translations is the question - glossary, terminology, translation memory, styleguide, tone and formality, AI or machine translation, ContentGuard, review.
compatibility: Needs the Easyling MCP server
---

# Linguistic quality

Make a project's translations say what the customer wants: the right terms, the right tone,
approved translations reused, an AI configuration that produces all of that, junk kept out before
it costs anything, and stored translations checked and corrected. The MCP reads and changes
glossaries, memories, styleguides, the AI configuration and ContentGuard, and corrects stored
translations; every change goes through the write gate below.

## When to use

- **Terminology**: a glossary term ignored, inconsistent or wrong terms, names that must stay in
  the source language.
- **Reuse**: translation memories, their matches, what is saved into them.
- **Style**: the styleguide per language, tone and form of address, formats.
- **The machines**: which steps run (memory, machine translation, AI), the engine and model, the
  prompts, the quality and the cost of AI translation.
- **ContentGuard**: junk, foreign-language or personal text entering the project, and its
  verdicts.
- **Review**: checking stored translations against the project's rules, correcting them,
  recording or resetting review, "is it done?".

Hand-offs. Setting up or publishing a site (the project, languages, path rules, collecting
content, serving, crest exports) belongs to the onboarding skill. Translating a Word document
with its formatting belongs to the translate-docx skill. Something that used to work and
no longer does, such as pages that stopped translating or old text on the live site, is a fault:
send it to Easyling support, or to a triage skill if one is installed. When the skill for a step
is not installed, describe the step instead of making it.

## Intake

Establish these first, and ask for whatever the request leaves out.

0. **Which Easyling installation the MCP reaches.** A project lives on one installation (the
   main one or a white-label one), and the MCP sees only the installation it is connected to. The
   connection this plugin ships with is a development installation that holds test projects
   only. Until the customer's installation is connected, work in that installation's dashboard and
   Workbench: every MCP step below is then a check or a change for someone with access to make
   there. Never read "not found" on the wrong installation as "does not exist".
1. **The project.** `projects list` gives its code and source locale. One site often has several
   projects (staging, an older copy): confirm the one that serves the content in question, because
   a resource fixed in another project changes nothing on the live site.
2. **Target languages**, as locales. AI configuration slots are filed under the exact spelling
   `aiTranslationConfig listSlots` reports.
3. **The problem or the goal, with examples**: two or three source texts, what each says now, what
   it should say, and where it shows. Each example becomes an entry key to test against.
4. **Who decides wording**: the customer's approved terms, styleguide or reviewer. Never invent
   terminology or tone rules; propose them and let the customer decide.
5. **Budget**: AI tests, classification and re-translation are paid per call.

## How a translation is decided

Auto pre-translate runs on newly collected content while
`autoTranslateConfig.autoPretranslateEnabled` is on, entry by entry and language by language:

1. **ContentGuard**, when enabled, may leave the entry untranslated (EXTERNALIZED) or mark it
   for review (PENDING). A PENDING entry is still translated by the steps below and served;
   it goes into a separate pending work package, and work package (XLIFF) exports leave it out
   until approved. A crest export includes it.
2. **Translation memory** fills in a match above the threshold, and may confirm it.
3. **Machine translation**, the first listed engine that handles the language pair.
4. **AI translation** (post-editing), when switched on and the language's configuration slot
   resolves enabled: the AI translates or rewrites with the styleguide, the published glossary
   terms found in the text and, where the slot allows it, a memory match; a validator scores the
   result.
5. **People** review in the Workbench along the project's workflow, or through XLIFF.

Two consequences shape every fix:

- **A resource change affects future translations only.** Stored translations stay until they are
  re-translated (Dashboard → Pre-translate *(no MCP tool)*) or corrected.
- **The AI reads published copies.** A glossary edit is not seen until published; a styleguide is
  read per slot; by default only a near-exact memory match is offered, never a fuzzy one.

The tool texts hold the configuration cascade (`aiTranslationConfig`), the export list
(`entries`, `manageEntries`) and workflow states (`entries`), with each call's traps in the
texts of the fields it uses.

## Where to look

| The request is about | Read |
|---|---|
| Terms ignored or wrong, names translated, a glossary to create, attach, publish or clean up | [glossary](references/glossary.md) |
| Memory matches, reuse, a memory from another project, what gets saved | [translation memory](references/translation-memory.md) |
| Tone, form of address, formats, style rules | [styleguide](references/styleguide.md) |
| Which steps run, engine and model, prompts, AI quality or cost, re-translating | [AI translation](references/ai-translation.md) |
| Junk or personal text collected, ContentGuard verdicts and setup | [ContentGuard](references/contentguard.md) |
| Checking, correcting, confirming translations; workflow and source status | [reviewing translations](references/reviewing-translations.md) |

## Diagnosing a wrong translation

Work through these in order, and say what each step showed.

1. **Find it.** `entries search` for the text in that language (check `exportListFresh`), then
   `entries get` with the key and `targetLanguage` for the stored translation and its state.
2. **Stored or served?** If the stored translation is right and the site shows something else,
   it is a serving or caching fault: hand it off.
3. **Where it came from.** The Workbench shows each translation's origin and history:
   Workbench → the entry's flag and History *(no MCP tool)*. A human or memory origin points at
   the memory and the reviewers; machine or AI points at the configuration.
4. **Replay it.** `aiTranslationConfig testTranslate` with the source and `includeUserPrompts`
   (paid, stores nothing): which memory match, glossary pairs and styleguide reached the AI, what
   it produced, and the validator's score. Use `runs` to see the spread.
5. **Narrow it.** A term not offered: [glossary](references/glossary.md). A rule ignored: the
   `reviewStyleguide` prompt and [styleguide](references/styleguide.md). The AI not running, or the
   wrong engine: [AI translation](references/ai-translation.md). A memory pair: [translation
   memory](references/translation-memory.md).
6. **Fix the cause, test, then the stored text.** Change the resource through the gate, replay the
   same examples, then correct what is stored: the `checkTranslations` prompt on the affected keys,
   then `manageEntries setTranslation`, or a re-translation of the scope.

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

- **Dry runs** exist for `manageGlossaryEntries` (all three actions),
  `createLinguisticResources createGlossary`, `manageLinguisticResources assignGlossary`,
  `manageLinguisticResources assignMemory`,
  `manageLinguisticResources publishGlossary`, `manageProjectSettings update`,
  `manageEntries setTranslation`, `manageEntries setWorkflowState`, `manageEntries setSourceStatus`,
  `manageContentGuard setPrompt`, `manageContentGuard setConfiguration` and
  `manageContentGuard classifyAndApply`.
- **Dry runs that cost the same as the change**: `manageAiTranslationConfig updateSlot` and
  `manageAiTranslationConfig addSlot` run one live test translation either way;
  `manageContentGuard classifyAndApply` bills every key either way.
- **No dry run**: `manageLinguisticResources saveStyleguide` overwrites the slot whole, so read it
  with `linguisticResources getStyleguide` and show before and after.
  `manageContentGuard startClassification` costs one AI call per entry, with no undo.
  `manageEntries delete` removes entries from every language and is not a correction.
  `manageDocuments translate` stores content, counts its words and spends on its translation.
  `manageWorkPackageSets createFromKeys` creates a set that cannot be deleted over MCP; name it
  deliberately. `manageEntries rebuildExportList` rebuilds the export list in the background.
- **Costs to name**: `aiTranslationConfig testTranslate` (every AI call of the pipeline, times
  `runs`), `contentGuard classifyText` and `contentGuard classifyEntry` (one AI call each), any
  slot write, and switching on auto pre-translate, AI translation, a machine translation engine or
  ContentGuard, which spends on every new entry from then on without asking again. A dashboard
  re-translation pays for every entry in scope.

## Pitfalls

- **The data beats the matcher.** A typo or a contradicting entry in the glossary comes back in
  every translation; fix the data before tuning prompts or models.
- **Attached is not published.** A glossary nobody published is invisible to the AI and to the
  machine translation engines, however many terms it holds.
- **Sentence-length glossary entries are deliberate.** They are approved patterns for the AI to
  adapt; never prune them as noise.
- **A language styleguide replaces the `*` one**, it does not extend it.
- **`*` index 0 reaches every language** that pins nothing of its own; write the language slot
  when one language is meant.
- **The test path is not the production path.** `aiTranslationConfig testTranslate` needs only a
  slot that resolves enabled; new content also needs the auto pre-translate switches.
- **Credentials do not choose the AI engine.** Unpinned, the first engine with a key in a fixed
  order runs, not the one loaded last. Pin `aiEngine` and `aiModel` on `*` index 0 (OpenAI
  recommended) and read "Effective AI" in the `testTranslate` log: `getSlot` and `listModels` do
  not show what runs ([AI translation](references/ai-translation.md), section 3).
- **The AI is not deterministic.** Judge a change on several runs and several examples.
- **Prompts are started by the user**, as slash commands, with arguments separated by spaces.
- **Confirmed over MCP means final.** `confirmed: true` skips every intermediate review step and
  saves to the memory; use it only when the user says the text is approved.
- **Stored is not live on crest.** New translations reach visitors after `manageCrest startExport`
  (sooner where `enableCrestMissingFetch` is on).
- **A token count of 0** over MCP means "not reported", not "free".
- **Read-only over MCP does not mean unchanged.** Much of this configuration is edited in the
  dashboard at any time; read it before relying on it.
- **"Project is not accessible"** for a project created after you connected: reconnect the MCP
  (in Claude Code, `/mcp`).

## Report back

Answer in this shape:

1. **Request:** the project, languages, and the example keys with what they say now and should say.
2. **Checked:** each tool call, prompt or dashboard check, and what it showed.
3. **Cause:** which step produced the wording, and why, or what is still unproven.
4. **Changed:** each write, what is now stored, and the paid calls made.
5. **Open:** re-translation or review still needed, crest exports, and the decisions only the
   customer can make, in sentences they can be sent.
