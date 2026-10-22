# Launch and after

A website changes every week, so launch is the start of maintenance. Check everything once before
the languages go public, then agree how new content is collected, translated and published.

## Contents

1. Go-live checklist
2. Keeping translations current
3. Swapping localized files and embeds
4. Changes to the site itself

## 1. Go-live checklist

Run it per language. Note each check and what it showed.

**Content**
- [ ] Scope is what was agreed: `projectSettings get` with the three `restrictions.*` names.
- [ ] Translation is complete enough: one `manageWorkPackageSets createFromScope` call with
      every language and `["notTranslated"]` over the scope shows what is left (through the write
      gate; each call opens a new contract index), and key
      pages look right in the ABC or `-x` preview (proxy) or the `-v` preview (crest).
- [ ] Every state behind an interaction reads in the target language, checked after the AI
  window, not only page loads: search results with few and many hits, detail dialogs, tabs,
  filter panels and their dropdowns, map and list views, empty and validation states
  ([content collection](content-collection.md), section 4).
- [ ] Freezes are set as agreed: `projectSettings get` with `category` `freeze`.
- [ ] There is headroom in the word allowance: `projects subscription`.

**Proxy**
- [ ] DNS is verified and the live domain answers, over HTTPS, with an
      `x-translationproxy-trace-id` response header.
- [ ] Subdirectories: every language folder reaches Easyling (the trace header is there), on
      staging as well as production.
- [ ] Logins, carts, forms, search and the consent banner work on the translated site.
- [ ] The customer's firewall, bot protection and CDN let the proxy through.
- [ ] Caching rules cover static files only: `pathPrefixOverrides list` with `includeOverrides`.

**Crest**
- [ ] `crest getStatus` reads live **and shown** for every language. Live is the script; shown is
  the language's Show switch on Dashboard → Language selector, without which the language picker
  leaves the language out.
- [ ] The embed tag is on every page template, character for character, and the stub answers 200.
- [ ] The `-j` preview, or the real site with the language chosen, shows the published script.
- [ ] The ingestion flags match the agreed policy, and `enableCrestMissingReport` is off:
      `crest getConfig`.

**Both**
- [ ] The language selector is on the source site, reaches every language, and leads back to the
      source language.
- [ ] SEO: language alternates in the sitemap (or the site's own `hreflang` links, reciprocal; the
  proxy adds none, the crest script inserts them), canonical links; SEO overrides imported
      if used.
- [ ] Right-to-left and long-text layouts checked on the key templates.

## 2. Keeping translations current

Agree the new-content policy before launch, because it decides the setup.

- **Let new text show in the source language until translated** (the default). Simple, and
  nothing is hidden, but visitors see mixed pages for a while.
- **Hold new text back**:
  - proxy: an origin snapshot or the keep-cache strategy (see
    [serving through the proxy](serving-proxy.md));
  - crest: new text stays in the source language until the next export carries its translation;
  - manual publishing holds translations back from the live site until they are published from the
    Workbench: Dashboard → Advanced settings → Manual publishing *(no MCP tool)*. Every sign-off
    is then followed by a publish step, so agree who does it.
  - `defaultSourceStatus` PENDING is not a way to hold text back: new entries are still
    translated by auto pre-translate and served, crest exports included; only work package
    (XLIFF) exports leave them out until they are approved.
- **A reviewer's sign-off copy**: there is no PDF export of translated pages. Open the page in the
  `-p` preview and print it to PDF from the browser.
- **Collect new content regularly**:
  - proxy: the live site collects pages as visitors request them; a recurring crawl (daily,
    weekly or monthly) catches pages nobody visits: Dashboard → Crawl → Recurrence
    *(no MCP tool)*. Easyling picks the time of day a recurring crawl runs; never change a crawl
    while it runs.
  - crest: the source reporter or authenticated ingestion links, or a recurring crawl.
  - With a staging site, collect from staging before each release, so translations are ready when
    the content goes live.
- **Translate it**: auto pre-translation and review belong to the linguistic-quality skill. For
  outside translators, a work package of the untranslated text
  (`manageWorkPackageSets createFromScope`) is exported as XLIFF and the translation imported back:
  Dashboard → Work packages, Export and Import *(no MCP tool)*. Easyling's XLIFF covers its own
  collected content only; a third-party XLIFF file is not a way to bring new content in.
- **Publish it on crest**: run `manageCrest startExport` after each translation round, or on a
  regular schedule, and confirm with `crest getStatus`. `enableCrestMissingFetch` bridges the gap
  between exports at the cost of slower pages.
- **Watch the allowance**: `projects subscription`. Over the limit nothing new is collected, and
  nothing on the site says so.
- **Unfreeze for planned rounds**: a page or dictionary freeze set after the quote also stops the
  new content you want. Lift it for the round, then set it again.

## 3. Swapping localized files and embeds

| What | How |
|---|---|
| An image, PDF or download | Dashboard → Pages → Resources: mark it translatable, then upload or link the localized file per language *(no MCP tool)*. One file, one language at a time. On crest, check after the next export that the localized file is the one served; if it is not, replace the link with a page content override or ask support. |
| Images in lazy-loading attributes | List the attribute in `htmlAttributes.link` or `htmlAttributes.srcset` first, then collect again. |
| A video, form or widget id in the HTML | Proxy: the `contentSearchAndReplace` slot of `managePathPrefixOverrides setOverrides`, with `targetLanguages`. Crest: a script in `crestConfig.scriptInjections` limited to the language. |
| A whole page or file per language | Proxy: `managePageContentOverrides put` with the `targetLanguage`; read the current one first. |
| Third-party forms | The vendor's own translated form per language, chosen by a small script that reads `document.documentElement.lang`. |

## 4. Changes to the site itself

- **A new language**: Dashboard → Target languages *(no MCP tool)*, then translation, then
  publishing; on crest add it to the language selector and export it.
- **A new subdomain** with its own content: a new project, linked both ways, published with the
  same languages.
- **The origin moves to another domain**: add the new domain as a staging domain set as live
  default, and update the publishing settings; the project keeps its translations.
- **A new section to leave out**: add its prefix to `restrictions.externalizedPathPrefixes` with
  `manageProjectSettings update` before it is crawled.
