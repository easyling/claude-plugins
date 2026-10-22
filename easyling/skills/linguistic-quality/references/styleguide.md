# Styleguide

The styleguide is the Markdown text the AI reads as its system prompt on every call of a
configuration slot: tone, form of address, number and date formats, what never to translate. It
is one key of the AI configuration, stored per slot, a target language (or `*` for every
language) and an index from 0 to 9. Most projects use index 0.

## 1. Read it

- `linguisticResources getStyleguide` with `targetLanguage` (and `configurationIndex` when the
  project uses another index): the one styleguide that applies there. `resolvedFrom` names the
  slot it came from. Without coordinates it returns every stored styleguide in full, which runs to
  tens of thousands of characters on a project with language slots; for an overview,
  `aiTranslationConfig listSlots` gives each slot's `styleguideHash` and
  `styleguideCharacterCount`. Both forms warn about single-brace placeholders.
- **A language's own styleguide replaces the `*` one; it does not add to it.** A rule written
  only in `*` is gone for every language that has a styleguide of its own. Repeat shared rules in
  each language styleguide, or keep the language ones empty.
- Which index the project's AI translation reads: `activeConfigurationIndex` in
  `aiTranslationConfig listSlots`.
- A styleguide's `contentHash` compares the text only. Two projects with equal hashes can still
  translate differently, because the rest of the slot differs; compare the slot hashes of
  `aiTranslationConfig listSlots` instead.

## 2. Review it before editing

- The `reviewStyleguide` prompt carries the review method: it extracts every rule, finds
  conflicts, glossary mismatches, rules without an example and unreadable sections, and proposes a
  rewrite for the affected sections only. It writes nothing.
- Only the user can start a prompt, as a slash command or from the client's prompt menu. Ask them
  to run it with the project code and, for a language slot, the language and index. Arguments are
  separated by spaces, never by commas: a comma becomes part of the value and the call is refused.
- A conflict with two valid readings is the customer's decision. Put it to them instead of
  choosing in an edit.
- In a client without prompts, apply the same method by hand and say so.

## 3. Write it

- `manageLinguisticResources saveStyleguide` overwrites the whole slot and has no dry run. Read the
  current text with `getStyleguide`, show the change as before and after, wait for the yes, save,
  then read it back.
- It defaults to `*` index 0, the slot every language inherits from. Always name the language and
  index you mean.
- Saving to coordinates that hold no slot creates one named `< unknown >`. Rename it with
  `manageAiTranslationConfig updateSlot` and `displayName`; that save runs one paid test
  translation.
- A new language slot changes more than its styleguide: it stops that language from inheriting
  index 0 wholesale (see [AI translation](ai-translation.md)).
- The styleguide is a Mustache template: `{{targetLanguage}}` and `{{sourceLanguage}}` are filled
  in; a placeholder in single braces reaches the AI exactly as written.
- Generating a styleguide with AI is in Dashboard → AI translation *(no MCP tool)*. A generated
  styleguide overwrites the stored one.
- After a change, rerun `aiTranslationConfig testTranslate` on the examples that prompted it.
  Stored translations do not change until re-translated or corrected.

## 4. What makes a styleguide work

- **One rule per point, with an example** wherever numbers, units, dates, capitalisation or
  terminology are involved. A rule without an example is read loosely.
- **No contradictions.** Where two sections cannot both be obeyed, the AI follows one or the
  other, and not the same one every time.
- **Form of address and tone per language.** Formal or informal address is a language decision:
  put it in the language slot.
- **Concrete glossary data beats a general rule.** A sentence entry that contradicts the
  styleguide wins; fix the glossary entry rather than adding emphasis to the styleguide.
- **Never ask for glossary sentences to be copied verbatim.** Ask for the pattern to be adapted to
  what the source says, with the source winning where they differ.
- **Names that must stay in the source language** belong in the glossary as do-not-translate
  terms, where the engine sees them per sentence, rather than in a list in the prose.
- **Keep it short.** It is sent with every AI call of the slot, so its length is paid for on
  every call.
