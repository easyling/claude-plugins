# AI and machine translation

Two layers decide what the machines do. The project's auto pre-translate switches decide which
steps run on new content; the AI configuration (what the server stores as automatic post-editing,
APE) decides how the AI step translates. The `aiTranslationConfig` tool text describes the
configuration cascade; this file is the process around it.

## Contents

1. Which steps run
2. The configuration: slots and the cascade
3. Engine, model and temperature
4. Prompt templates
5. Testing: `aiTranslationConfig testTranslate`
6. Validation and the correction loop
7. Re-translating stored content
8. Costs

## 1. Which steps run

Read with `projectSettings get` and `category` `autoPretranslate` (add `verbose` for what each
does); change with `manageProjectSettings update`, `dryRun` first.

| Setting | Decides |
|---|---|
| `autoTranslateConfig.autoPretranslateEnabled` | The master switch: new content runs through the steps by itself. With machine translation or AI among them it spends as content arrives, with no further confirmation. Not retroactive. |
| `autoTranslateConfig.useMemory` | The memory step (see [translation memory](translation-memory.md)). |
| `autoTranslateConfig.machineTranslationServices` | The machine translation engines, in priority order: the first that handles the language pair runs. `add` appends. Listing an engine does not configure it. |
| `autoTranslateConfig.useAutomaticPostEditing` | The AI step. |
| `autoTranslateConfig.automaticPostEditingConfigurationIndex` | Which configuration index the AI step uses. Nothing checks that it exists. |
| `autoTranslateConfig.partitioningForMachineTranslation`, `autoTranslateConfig.partitioningForAutomaticPostEditing` | Always, never, or only where a rule does or does not match. |
| `autoTranslateConfig.useAutomaticPostEditingForClasses.mustHave` and `.mustNotHave` | Limit the AI step to, or keep it away from, HTML classes; the memory and machine translation steps have the same pair. |
| `autoTranslateConfig.passMachineTranslation` | Machine translations still go to people for review, instead of counting as final. |

- **Who obeys the switches.** The unattended run and `manageDocuments translate` obey all of
  them. `aiTranslationConfig testTranslate` and the Workbench's Suggest with AI need only a slot
  that resolves enabled. "The test is good but new content gets no AI translation" therefore
  usually means `useAutomaticPostEditing` or the master switch is off.
- Engine credentials (machine translation and AI API keys) are set per engine in Dashboard → MT
  engines *(no MCP tool)*. For OpenAI and Gemini, start from
  `manageAiTranslationConfig loadAccountCredentials`, the engine page's Load from account: it
  copies that engine's key and settings, its model among them, from your account into the
  project, replacing what the project held for that engine. It is free, `dryRun` previews it, and
  it refuses when the account holds no key. Type a key in only where the account holds none; load
  other engines' credentials on the engine page. `aiTranslationConfig listModels` says whether the
  project holds a key for each AI engine.
- **A new project, before the master switch goes on**: load the credentials from the account, pin
  the AI engine and check what runs (section 3), test the domain's vocabulary (section 5), and
  only then switch `autoPretranslateEnabled` on.

## 2. The configuration: slots and the cascade

A slot is a target language, or `*` for every language, and an index. A key the slot does not set
comes from `*` at the same index, then from `*` index 0, then from the installation default.

- `aiTranslationConfig listSlots`: the slots, whether the pipeline calls the AI at all,
  `activeConfigurationIndex`, and hashes per slot. To compare two projects, compare the hashes
  first: where `slotHash` and `resolvedHash` match, there is nothing to read, and `getSlot` is
  needed only for the slots that differ.
- `aiTranslationConfig getSlot`: every key, its state, what it resolves to and which level
  supplied it, plus `apeMode`, one word for what the pipeline does there. `state` with `set` and
  `cleared` shows what the slot decides itself; `key` reads one key in full; `verbose` explains
  each key.
- **A sparse slot is normal.** Most keys are inherited; read what a slot resolves to, not what it
  stores.
- **A write to `*` index 0 reaches every language** that pins nothing of its own. Each change's
  `affectedSlots` counts the coordinates it moved. Write a language slot when one language is meant.
- **Where a language has no slot at index N, its index 0 stands in wholesale.** Creating a slot
  there with `manageAiTranslationConfig addSlot` (index 0 to 4, a name required) ends that, and can
  move dozens of resolved values. Compare `getSlot` before and after.
- **Coordinates are exact strings.** `ja-jp` and `ja-JP` are two slots. Pass a language exactly as
  `listSlots` spells it.
- **Set, inherited or cleared.** `manageAiTranslationConfig updateSlot` pins a key (`op` `set`) or
  unpins it (`op` `inherit`). A cleared key blocks inheritance; clearing a key, returning it to
  inheritance and removing a slot are done in Dashboard → AI translation *(no MCP tool)*.
- Pass `expectedSlotHash` from the last read, so a concurrent edit is refused rather than
  overwritten.

## 3. Engine, model and temperature

- **Recommended engine: OpenAI.** It is the only engine the slot's `costPreference` reaches (the
  OpenAI service tier: `lowestPricesPossible` trades a slower answer for roughly half the cost).
  Load its credentials from the account (section 1), then pin it as below. Where the account
  holds no OpenAI key, ask for one, or pin the engine it does hold.
- **Credentials do not choose the engine.** Where no slot pins `aiEngine`, the run starts from
  the first AI engine that holds a key, in a fixed order: the installation default's engine, then
  openai, deepseek and gemini, so gemini → openai → deepseek where the default is Gemini. That
  engine's credentials also supply the model and temperature. Loading a key for an engine later
  in the order changes nothing, and neither does a slot saved in the dashboard without engine
  keys. `manageAiTranslationConfig loadAccountCredentials` reports the engine that then runs as
  `effectiveEngine` and warns when it is not the one loaded. `aiTranslationConfig getSlot`
  resolves `aiEngine` and `aiModel` from the installation default, before the credentials apply,
  so only the `testTranslate` log shows what runs (section 5).
- `aiTranslationConfig listModels` (free): for openai and gemini, whether the project holds a key,
  the default model and the models offered. Only those can be set. The default model is the one
  that engine's credentials name, not the one that runs.
- **Pin the engine on `*` index 0**: `aiEngine` (`openai`), `aiModel` and `temperature` in one
  `manageAiTranslationConfig updateSlot`, with `expectedSlotHash` from the last read. Use
  `addSlot` only where no slot stands there; it refuses an existing one. The luna models accept
  only temperature 1. A model goes verbatim to whichever engine resolves, and a model no slot
  sets comes from the credentials, possibly another provider's. Unpinned, a project can fall back
  to a default model the installation has retired, and every AI run then fails with an engine
  error and zero tokens.
- Try the combination first: `aiTranslationConfig testTranslate` with `overrides` on the three
  keys. Each call it lists names the engine it reached and the model it asked for. After the
  save, run one `testTranslate` without overrides and read its "Effective AI" line.
- **Every save costs an AI request, and so does its dry run.** The save runs one live test
  translation and refuses the write when it fails.
- After an engine change, check that the glossary is published for the new engine
  (see [glossary](glossary.md)).
- **An AI failure with zero tokens is usually configuration**: a retired model name or missing
  credentials. `getSlot` shows `aiEngine`, `aiModel` and `resolvedEngineHasCredentials` as the
  slots resolve them; the `testTranslate` log shows what the run used.
- The per-stage engines, models and temperatures (post-editing, validation, correction) and the
  retry keys are readable here and changed in Dashboard → AI translation *(no MCP tool)*.

## 4. Prompt templates

- A slot has seven prompt templates. The styleguide is the one writable over MCP
  (see [styleguide](styleguide.md)); the other six (batch context, block context, glossary,
  post-editing, validation, correction) are read with `getSlot` and `key`, and changed in
  Dashboard → AI translation *(no MCP tool)*.
- Templates are Mustache: `{{targetLanguage}}`, `{{{source}}}`. Single braces reach the AI as
  written.
- Try a template before anyone authors it: `testTranslate` with an override of that key. Nothing is
  stored.
- **Context travels with the content.** A `manageDocuments` field's `classes` and `context` reach
  the templates as `entryClasses` and `entryDescription`. In `testTranslate`, surrounding text goes
  in through an override of `batchTranslationContextPromptTemplate`.
- Related translations reach the prompt only when the template renders `{{#neighbors}}` and the
  slot's neighbour search is on. They come from the ContentGuard index, which changes only when it
  is trained again (see [ContentGuard](contentguard.md)).

## 5. Testing: `aiTranslationConfig testTranslate`

- Runs memory, machine translation, the glossary, the AI draft, the validation score and any
  correction round on one segment (plain text, or a block in Easyling's `<g>`/`<x>` markup, up to
  4000 characters). Returns the log, the translation it would store, the score and notes, and the
  AI calls made. Stores nothing.
- **Paid** at the AI provider for every call it makes, and not counted in Easyling's statistics.
  Tens of seconds; minutes with the correction loop. `finished: false` means the deadline stopped
  it, and the log is partial.
- **The log is the one place that shows the engine that ran.** Its configuration notes print
  "Checking against AI engines" (the order), "Base AI" (what the first engine with a key
  supplied), "Configuration AI" (after the slots) and "Effective AI": the engine, model and
  temperature the run used. "Effective AI: -" means that engine has no credentials. Read it after
  every engine, model or credentials change.
- **Test the domain's vocabulary before the first collection.** A general model reads a term in
  its everyday sense: a British "consultant" (a senior hospital doctor) came out in Spanish as a
  business adviser. Put such terms in the glossary, or a rule with an example in the styleguide,
  before content arrives; stored translations do not change when the resources do.
- `runs` (up to 10, run at once) repeats the segment and reports the distribution. The AI is not
  deterministic: judge a change on several runs, never one.
- `existingTranslation` post-edits a given translation instead of translating from nothing.
- `includeUserPrompts` shows the glossary entries and formatting instructions offered for this
  segment; `includeSystemPrompts` the styleguide as sent; `includePublishedGlossary` every
  published pair.
- `overrides` apply any key to this run alone, read-only ones included; `enabled` set to true runs
  a disabled slot. It needs a configuration stored on the project.
- It defaults to the index the project actually uses.

## 6. Validation and the correction loop

- On the unattended path every AI translation is also scored by a validator. That call is paid
  even with the loop off, and the score is not returned over MCP. A pre-translate run started in
  the dashboard can sort its entries into Accepted Score and Low Score work package sets
  (`workPackageGenerationAllowed`, `lowScoreThreshold`); find them with `workPackageSets list`.
- `translationCorrectionLoopEnabled` sends a part scoring below `minimumScoreToReachWithCorrections`
  back with the validator's notes: up to 2 + 2 × `maximumNumberOfCorrections` AI calls per part.
  Unset, the minimum behaves as 1.0, the most expensive value. The MCP writes 0 to 3 corrections.
- **The loop fixes only what its validator flags.** The stock validator scores general quality,
  not whether every number or list item survived. Extend the validation template first, test it
  with an override, then enable the loop on one language slot, never blindly on `*` index 0.
- Scales differ: `lowScoreThreshold` and `minimumScoreToReachWithCorrections` run from 0 to 1,
  `memoryTranslationMinimumScore` from 0 to 100.

## 7. Re-translating stored content

- Auto pre-translate handles new content only. To re-translate what is stored: Dashboard →
  Pre-translate *(no MCP tool)*, choosing the scope (the project, a work package set, a contract
  range, a URL), the step (memory, machine translation, AI) and whether to overwrite existing
  translations. Every entry in scope is a paid call.
- **Check the slot's skip flags first** (`getSlot`). With `skipManualTranslations` off the AI
  replaces what people wrote or imported; `skipMemoryTranslations`, `skipMachineTranslations` and
  `skipAutomaticallyPostEditedTranslations` decide whether earlier output is paid for again.
- Confirming an AI translation without editing it keeps its AI origin, so with the AI skip flags
  off a later run can re-translate confirmed text.
- On a crest project, re-translated text reaches visitors after `manageCrest startExport`.

## 8. Costs

- Free: `aiTranslationConfig listSlots`, `aiTranslationConfig getSlot`,
  `aiTranslationConfig listModels`, and the `linguisticResources` lookups.
- Paid: `aiTranslationConfig testTranslate` (every AI call, times `runs`); every
  `manageAiTranslationConfig` write and its dry run (one test translation); machine translation and
  AI in auto pre-translate and in `manageDocuments translate`; the validator on every unattended AI
  translation; each correction round; a re-translation run from the dashboard.
- A token count of 0 over MCP means "not reported", never "free".
