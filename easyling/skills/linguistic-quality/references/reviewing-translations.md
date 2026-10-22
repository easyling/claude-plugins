# Reviewing and correcting translations

Find the stored translations in question, check them against the project's own rules, correct the
ones that break a rule, and record how far review got. Fix the resource first when the same rule
breaks everywhere: correcting entries one by one does not stop the next translation repeating the
mistake.

## Contents

1. Find the entries
2. Check them: the `checkTranslations` prompt
3. Correct them: `manageEntries setTranslation`
4. Workflow states: how far review got
5. Source status: whether an entry is translated at all
6. Not a correction

## 1. Find the entries

- `entries search` in one target language, with `query` and then `exact` or `regexp` to keep only
  real hits. The index works on words: `run` does not find `running` unless written `~run`, and
  punctuation is not searchable. Keep calling with `cursor` while `hasMore` is true, even after an
  empty page.
- **Check `exportListFresh` and the warnings first.** Search works from each language's export
  list: content collected since its last rebuild cannot be found, and deleted entries keep coming
  back. `manageEntries rebuildExportList` repairs it (safe to repeat; it reports `started`, then
  `alreadyGenerating`, then `alreadyFresh`). A project that turned entry indexing on late finds
  fewer candidates than it holds, and the warnings say so.
- `entries get` with the keys and `targetLanguage`: source, translation, source status,
  `workflowState`, `atFinalWorkflowState` and whether the entry is visible. `includeSegments` adds
  the segment shape a segmented correction must match.
- `entries listByPage` with `path` and `kind`: every entry of one page, read directly, including a
  document sent with `manageDocuments translate`. At most 1000 entries.
- `workPackageSets getContent` reads the entries of a set, for example the Low Score set of an AI
  run started from the dashboard, with `targetLanguage` for the translations.
- To hand a list of keys to people in the Workbench or to an XLIFF export,
  `manageWorkPackageSets createFromKeys` makes a set of them. Every call creates a new set, and
  sets cannot be deleted over MCP.

## 2. Check them: the `checkTranslations` prompt

- The `checkTranslations` prompt carries the method. It embeds, for up to 10 keys, the styleguide
  the engine read, the engine's validation criteria and the published glossary terms per entry,
  marking terms the engine never saw. Every proposed edit cites the rule that requires it; where
  two rules conflict it reports the conflict instead of choosing; block entries keep their markup;
  numbers and units change only when a rule says so. It writes nothing.
- Only the user can start it. Arguments are separated by spaces: the project code, the target
  language, then the keys as one comma-separated list with no spaces, and optionally a focus such
  as `terminology`.
- For many entries, check a sample of 10 first. If one rule fails everywhere, fix the glossary,
  styleguide or configuration, and re-translate the scope rather than correcting by hand.
- In a client without prompts, apply the same discipline: cite the rule for every edit, and leave
  everything no rule requires.

## 3. Correct them: `manageEntries setTranslation`

- Run it with `dryRun: true`, show the result, wait for the yes, then run it for real and read the
  entries back with `entries get`. At most 100 translations per call, one language per call.
- Each translation gives `target` (the whole entry) or `targetSegments` (one per source segment,
  on a project that segments). Each segment keeps its own source segment's tags; a tag may open in
  one segment and close in a later one. Read the shape with `entries get` and `includeSegments`.
- **Block entries keep their markup.** Inline tags that do not match the source's send the entry
  to `skipped`.
- **`confirmed: true` only on the user's word.** It lands the translation directly on the project's
  final workflow state, skipping intermediate steps and roles, and saves it to the translation
  memory. `confirmed: false` stores a draft and removes every workflow state.
- A text identical to the stored one writes nothing, tags included. To turn a translation stored
  as one run back into segments, it therefore takes two writes.
- `skipped` lists LOCKED and EXTERNALIZED entries; `unmatched` lists keys of another project.
- Writing needs the Workbench's right to edit entries in that language, which a reviewer-only role
  lacks.
- Unless the project publishes by hand, the proxy serves the new translation at once; on crest it
  reaches visitors after `manageCrest startExport` (sooner where `enableCrestMissingFetch` is on).
- **Let the requester check it in context**: send the page in the `-p` preview (proxy) or the `-v`
  preview (crest), which show the stored translations without waiting for caches or an export.
- **An outside reviewer must sign off before visitors see a translation**: that is manual
  publishing, set up with the onboarding skill. There is no PDF export of translated pages; the
  reviewer's copy is the preview printed to PDF from the browser.
- A translation that was ever machine-translated keeps that origin after a human edit.
- **Bulk wording changes** (a renamed product across hundreds of translations): Dashboard → Search
  and replace *(no MCP tool)*. Do a test run first; it cannot be undone, and it does not update the
  translation memory (populate the memory afterwards). Over MCP, the same is search plus
  `setTranslation` in batches, each through the gate.

## 4. Workflow states: how far review got

- A translation carries a review state per language, and on segmented translations per segment:
  NEW (nothing confirmed), S1, S2, S3 (an earlier step's confirmation), an -EDITED state (edited
  since that confirmation), FINAL (the last step's). Which ones a project uses follows its
  workflow: translation, then optionally proofreading, a quality check and client approval.
- The workflow is chosen in Dashboard → Project overview *(no MCP tool)*, and who holds which
  role in Dashboard → Sharing *(no MCP tool)*.
- **"Is it done?" is `atFinalWorkflowState`, nothing else.** A segmented translation keeps its
  state per segment and leaves `workflowState` at NEW, and the per-segment list can read FINAL on a
  half-confirmed entry.
- `manageEntries setWorkflowState` records, withdraws or resets review without touching the text,
  `dryRun` first. It writes any state directly, checks no role and writes nothing to the memory;
  NEW withdraws every confirmation.
- The Workbench's confirm is relative: one step forward for the acting role. The MCP writes are
  absolute. Say which one a reported state came from.

## 5. Source status: whether an entry is translated at all

- APPROVED is translated and served. PENDING marks the entry for review: auto pre-translate still
  translates it and it is served, crest exports included; only work package (XLIFF) exports,
  external submissions and exports run with "skip pending" leave it out until it is approved.
  EXTERNALIZED is served in the source language in every language. The status belongs to the
  entry, never a segment, and is shared by every target language.
- Change it with `manageEntries setSourceStatus`, `dryRun` first. It takes effect at once on the
  proxy. On a crest project an entry set to EXTERNALIZED stays translated until
  `manageCrest startExport`, which always leaves EXTERNALIZED entries out; a dashboard export
  does so only with "Skip excluded segments" ticked. It needs the right to edit source status,
  which a translator may not hold.
- ContentGuard writes the same status and a later run may overwrite a manual change (see
  [ContentGuard](contentguard.md)).

## 6. Not a correction

- `manageEntries delete` removes the source entry from every target language, cannot be undone,
  and finishes in the background; collecting the page again brings the text back as new words.
- **Deleting and verifying it**, each write through the gate:
  1. `manageEntries delete` with the keys. It returns once the deletion is queued; on a large
     project the scan takes several minutes, with no completion signal. Do not repeat the call
     to check on it: that queues another scan.
  2. Once it has had time to finish, `manageEntries rebuildExportList` for every target language
     of the project. A deleted entry keeps coming back from `entries search` until its language's
     export list is rebuilt.
  3. Call `rebuildExportList` again for each language until it reports `alreadyFresh`.
  4. Only then `entries search` to verify: the deleted keys no longer come back.
- Sending the same content again with `manageDocuments translate` reuses the stored translation:
  it does not translate again.
- Changing a glossary, memory, styleguide or AI setting changes future translations only.
