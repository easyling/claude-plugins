# Serving through crest

The page comes from the customer's own server; one script tag on it makes the visitor's browser
translate it. The project's configuration is compiled into each language's exported script, so a
stored change reaches visitors with the next export.

## Contents

1. How it works
2. Set it up
3. Language selection
4. A language per path
5. Single-page apps and frameworks
6. SEO, attributes and speed
7. What does not apply on crest

## 1. How it works

- The embed tag loads the **stub** from Easyling. The stub picks the language (the visitor's
  earlier choice in `localStorage` under `ptLanguage`, the `__ptLanguage` query parameter, or the
  path), shows the language selector, and loads that language's **translator**: the published
  export, which carries the translations and the configuration. The translator translates the
  page and keeps translating as the page changes.
- On pages shown in the source language the stub can run the **source reporter** instead, which
  collects new content (see [content collection](content-collection.md)).
- **The three scripts can be loaded on their own**: the stub (`/client/<projectCode>/0/stub.js`:
  selector, remembered choice, loads the others), one translator per language
  (`/client/<projectCode>/0/<locale>.js`) and the source reporter
  (`/client/<projectCode>/reporter/<sourceLocale>.js`, which only collects). To collect content on
  a live site before anything is visible, put only the reporter there. The stub offers every
  language that is shown (section 3) and has a published script; a site with its own language
  switcher can load the translator itself and skip the stub.
- **Crest gives no traffic or per-language analytics.** The site sends its own analytics events
  if the customer wants them.
- `crest getConfig` lists every crest setting and whether the MCP may change it. `crest getStatus`
  says per language whether the published script is live, stale (built before the current
  configuration), unpublished or unknown, whether the language is shown, and gives the embed tag.
- **What needs no export**: `enableCrestMissingFetch`, `enableCrestMissingReport` and
  `enableCrestMissingSourceReport`, and what the source reporter collects
  (`crestConfig.ingestExcludePattern` included). Everything else waits for
  `manageCrest startExport`. Browsers may keep the stub and crest's responses for up to ten
  minutes either way.

## 2. Set it up

1. **Collect and translate** the content ([content collection](content-collection.md); the
   translation itself belongs to the linguistic-quality skill).
2. **Choose the languages visitors are offered**: turn on each one's **Show** switch on Dashboard
   → Language selector *(no MCP tool)*. A language is offered only when it is shown **and** has a
   published script; `crest getStatus` reports both, as `shown` and `state`.
3. **Export.** `manageCrest startExport` with the `targetLanguages` and `dryRun: true`; check
   `languagesSkipped`; then run it for real. Without `targetLanguages` it exports every language,
   hidden ones included. Exporting publishes a script; it never turns a language's Show switch on.
   There is no job to follow: call `crest getStatus` until the language reads live and shown.
   Each call is a new export.
4. **The embed tag.** Take the `<script>` tag from `crest getStatus` and have it placed as high in
   `<head>` as possible, in the template every page uses. It must arrive **character for
   character**: CMS editors and page builders turn the URL into a link, curl the quotes or change
   the host. In the browser's network panel the stub request must answer 200. A site builder that
   refuses custom scripts cannot run crest (use the proxy).
5. **Test before launch.**
   - The `-v` preview (`<locale>-<projectCode>-v.app.easyling.com` on the main installation)
     always runs the server's current translator: no export needed.
   - The `-j` preview shows what a live visitor gets: the published export only, with no
     fallback. A language gets it only when it has a published export and a domain or domain
     override; otherwise the page is served without crest. It adds the stub only when the crest
     configuration asks for stub injection.
   - A published script before its language qualifies for `-j`: add the embed tag to the `-j`
     page yourself and choose the language as below.
   - On the real site, before the language is offered: with the tag on a page, run
     `localStorage.setItem("ptLanguage", "de-DE")` in the browser console and reload. The
     `?__ptLanguage=de-DE` query works too, but can break a single-page app's routing. Both names
     are defaults that `crestConfig.stubParameterOverrides` can rename.
   - Blocks left in the source language although `entries get` shows their translations: look for
     an uncaught exception from the crest script in the browser console before changing settings
     (section 5).
6. **Set the ingestion policy for production** ([content collection](content-collection.md)):
   collect from source-language pages or through authenticated links, and turn
   `enableCrestMissingReport` off. `enableCrestMissingFetch` lets the script ask for translations
   of text added after the export; an export is still faster for visitors.

## 3. Language selection

- **"Published" means three different things; never use the bare word.**
  - A crest **script is published** when an export serves it: `crest getStatus` `state` live.
  - A **language is shown** when its Show switch on the Language selector page is on (stored as
    the language being published): `crest getStatus` `shown`. Only a shown language is listed in
    the sidebar and the dropdown, and `crestStub.setCurrentLanguage` refuses a hidden one. A hidden
    language still loads for a visitor whose stored choice (`ptLanguage`), `?__ptLanguage=` or
    language path selects it, which is how it can be tested before launch.
  - A **language is published on a host** when Dashboard → Publish gives it a domain or a
    subdirectory, which the proxy and the `-j` preview need. Publishing on a subdomain also turns
    its Show switch on.
- **Sidebar**: built into the stub, showing flags; its side and names are set on the Language
  selector page.
- **Dropdown**: an empty element with the class `el-dropdown` (or the selector configured) where
  it should appear, plus the dropdown script tag from the Language selector page. Turn the sidebar
  off with `crestConfig.selectorDisabled`, or the page shows both.
- **The site's own links**: link each language with `?__ptLanguage=<locale>`, the source language
  included, so visitors can switch back; the choice is remembered in `localStorage`.
- **The site drives the language itself**: `crestConfig.passive` keeps crest present but idle (no
  selector, nothing remembered); the site calls `window.crestStub.setCurrentLanguage("de-DE")`
  (the source locale switches back), reads `getCurrentLanguage()`, and builds menus from
  `window.crestStub.languages`.
- `crestConfig.stubParameterOverrides` renames the query parameter or the storage key and sets
  the stub's other options. It is a whole list, and every value is a string (`"true"`).

## 4. A language per path

- **Behind a CDN**: the CDN sends each language folder to that language's `-j` host, as for proxy
  subdirectory publishing ([serving through the proxy](serving-proxy.md), section 3).
- **Without a CDN, by path**: `crestConfig.languageSelectedByPath` makes the stub take the
  language from the first path segment when it matches a locale, ahead of the remembered choice.
  The customer serves the source pages under a folder per language (`/de-de/…`).
- **Without a CDN, by script**: a short script that reads the path and calls
  `window.crestStub.setCurrentLanguage`. Host it as a page content override with
  `Content-Type: application/javascript` (`managePageContentOverrides put`) and a
  `Cache-Control: public, max-age=86400` header, and add its URL on the language's temporary
  domain to `crestConfig.scriptInjections`. That list is replaced whole on every write; an entry's
  `languagePattern` limits it to some languages.
- **On a subdomain**: publish the language on a subdomain (Dashboard → Publish *(no MCP tool)*,
  with the customer's DNS); crest serves it through the `-j` route. If missing-text requests from
  those subdomains are refused while Fetch or Report is on, add the subdomains to the project's
  alternative domains as well (this was needed at the time of writing; check before relying on it).
- **On a second hostname the customer runs** (for example a host per market serving the same
  source pages with the same script): ask Easyling support to map the host to the language.
  `localStorage` does not cross hosts, so the site's switcher must change the host, keep the path
  and pass the language in the `__ptLanguage` query parameter.
- **Every language URL must load on its own.** If a language URL answers 404 unless the visitor
  arrived from the source site, the script never runs there; find out what produces the 404 (the
  site's router, the CDN, the server) before anything else.

## 5. Single-page apps and frameworks

- **Server-rendered pages that hydrate**: `crestConfig.manuallyStarted` holds translation until the
  site calls `window.crestTranslator.start()`, after the `crestTranslatorAvailable` event. A single
  page can ask for it with `data-crest-manual="true"` on the script tag.
- **Content the site rewrites after crest translated it**: `crestConfig.treatUnhandledOnChangeSelector`
  names the elements to translate again. While reporting is on, it can collect translated text as
  source.
- **An inline element that should be its own unit**, or one crest moves or mixes up:
  `crestConfig.blockSelector`.
- **Blocks stay in the source language although translations exist**: look for an uncaught
  exception in the browser console first. One exception abandons the rest of that translation
  pass; no setting fixes it.
- **Hiding the switch**: the events `crestDictionaryLoadingStart` / `End`,
  `crestDocumentTranslationStart` / `End` and `crestMutationTranslationStart` / `End` let the site
  show an overlay while the language changes.

## 6. SEO, attributes and speed

- Crest inserts `hreflang` alternates, an `x-default` and a canonical link.
  `crestConfig.linkElementsDisabled` leaves out some or all of them when the site manages its
  own.
- Attributes follow the project's `htmlAttributes` lists ([setup and scope](setup-and-scope.md)).
  Meta descriptions are translated on crest only while `enableCrestMetaHandling` is on; the MCP
  can read it but not change it.
- **Slow translation**: try `crestConfig.attributeTranslationDisabled` first. It turns off the
  costly attribute pass; the built-in attributes stay translated, but listed ones such as
  `aria-label` go back to the source language, which matters on accessible sites.
- **Very large sites**: a bootstrap export carries only the segments most pages share, and
  `enableCrestMissingFetch` fetches the rest. The bootstrap work package is created in Dashboard →
  JavaScript publishing → Bootstrap and exported from the dashboard *(no MCP tool)*.
- **The source text shows briefly** before translation: keep the tag high in `<head>`, and use
  the events above for an overlay.

## 7. What does not apply on crest

These act only on the proxy, so they change nothing for crest visitors: path prefix overrides,
caching rules and snapshots, the injected JavaScript and CSS settings (use
`crestConfig.scriptInjections`), meta tag overrides, the multilingual sitemap, keeping the
DOCTYPE, and the analytics header. `customHeaders.*` reach only previews and crawls. Page content
overrides serve only on Easyling's own hosts. A search integration injected over the proxy does not
work on crest.
