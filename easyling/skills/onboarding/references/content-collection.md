# Content collection

Get every text that should be translated into the project, and nothing else. Everything stored
counts toward the word allowance, so check scope and settings
([setup and scope](setup-and-scope.md)) before collecting, and check what arrived afterwards.

## Contents

1. Crawls
2. Content a crawl does not see
3. Crest collection
4. States behind interactions
5. Content that is not on a page
6. Check what arrived
7. Freezes

## 1. Crawls

Crawls are started in the dashboard: Dashboard → Crawl *(no MCP tool)*.

| Crawl type | What it does |
|---|---|
| Discovery (word count) | Visits pages and counts words; stores no content. |
| Scan (content extraction) | Stores every new text as source entries. This is what gets translated, and what counts. |
| New content detection | Counts new words on the known pages against what is stored; stores nothing. |
| Target-language-specific scan | For origins that serve different content per language: each request carries `X-TranslationProxy-Translating-To` with the locale. |

- **Pages to visit**: revisit the known pages and find new ones; the known page list only; or a
  given list of URLs or a sitemap. Always set a page limit when new pages may be found. A crawl
  never visits pages out of the project's scope ([setup and scope](setup-and-scope.md), section 3).
- **Resources**: collect HTML pages only at first. Scripts, styles and images can be added later
  from the Pages list; collecting them all makes the list long and the crawl slow.
- **A crawl's options are fixed when it starts.** To change them, stop it and start a new one;
  never edit a running crawl.
- **Logins**: open the login page in the preview, log in, copy the request's `Cookie` header from
  the browser's network panel, and paste it as the crawl's session cookie. Sites that check the
  visitor's address or browser may still refuse it.
- **A small origin server**: limit the crawl's simultaneous requests.
- **From a staging host**: a staging domain set as the default is what previews and crawls
  fetch from (see [serving through the proxy](serving-proxy.md)).
- **Crest projects**: a plain crawl reads the HTML the server sends. When a framework renders the
  content in the browser, choose prerendering for the crawl. Compare the page source with the
  rendered page first.
- **Error pages**: on the live site, a page answering 3xx, 4xx or 5xx records nothing new. In
  preview it does, so a 404 template opened in preview becomes content.

## 2. Content a crawl does not see

Text that scripts put on the page, or that arrives from API calls, is missing from a proxy
project until it is configured. Find it first.

- **Look**: open the page in the `-x` preview (proxy), which replaces every text the proxy handles
  with x's, or the `xx-xx` preview (crest), which does the same for crest. Whatever is still
  readable is not collected. Search the browser's developer tools (all resources, and the XHR
  responses in the network panel) for that text to find where it comes from.
- **Where it can be**, and what to do:

| Source | Proxy setup |
|---|---|
| A `<script>` block in the HTML page | `jsonSearchPaths` naming the variables or keys |
| A JavaScript file | `jsonSearchPaths`, and `enforceDictionaryPathPrefixes` for the file's URL |
| A JSON response (AJAX) | `jsonSearchPaths` with the `json.` prefix (`json.items.*.title`), and `enforceDictionaryPathPrefixes` for the endpoint |
| An XML response, an RSS feed (`application/rss+xml`) included | `xmlSearchPaths` (XPath: `/rss/channel/item/description/text() html`, `/rss/channel/item/link url`), and `enforceDictionaryPathPrefixes` for the endpoint |
| Another domain | A separate project for that domain, linked to this one |
| An image | Replace the file per language ([launch](launch.md)) |

- **JSON and JavaScript, step by step**:
  1. `projectSettings testJsonPaths` with the data URL (a URL the project serves: its domain, an
     alias or a staging domain) or the script text, and no `paths`. It saves nothing and lists
     every string with a candidate rule, each a pasteable path (array positions as `*`).
  2. `manageProjectSettings update` on `jsonSearchPaths` with the rules wanted. A mode after a
     space marks a value as `url` or `html` (`json.items.*.link url`).
  3. `projectSettings testJsonPaths` again, with `paths` omitted to test the stored rules, to check
     what they match.
  4. `manageProjectSettings update` on `enforceDictionaryPathPrefixes` with the absolute URL
     prefix of the data (`https://www.example.com/api/`, scheme and host included). Every JSON,
     JavaScript and XML response under it is translated and its strings are collected, live at
     once on the proxy; the next crawl collects from it. A prefix does not widen the scope: a URL
     outside "limit to" or under an exclusion stays untranslated (`projectSettings checkScope`
     says which rule decides). Under a page or dictionary freeze the endpoint is translated from
     what the project holds but adds no new strings. Crest does not use the setting. To stop
     translating the endpoint later, exclude it: removing the prefix leaves the URLs it collected
     translated.

  The test and both writes need edit access to the project (an editor or a project manager).
- **Search paths** are writable: `manageProjectSettings update` on `jsonSearchPaths` or
  `xmlSearchPaths`. A malformed JSON path refuses the call; a malformed XPath is stored and
  silently matches nothing. A path can end in ` html` (the match is parsed as HTML and its text
  translated) or ` url` (the match is a link, mapped to the translated host rather than
  translated). For different paths under one part of the site, the `jsonPathOverride`
  slot of `managePathPrefixOverrides setOverrides` replaces the project's paths under that path.
- **Collecting dynamic content**: open the page in the preview and do what makes the content
  appear (open the menu, run a search, add to cart). The proxy stores what the responses carry.
  The dictionary freeze must be off while you do it.
- **Unusual formats**: ASP.NET partial-page responses (`specialFormat` slot), responses mislabelled
  as `text/plain` (`contentTypeOverride` slot), text wrapped in non-standard formats (`clipwrapper`,
  the extractor slot). Read `pathPrefixOverrides describeSlots` before writing any of them.
- **Strings computed in JavaScript** cannot be translated through the proxy.

On crest none of this setup is needed for text that ends up in the page: crest translates the
rendered page.

## 3. Crest collection

The proxy collects as it serves. Crest collects nothing until something hands it the page in a
real browser. Three ways:

1. **A crawl**, as above.
2. **A target-language `-v` preview opened in a browser.** Crest reports the text it finds. This
   stores entries only while `enableCrestMissingReport` is on; `enableCrestMissingFetch` alone
   opens the endpoint but stores nothing. With both off, every report is refused (a 400 on the
   `OPTIONS` request in the network panel). A project created in the dashboard starts with both
   off. One created through a crest trial or the onboarding flow starts with both on, and the
   onboarding flow switches `enableCrestMissingReport` off and `enableCrestMissingSourceReport`
   on once its first exports finish. Read the flags with `crest getConfig` rather than assuming.
3. **The source reporter**: `enableCrestMissingSourceReport` makes the embed collect from visitors
   browsing the untranslated site. It needs the embed installed, and `enableCrestMissingFetch` or
   `enableCrestMissingReport` on for the project.

- **Never collects**: the `xx-xx` preview (it only shows coverage), and fetching any page with
  `curl` or another client that does not run JavaScript.
- **The three flags need no export.** Change them with `manageProjectSettings update`; they apply
  to the next request, though browsers may keep crest's responses for up to ten minutes.
- **When collected text reaches visitors**: it is pre-translated like any other content while
  `autoTranslateConfig.autoPretranslateEnabled` is on, and visitors see the translations once
  `manageCrest startExport` has rebuilt the script, or sooner wherever the missing endpoint is
  open, because it hands back the stored translations of what a page reports.
- **Collection takes whatever the page shows at that moment**: half-rendered markup, placeholder
  keys, consent banners, browser-extension overlays, personal data. Collect from a clean browser
  profile, and keep text that is never content out with `crestConfig.ingestExcludePattern`.
  Texts that repeat with a changing value (a phone number, a date, a count) are content: protect
  the value with `ignoreRegexp` instead, so the variants become one entry (see
  [setup and scope](setup-and-scope.md), section 5).
- **`crestConfig.ingestExcludePattern` is one JavaScript regular expression**, and two mistakes
  fail silently. An unnecessary escape or an inline flag such as `(?i)` makes the whole pattern
  invalid, so nothing is excluded; an empty alternative (`a||b`, or a leading or trailing `|`)
  matches every text, so nothing is collected. `set` replaces it: send the current value with
  `|new` appended.
- **The ingestion policy** (the dashboard calls it content ingestion):
  - *Disabled*: no new content.
  - *Manual*: only browsers opened through an authenticated ingestion link collect. The link (a
    crest authorization) is made in Dashboard → Settings → Content ingestion *(no MCP tool)*, and
    it needs `enableCrestMissingFetch` on for the project.
  - *Automatic, from source-language pages* (`enableCrestMissingSourceReport`): recommended for
    sites that change often.
  - *Automatic, from translated pages* (`enableCrestMissingReport`): collects every visitor's
    translated page, extension and machine-translated text included. Fine for a collection
    session; do not leave it on for the live site.

## 4. States behind interactions

Crest and the `-v` preview collect only what is on screen. Search results, detail dialogs, tabs
and accordions, filter panels, map and list views, and empty, validation and error states exist
only after someone acts. Loading every URL leaves them out, and a page checked only as it loads
can read as translated while they are not.

- **Inventory first.** For each page template, list the states it can reach and the inputs that
  reach them: a search term, a postcode, a record that opens a dialog. Before the collection
  round, ask the customer for representative inputs and for permission to submit read-only forms
  such as searches.
- **Exercise every state** in the target-language `-v` preview with `enableCrestMissingReport`
  on: every search mode, tab, panel and dialog, a search with many results, and the empty and
  validation states. Pick from autocomplete lists the way a visitor would; a typed value alone
  may not start the search.
- **Dropdowns are value lists.** Opening a filter panel puts its options on screen: categories,
  specialties, languages. One visit collects every value a record can show, because a value in a
  dialog and the same option text share one entry.
- **Variable parts make every record new text.** A count ("6 results shown"), a distance, a time
  range or a list of names inside a sentence turns each variant into a new entry, so no amount of
  visiting covers them. Protect the variable part with `ignoreRegexp`, one capturing group per
  value, so the variants share one entry ([setup and scope](setup-and-scope.md), section 5). Use
  `crestConfig.ingestExcludePattern` only for a text that is all data, such as a name or an
  address on its own.
- **Never exclude a label together with its data.** Excluding "More Details" followed by a
  record's name, or setting that entry EXTERNALIZED, keeps the label in the source language too,
  attributes such as `aria-label` included, so screen readers read it out untranslated. Protect
  the data part instead, or ask the site to mark data fields with a class (`ignoreClasses`) or
  `translate="no"`.
- **Read what was collected as a map.** Entries holding escaped HTML (`&lt;p&gt;`) or
  `{{placeholders}}` are usually the site's component templates. They name the labels of results
  and dialogs before anyone opens them. They are never shown as text, and some carry a record's
  real data: read them, then set them EXTERNALIZED. A site that loads its texts from a CMS or an
  API has none of them in its JavaScript bundle; read the content API instead.
- **The first viewer sees the source language.** A state collected for the first time stays
  untranslated until auto pre-translation has handled it, which takes minutes. With
  `enableCrestMissingFetch` on, the next viewer gets the translation without an export; the
  script carries it after the next `manageCrest startExport`.
- **Check each state again** after that wait: reopen it and list what is still in the source
  language, then export. "Every page reads translated on load" does not mean collected.

## 5. Content that is not on a page

CMS fields, app strings, email texts or documents can be sent straight to the project with
`manageDocuments translate`.

- `kind` is required: `http` stores the fields as a page of the site at `path`; `file` stores
  them beside the site under `file://`, where they can never clash with a page.
- The path obeys the scope rules. Outside them the content is still stored, translated and
  counted, but never served; the answer says `pathExcluded`.
- One target language per call. The AI runs only when the project's auto pre-translate switches
  allow it; each untranslated field says why.
- Sending to the same path again adds to the page and never removes a field. For repeated
  deliveries, put a batch or job id into the path.
- A field's `classes` and `context` are stored when its text is first seen: send headings and
  labels before table cells.
- `finished: false` means the time ran out; what was done is stored, and calling again continues.
- These entries count as words like any other.

## 6. Check what arrived

- `entries listByPage` with the page's `path` and `kind`: every entry of one page, read directly,
  so it works a moment after collection. It does not take `/` (use `entries search` with a phrase
  from the home page) and returns at most 1000 entries.
- `entries search` works from each language's export list. New content is invisible to it until
  `manageEntries rebuildExportList` has run for that language (through the write gate; it is safe
  to repeat and reports `started`, then `alreadyGenerating`, then `alreadyFresh`). Check
  `exportListFresh` and the warnings, and keep paging while `hasMore` is true.
- `projects subscription` shows the words used against the allowance.
- `projectSettings get` with `category` `freeze` shows whether anything stops collection.

## 7. Freezes

Once the quoted content is in, freeze it so that the project does not grow behind the quote.

| Setting | Effect |
|---|---|
| `pageFreeze` | No new pages are recorded; new text on known pages still is. |
| `dictionaryFreeze` | No new text is recorded anywhere. It also refuses new `manageDocuments` text, unless `sanityIgnoreDictionaryFreeze` is on. |
| `unknownPagesAreExternalized` | Pages not in the list are served untranslated. Only with `pageFreeze`. |
| `hardDictionaryFreeze` | Set automatically when the project is over its word limit; read-only, and nothing bypasses it. |

- Text the project already holds is served and translated under any freeze.
- A crawl or "add pages" started on purpose can still add pages under a page freeze.
- Turn the freezes off for each planned collection round, and on again after it.
