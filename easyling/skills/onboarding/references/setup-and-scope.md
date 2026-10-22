# Setup and scope

Create the project, add its languages, and settle what is translated and how pages are read,
before the first Scan. Most of these settings act only as content is collected, so a mistake
found after the Scan means collecting again.

## Contents

1. The project
2. Languages
3. Scope: limit to and exclude
4. One page per page: grouping and query parameters
5. What is collected from a page
6. Requests and responses
7. Reading and writing settings

## 1. The project

- **Create it**: Dashboard → new project *(no MCP tool)*. The domain cannot be changed afterwards.
  Easyling detects the canonical host; a path in the address is dropped and added as a page. If
  the root redirects elsewhere (a login, another host), turn off the redirect check under the
  dialog's advanced options, then add the pages by hand. The scope rules, "Limit to" and "Exclude"
  (section 3), can be set in the same dialog; a custom segmentation (SRX) file can be added only
  there.
- **Find it over MCP**: `projects list` gives the code, alternative domains, source locale and
  active technologies. A project created after the MCP connection was authorized reads as not
  accessible until you reconnect (in Claude Code, `/mcp`).
- **Alternative domains**: list every host that serves the same content, typically both
  `www.example.com` and `example.com`. Dashboard → Project overview → Alternative domains
  *(no MCP tool)*.
- **Subdomains with their own content** (`blog.example.com`, `shop.example.com`) are separate
  projects. Link them both ways so links between them map to the right language, and publish them
  together with the same target languages: Dashboard → Project overview → Linked projects
  *(no MCP tool)*.
- **Staging hosts** are added to the project rather than made into projects (see
  [serving through the proxy](serving-proxy.md)).
- A wrong source language is fixed by Easyling support.
- **"This project is not indexed"** in the Pages list: ask Easyling support to turn on page
  indexing. It is a background migration that can take up to a day, and it has nothing to do with
  search engines.

## 2. Languages

- Dashboard → Target languages *(no MCP tool)*. Previews, the Workbench and most page actions
  need at least one target language.
- Use full locale codes. The MCP stores them canonically (`de-de` comes back `de-DE`).
- On the proxy each locale serves from its own domain or folder, so `fr-FR` and `fr-CA` need one
  each.
- Right-to-left languages need layout CSS for that language only, for example
  `html[lang="ar-SA"] body { direction: rtl; }` in `injectedStylesheet` (proxy) or a script
  injected for that language (crest).

## 3. Scope: limit to and exclude

The project's **scope** is the set of pages it collects, translates and serves translated. Two
lists set it, and a third, filled by publishing, is always left out.

| Setting | Dashboard | Meaning | Over MCP |
|---|---|---|---|
| `restrictions.pathPrefixMask` | "Limit to" | When it holds a prefix, only paths that start with one are in scope. **Empty means every page.** | writable |
| `restrictions.externalizedPathPrefixes` | "Exclude" | Paths that start with one of these are out of scope, whatever "limit to" says. | writable |
| `restrictions.translationPathPrefixes` | Reserved language subdirectories | The folders translations are published in; always out of scope. | read-only |

**The rule.** A page is in scope when no exclude prefix or language subdirectory starts its path,
and "limit to" is empty or one of its prefixes does. A prefix is plain text, not a folder: it is
matched case-sensitively against the start of the path and query string, percent-encoded as a
browser sends them.

| Rules | `/` | `/en` | `/en/faq` | `/enroll` | `/es/faq` |
|---|---|---|---|---|---|
| "Limit to" empty | in | in | in | in | in |
| "Limit to" `/en` | **out** | in | in | **in** | out |
| "Limit to" `/en/` | out | **out** | in | out | out |
| "Limit to" `/en`, exclude `/enroll` | out | in | in | out | out |

- **The home page.** Any "limit to" leaves `/` out unless one of its prefixes starts it, and `/`
  itself is refused as a prefix: serving would read it as every page, page listings and work
  package scopes as the home page only. To translate the home page but leave sections out, use
  exclusions, not "limit to".
- **A folder that is also a page.** `/en` covers the page `/en`, everything under `/en/` and every
  neighbour that starts with the same letters, such as `/enroll`. `/en/` covers the folder only,
  not the page `/en`. To keep the page and the folder but not the neighbours, use `/en` and exclude
  the neighbours.
- **Check, before and after**: `projectSettings checkScope` with the URLs in question says in or
  out, and which rule decides.
- **Read**: `projectSettings get` with category `scope`.
- **Write**: `manageProjectSettings update` with `dryRun` first. Its warnings say when "limit to"
  becomes empty, when the home page falls out of scope, when a prefix lacks its leading `/`, and
  which pages of the Pages list a new prefix takes in beside its folder. On the proxy the change
  is live on the next request; on crest the published script follows with the next export.
- **Out of scope** a page is served from the origin untranslated and crest leaves it in the source
  language: labels, navigation and footer too, not only the content you meant to leave out. To
  keep part of a page untranslated, use the ignore rules (section 5) instead.
- **Narrowing never deletes translations.** They are hidden, and come back if the scope widens
  again.
- **A project with `useEntryOrdering` on** (`projectSettings get`) works from an entry list that
  grows by itself as content is collected but ignores the scope. After narrowing the scope or
  excluding single pages, the entries of the pages left out stay in exports, the Workbench and
  search until an Easyling admin prunes excluded page entries; after deleting pages, until an admin
  updates the entry list. Ask one to. The write and `projectSettings checkScope` warn about it.
  Widening needs nothing.
- The crawler does not visit pages out of scope, so they never count. If every known page is out
  of scope, a crawl has no entry point and visits nothing: keep at least one page in scope.
- Content sent with `manageDocuments translate` under a path out of scope is still stored,
  translated and counted, but never served there (`pathExcluded`).
- Single pages are excluded, or deleted, in the Pages list: Dashboard → Pages *(no MCP tool)*.

## 4. One page per page: grouping and query parameters

Keep the Pages list from filling with copies of the same content.

- `pathIgnoreRules` groups URLs into one page: `*` matches one path segment, `**` any number,
  and a rule must start with `/` (for example `/category/*/sorted`). The content is still served
  and translated.
- `ignoredParameters` treats URLs that differ only in these query parameters as one page. A new
  project already ignores the common tracking parameters (`utm_*`, `gclid`, `fbclid` and more):
  extend the list with the `add` operation, because `set` replaces it, built-in entries
  included. A bare `*` drops the whole query string from page identity.
- Neither merges pages already listed. Set them before the first crawl; duplicates collected
  earlier are deleted in the Pages list.

## 5. What is collected from a page

All of these apply to content collected from then on.

- **Leave elements out**: `ignoreClasses` (a trailing `*` is a prefix match), `ignoreIds`, and
  `tagOverrides` for custom elements such as the ones browser extensions insert. On the origin,
  the customer can mark an element `translate="no"`.
- **Protect parts of a text**: `ignoreRegexp` turns what it matches (phone numbers, user names,
  dates, order numbers) into a placeholder inside the text that is never translated. Each
  capturing group's span becomes a placeholder and the rest of the match stays translatable;
  `(?:…)` groups without capturing, and `\(` is a literal parenthesis.
  - **Always capture what to protect.** Without a capturing group the proxy protects the whole
    match, but crest fails on the pattern in the visitor's browser wherever it matches, which can
    leave the page untranslated. Write `(\(\d{3}\) \d{3}-\d{4})`, not `\(\d{3}\) \d{3}-\d{4}`; it
    protects a phone number the same way on both.
  - **Keep to what Java and JavaScript handle alike.** The pattern must compile in Java, or the
    write is refused, and crest runs it as JavaScript.
    - **Refused on a crest project** (`crestActive` in `projects list`): an alternative without a
      capturing group, and an inline flag such as `(?i)`, `(?-i)` or `(?i:…)`. Crest throws in the
      visitor's browser or cannot compile the pattern; spell out both cases instead, as in
      `([Aa]\d+)`.
    - **Warned about**, because crest misplaces the placeholder, throws or cannot compile the
      pattern: a capturing group inside another group, an optional or repeated capturing group
      (`(\d)+`, `x(a)?`), a `)` inside a `(?:…)` group (write literal parentheses there as `\x28`
      and `\x29`), a lookaround or atomic group such as `(?<=…)` or `(?>…)`, and an unescaped `(`,
      `)` or `|` inside `[…]`. Each warning names the alternative and shows the fix.
    - A project crest does not serve is warned about all of these and refused none, since they
      break crest only if the project switches to it. Fix the warnings anyway.
  - **One entry for every variant.** The matched value is not part of the entry's identity, so
    texts that differ only in it share one entry and one translation, and each page still shows
    its own value. With the pattern above, "Phone: (555) 010-0100" and "Phone: (555) 010-0199"
    are one entry, "Phone: {x}", translated once; "1-800-555-0100" does not match and is left
    alone.
  - **Protect only the part that changes.** In "08:00 AM-05:00 PM" protect the two times,
    `(\d{2}:\d{2}) [AP]M-(\d{2}:\d{2}) [AP]M`, not the whole range: the words between them stay
    translatable, so the target language gets its own form, such as "a. m." and "p. m.".
  - **Not for names.** Keep plan, product, place and brand names untranslated with a
    do-not-translate glossary (the linguistic-quality skill), never with this pattern. The pattern
    applies to every page, and a loose name alternative such as `([A-Z][^,]*? - Plan)` matches from
    the first capital letter: it freezes whole sentence beginnings ("If you choose … - Plan") in
    the source language and gives them a new key, so their stored translations stop applying.
    A match that crosses an element boundary, such as a bold label in front of the value, also
    makes crest skip the whole block. Keep each alternative to a value with a fixed shape: a
    number, a time, a phone number.
  - **Page text only.** Attribute values such as `aria-label` and `title` are not searched, so an
    attribute that mixes a label with data ("More details" followed by a name) becomes one entry
    per record.
  - **Check the shared entries once translated.** Auto pre-translation handles each new shared
    entry on its own, so siblings can come out in different formats: one weekday with "a. m.", the
    next with "AM". Correct them to one format, and pin it in the styleguide (the
    linguistic-quality skill).
  - **The proxy and crest share it by design.** Both run the same rule, and the crest export
    carries it, so an entry collected through one is served by the other. Crest pages pick up a
    change after the next `manageCrest startExport`.
  - **It shapes content collected from then on.** Existing entries and their translations are
    not rewritten; new content uses the shared entry and the old ones simply fall out of use.
    That is intended, and nothing needs re-collecting.
  - **Not the same as `crestConfig.ingestExcludePattern`**, which keeps a whole text out of
    crest's collection, on crest only. `ignoreRegexp` protects part of a text, on both paths,
    and folds the variants into one entry.
  The rule for number-only text (`projectConfigOverrides.dontTranslatePattern`) is admin-only:
  ask Easyling support to change it.
- **Segment boundaries**: `scbClasses` makes an element one unit with everything inside it inline.
- **Attributes**: only `title`, `alt`, `placeholder`, button `value` and meta descriptions are
  translated without being told. Add others to `htmlAttributes.text`: `aria-label` on any site
  with accessibility obligations (government, healthcare), `data-tooltip` and the like. Never add
  `aria-labelledby` or `aria-describedby`: they hold element ids. Lazy-loading attributes that
  hold URLs go in `htmlAttributes.link` (`data-src`) or `htmlAttributes.srcset` (`data-srcset`).
  A name can sit in one of these lists only, and moves silently.
  - **Adding one is not retroactive.** Pages already collected are not read again, so collect them
    again for the attribute values to arrive as new source entries: recrawl a proxy project; on a
    crest project, open a target-language preview in a browser with `enableCrestMissingReport` on (see
    [content collection](content-collection.md)). Then let auto pre-translate translate them, or
    translate them yourself, and on a crest project run `manageCrest startExport`: its export
    carries both the translations and the attribute list.
- **New entries' status**: `defaultSourceStatus` sets whether new text starts APPROVED (default),
  PENDING (marked for review: still auto pre-translated and served by the proxy, but left out of
  work package exports)
  or EXTERNALIZED (served in the source language in every language). Neither of the last two
  stops the text from being collected and counted as words, and with ContentGuard off, auto
  pre-translate still pays to translate EXTERNALIZED entries, then discards the result.
- **JavaScript, JSON and XML**: `jsonSearchPaths` and `xmlSearchPaths`, together with
  `enforceDictionaryPathPrefixes` for the resource's URL (`projectSettings testJsonPaths` checks
  the JSON rules; see [content collection](content-collection.md)).

## 6. Requests and responses

The proxy forwards only known headers in both directions. Settle these before the first crawl
when the site needs them; [serving through the proxy](serving-proxy.md) has the detail.

- `customHeaders.additionalRemoteRequestHeaders`: a fixed header on every request to the origin,
  crawls included, for example a secret the origin's firewall checks. Anyone who can read the
  project's settings can read its value, and a firewall that trusts it trusts every request made
  through the translated hosts: filter in front of those hosts too.
- `customHeaders.allowedRemoteRequestHeaders`: visitor headers the site's own API needs (a tenant
  id, a CSRF token), in lowercase.
- `customHeaders.allowedLocalResponseHeaders` and `customHeaders.additionalLocalResponseHeaders`:
  response headers to pass through or add, such as a Content-Security-Policy. A wrong one breaks
  every translated page at once.
- All four are whole lists: read them, then send every entry to keep.

## 7. Reading and writing settings

- `projectSettings get` with a `category` (`serving`, `translation`, `crest`, `freeze`,
  `htmlAttributes`, `crawlSettings`, `autoPretranslate`) or with `name`; `writableOnly` lists what
  the MCP may change; `verbose` adds what a change does and whether it is retroactive.
- Settings are named for what they store, often negatively ("disable…", "ignore…"). Match the
  customer's words against the descriptions, not the names.
- `manageProjectSettings update` takes a list of changes, each `set`, `add` or `remove`. Every
  change is validated before anything is written. Run it with `dryRun` first, then for real, then
  read the setting back: an answer of `changed: false` with no warning stored nothing.
- A setting the MCP reports read-only is changed in the dashboard, mostly on Dashboard → Advanced
  settings *(no MCP tool)*, or by Easyling support when it is admin-only.
