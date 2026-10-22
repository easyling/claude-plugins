# ContentGuard

ContentGuard screens new content before anyone pays to translate it. Per entry it decides
APPROVED (translate), PENDING (translate and serve, but flag for review) or EXTERNALIZED
(leave untranslated), and writes that
as the entry's source status. It suits crest projects and sites with dynamic or user-generated
content, where scripts, browser extensions, error messages, foreign-language or personal text
otherwise become source entries.

Its inputs are language detection, a nearest-neighbour search against an index of the project's
known-good content, and an AI prompt. An evaluation script turns them into the verdict.

## Contents

1. Setting it up
2. The prompt and the evaluation script
3. Classifying, in increasing commitment
4. Reviewing and correcting verdicts
5. Costs

## 1. Setting it up

- **Ask Easyling support first.** The project needs preparing before ContentGuard can be enabled.
  Then Dashboard 3 → ContentGuard configuration *(no MCP tool)* holds the strictness slider, the
  allowed languages and the index training (Index project).
- **The index is the ground truth.** Train it only on content you have checked, typically a work
  package from a clean crawl. Polluted ground truth (pages that echo query parameters into the
  text, server error messages) makes look-alikes pass. Train it again after people have approved
  pending entries, so their decisions count.
- **Non-Latin scripts** are handled poorly by the neighbour search; add language detection for
  such sources.
- Read the configuration with `contentGuard getConfiguration` (free): `enabled`,
  `classifierEnabled`, `loadSourceEntryStatus`, `languageDetectionService`, `embeddingVersion`,
  `aiService`, `aiModel`, `aiTemperature`, the prompt (`aiPrompt`) and `evaluationScript`, plus the
  accepted `aiServices` and `languageDetectionServices`.
- Change any subset with `manageContentGuard setConfiguration`, `dryRun` first; fields not given
  stay as they are. A working setup can be read on one project and written onto another as it
  stands.
- **Switching `enabled` on starts spending.** On a project with auto pre-translate on, every newly
  collected entry is classified from then on, one AI call each. A project with no evaluation script
  of its own runs the built-in one, which approves everything and still pays.
- **`classifierEnabled` needs a trained index.** Without one every classification fails after
  its AI call, which is billed and then discarded; a
  background run stops at its first entry yet still sends the "Classification finished" e-mail,
  which is therefore no evidence. With it off, an untrained index is inert.
- `aiService` must be one of `aiServices` and needs credentials, or the AI step silently returns
  nothing. `aiModel` is not checked: a wrong name fails at the first classification. Set
  `aiTemperature` together with the model, since some models accept only 1.
- `languageDetectionService` must be one of `languageDetectionServices`; it uses a machine
  translation engine of the project and may add that engine's charges.

## 2. The prompt and the evaluation script

- The prompt is Mustache and must contain `{{{source}}}`; it may use the other placeholders
  `getConfiguration` lists in `promptVariables`, such as `{{sourceLanguage}}`,
  `{{targetLanguage}}`, `{{sourceHTMLTag}}` and `{{sourceHTMLClasses}}`. Ask for strict JSON with
  `score`, `detected_language`, `detected_language_confidence` and `reason`, which is what the
  standard script reads. `manageContentGuard setPrompt` replaces it whole: read it first.
- **Prompt design, not the model, is the weak point.** A bare "is this in the source language?"
  approves source-language debris (log lines, ids, code) at full score. A rule such as "mentions
  the brand, so approve" can outrank the language check and approve foreign text. Gate on the
  detected language first, and phrase personal data as visitor or customer data, so that authors,
  characters, staff and brand names do not trip it.
- The evaluation script is JavaScript up to ES2015. It is parsed, never run, before saving, and
  returns `approved`, `pending` or `externalized`.
- **A broken script approves everything, silently.** A script that throws or returns anything else
  gives no verdict, and no verdict counts as APPROVED. A blank script reverts to the built-in one.
  There is no staging: the next classification uses the new script.
- Replacing the standard script hides the dashboard's strictness controls.

## 3. Classifying, in increasing commitment

1. `contentGuard classifyText` on sample texts and `contentGuard classifyEntry` on real keys: one
   AI call each, nothing written, and they work on a disabled project. `verbose` shows the prompt
   as sent.
2. `manageContentGuard classifyAndApply` with `dryRun`: up to 10 keys, or the first 10 entries of
   a scope with `nextCursor` for the next sample. Still billed. Without `dryRun` it writes the
   verdicts, and only while ContentGuard is enabled.
3. `manageContentGuard startClassification` over a work package set or the whole project: in the
   background, one AI call per entry, minutes long, no progress query and no undo; an e-mail
   arrives when it ends. One MCP-started run at a time.

- The tuning loop: read the configuration, change the prompt (`dryRun` first), classify samples of
  both good content and junk, classify known keys, classify a sample of the scope with `dryRun`,
  and only then start the full run.
- Read outcomes with `workPackageSets getContent`, asking only for `sourceStatus` in `fields`.
- **A verdict is an observation, not a proof.** The same text can classify differently twice.
  `loadSourceEntryStatus` makes a verdict depend on the neighbours' statuses, so dry-run verdicts
  stop being reproducible once a real run has moved them.

## 4. Reviewing and correcting verdicts

- Pending entries are reviewed in the Workbench: Workbench → Show pending entries
  *(no MCP tool)*, where people with the right role approve or exclude them.
- Correct a verdict with `manageEntries setSourceStatus`, `dryRun` first. The status belongs to the
  entry and is shared by every target language; EXTERNALIZED hides the translation in every
  language, on the proxy at once and on crest with the next `manageCrest startExport`, and
  PENDING only marks the entry for review: it is still translated and
  reaches crest visitors with the next export; only work package (XLIFF) exports leave it out.
- **A later run may undo a manual correction**: a classification run decides from the current tag
  alone.
- **Switching ContentGuard off clears nothing.** Entries already EXTERNALIZED stay hidden until
  `manageEntries setSourceStatus` restores them.

## 5. Costs

- Every classification is one AI call, plus language detection where it is on. `classifyText`,
  `classifyEntry` and a `classifyAndApply` dry run are billed like real runs; a background run
  costs one call per entry in scope.
- Blank text, and text containing the Easyling application's own address, come back EXTERNALIZED
  with no AI call.
- `contentGuard getConfiguration` is free.
