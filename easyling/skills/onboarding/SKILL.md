---
name: onboarding
description: Use when setting up a site in Easyling or preparing a demo of it - word count and quote, proxy or crest, scope, collecting content, publishing a language, PDFs per language, going live.
compatibility: Needs the Easyling MCP server
---

# Onboarding

Take a website from "we want it in other languages" to translated pages that visitors see, and
keep it that way. Much of onboarding is decisions and dashboard work. The MCP reads the project,
changes the settings it exposes, counts the words left to translate and publishes crest scripts;
every change goes through the write gate below.

## When to use

- A prospect or customer wants a site translated: assessing it, sizing the words, the quote.
- A demo for a prospect, from nothing more than a project code: representative pages collected
  and translated, the serving mode, and the questions to ask: [preparing a demo](references/demo.md).
- A new project: languages, what is in scope, the settings to get right before the first crawl.
- Collecting content: crawls, JavaScript and JSON content, pages behind a login, crest
  collection, content that is not on a page.
- Publishing: a subdomain or another domain, a subdirectory behind the customer's reverse proxy
  or CDN, WordPress, staging hosts.
- Setting up crest on a site: the embed tag, the language selector, ingestion flags, exports.
- Going live, and keeping translations current afterwards.

Hand-offs. Wording, glossaries, translation memories, styleguides, AI translation settings and
ContentGuard belong to the linguistic-quality skill. Something that used to work and no longer
does is a fault: send it to Easyling support, or to a triage skill if one is installed. A language
host that shows the "Welcome to the Translation Proxy" page is not a fault: the language was
unpublished or its domain changed, and republishing it is self-service (see
[serving through the proxy](references/serving-proxy.md), section 2). Plans and
billing, certificates beyond the managed ones set up at publishing, and fixed outgoing addresses
are questions for Easyling support. When the skill for a step is not installed, describe the
step instead of making it.

## Intake

Establish these first, and ask for whatever the request leaves out. For a demo, follow
[preparing a demo](references/demo.md) instead: it works these out from the project and the site,
and turns what is left into questions for the customer.

0. **Which Easyling installation the MCP reaches.** A project lives on one installation (the
   main one or a white-label one), and the MCP sees only the installation it is connected to. The
   connection this plugin ships with is a development installation that holds test projects
   only. Until the customer's installation is connected, onboard in that installation's
   dashboard: every MCP step below is then a check or a setting for someone with access to make
   there. Never read "not found" on the wrong installation as "does not exist".
1. **The site.** Every host it uses (`www` and the naked domain, subdomains such as a blog or a
   shop, staging hosts) and which parts are in scope.
2. **Languages.** The source language and each target locale. On the proxy each locale variant
   needs its own domain or folder; right-to-left languages need layout work.
3. **Goals.** SEO (does each language need its own indexable URLs?), which pages, and what
   happens to new content: shown in the source language until translated, or held back.
4. **Timeline.** Launch date, review rounds, whether all languages go live together.
5. **Hosting.** CMS or site builder, single-page app framework, CDN, firewall or bot
   protection, logins; who controls DNS; whether the customer can add a script tag to every page
   or run a reverse proxy rule.
6. **An existing project.** `projects list` gives each project's code, domains, source locale and
   active technologies. One site often has several projects (staging, an older copy): confirm
   which one is meant before changing anything.

## Choosing the serving mode

| | Proxy | Crest |
|---|---|---|
| Translates | On Easyling's servers, as each page passes through | In the visitor's browser, from an exported script |
| The customer adds | DNS records, or a reverse proxy or CDN rule for subdirectories | One `<script>` tag on every page |
| Fits best | SEO with a URL per language; sites that cannot take a script | JavaScript-heavy sites and single-page apps; no DNS change possible |
| A stored change goes live | On the next request | With the next `manageCrest startExport` (three ingestion flags excepted) |
| Usage | Every HTTP request through the proxy counts | Pages come from the origin; Easyling serves the scripts |

A project can do both, for example collect through the proxy and serve through crest. Which
mechanisms serve a project is `activeTechnologies` in `projects list`, set in the dashboard. The
decision guide (SEO, single-page apps and Next.js, WordPress, subdirectories, staging, site
search) is in [serving mode](references/serving-mode.md).

## The shared trunk

The same steps for both modes, in this order. Each reference says what to check and what each
result means.

1. **Assess and quote.** A Discovery before any Scan, unique words, what a crawl cannot see, the
   traffic the proxy would carry, the plan size: [assessment and quote](references/assessment-and-quote.md).
2. **Create the project and its languages.** Dashboard → new project *(no MCP tool)*, then
   Dashboard → Target languages *(no MCP tool)*. Reconnect the MCP afterwards (in Claude Code,
   `/mcp`), because its project list is taken at sign-in. `projects list` confirms the code;
   `projects subscription` shows the plan and the word allowance.
3. **Scope and settings, before the first Scan.** The scope ("limit to" and "exclude"), page
   grouping, ignore rules, attributes, headers: [setup and scope](references/setup-and-scope.md).
   Most of them act only as content is collected, so they must be in place first.
4. **Collect the content.** Crawls, JavaScript and JSON content, logins, crest collection,
   content sent with `manageDocuments translate`: [content collection](references/content-collection.md).
   Freeze the page list and the dictionary once the quoted content is in.
5. **Translate.** Auto pre-translation, translation memory, AI and human review belong to the
   linguistic-quality skill. Before auto pre-translate goes on, load the engine credentials from
   the account with `manageAiTranslationConfig loadAccountCredentials` (OpenAI or Gemini; other
   engines in Dashboard → MT engines → Load from account *(no MCP tool)*), pin the AI engine (OpenAI
   recommended), check it with one `aiTranslationConfig testTranslate`, and put the domain's terms
   in the glossary or styleguide: the linguistic-quality skill's AI translation reference has the
   steps. Watch the words used with `projects subscription`.
6. **Serve.** Follow the fork below.
7. **Launch and keep it current.** The go-live checklist, recurring collection, new content and
   localized files: [launch](references/launch.md).

## The fork: serving

| | Proxy | Crest |
|---|---|---|
| Read | [serving through the proxy](references/serving-proxy.md) | [serving through crest](references/serving-crest.md) |
| Preview | `-p` to review, `-x` to see what the proxy handles | `-v` (current translator, no export), `xx-xx` for coverage |
| Publish | Dashboard → Publish *(no MCP tool)*: DNS records, or the customer's reverse proxy or CDN rule | `manageCrest startExport`, then the embed tag `crest getStatus` gives |
| Is it live? | The live host answers with an `x-translationproxy-trace-id` header | `crest getStatus` reads live and shown for each language; the `-j` preview shows the published script |
| Settings reach visitors | On the next request | With the next export |
| Main settings | `customHeaders.*`, path prefix overrides, page content overrides, injected CSS and JS | `crestConfig.*`, the three ingestion flags |

## The write gate

Onboarding writes settings, path rules, overrides and exports. Every one goes through this gate.

<!-- write-gate:start -->
**Before any change**
1. Show what will change: run with `dryRun: true` where the tool has it; otherwise read the
   current value and show before and after.
2. Say what it costs when it re-crawls, re-translates, calls an AI service or deletes.
3. Wait for an explicit yes from the user.
4. Make the change, read it back, and report what is now stored.
<!-- write-gate:end -->

- **Dry runs** exist for `manageProjectSettings update`, all three `managePathPrefixOverrides`
  actions and `manageCrest startExport`.
- **No dry run**: `managePageContentOverrides put` replaces the whole stored response, which is
  its only copy, so read it with `pageContentOverrides list` first.
  `manageWorkPackageSets createFromScope` and `manageDocuments translate` create things that
  cannot be deleted over MCP; name them deliberately, and give `createFromScope` every language
  in one call, since each call opens a new contract index. `manageEntries rebuildExportList`
  rebuilds the project's export list in the background.
- **Costs to name**: a Scan, crest reporting and `manageDocuments` add source words that count
  toward the plan, and auto pre-translation then spends on them; a public cache cannot be
  recalled; on crest every export replaces the live script.

## Pitfalls

- **Scope prefixes are plain text, and an empty "limit to" means everything.** "Limit to" `/en`
  takes in `/enroll` and leaves out the home page `/`; `/en/` covers the folder but not the page
  `/en`; emptying "limit to" widens the project to the whole site. Check with
  `projectSettings checkScope` ([setup and scope](references/setup-and-scope.md), section 3).
- **"Published" means three things.** A crest script is published by an export; a language is
  shown by its Show switch on the Language selector page; a language is published on a host by
  Dashboard → Publish. `crest getStatus` live is the script only: check that it says shown too.
- **A page is not collected until its states are.** Results, dialogs, tabs, filter panels and
  error states appear only after someone acts, so loading every URL misses them, and texts that
  mix a label with record data are new for every record. Inventory the states, exercise each one,
  and check again after the AI window ([content collection](references/content-collection.md),
  section 4). Never exclude a label together with its data.
- **Settings shape content as it is collected.** Ignore rules, attributes, page grouping and
  search paths are not retroactive: set them before the first Scan, or collect again.
- **`ignoredParameters` ships with a tracking-parameter list.** Use the `add` operation; `set`
  replaces the built-in entries.
- **Some settings are whole lists.** `tagOverrides`, every `customHeaders.*` list,
  `crestConfig.scriptInjections` and `crestConfig.stubParameterOverrides` are replaced on every
  write: read them first and send every entry to keep.
- **Every collection path counts.** Scans, crest reporting, error pages opened in preview and
  `manageDocuments` all add source words. Over the word limit nothing new is collected, on the
  proxy and on crest alike, and the site does not say so.
- **Content submitted under an excluded path** is stored, translated and counted, but never
  served there; the answer says `pathExcluded`.
- **Stored is not live on crest.** A setting reaches crest visitors with the next export, and
  browsers keep the stub for up to ten minutes.
- **A crest project created in the dashboard collects nothing from browsers** until
  `enableCrestMissingReport` is on, or `enableCrestMissingSourceReport` together with Fetch or
  Report; one created through a trial or the onboarding flow starts with Fetch and Report on.
  `enableCrestMissingFetch` alone stores nothing; a crawl collects regardless. The `xx-xx` preview
  and any fetch outside a browser never collect.
- **Do not leave `enableCrestMissingReport` on for a live site.** Every visitor's page, browser
  extensions and machine-translated text included, becomes source and counts.
- **A cached copy cannot be recalled.** Browsers and CDNs keep a response until its `max-age`
  runs out; cache only static, versioned files for long.
- **Read-only over MCP does not mean unchanged.** Most settings are edited in the dashboard;
  read them before relying on them.
- **Settings are named for what they store**, often negatively. Match the customer's words
  against the descriptions (`projectSettings get` with `verbose`), not against the names.
- **"Project is not accessible"** for a project created after you connected: reconnect the MCP.
- **Listings are complete** for the installation you are connected to: an empty result there
  means the thing does not exist.

## Report back

Answer in this shape:

1. **Site and goals:** hosts, languages, scope, SEO needs and the new-content policy agreed.
2. **Decision:** the serving mode, and why.
3. **Done:** each tool call or dashboard step, with what it returned or what is now stored.
4. **For the customer:** exactly what they must do (DNS records, the script tag, the reverse
   proxy or CDN rule, firewall allowances), in sentences they can be sent.
5. **Open:** risks, the usage to expect, and the next step.
