# Choosing the serving mode

Easyling serves translations in two ways, and the choice decides what the customer has to change,
how search engines see the languages and when a change reaches visitors. The MCP's server
instructions state the model in brief and the `crest` tool text holds the crest detail; this file
is the decision.

## The two mechanisms

- **Proxy.** Each language has its own host or folder. A visitor's request reaches Easyling,
  which fetches the page from the origin, translates it and returns it. The proxy reads the
  project on every request, so a stored change is live on the next one.
- **Crest.** The page comes from the customer's own server with one `<script>` tag on it. The
  script (the stub) loads that language's exported translator, which translates the page in the
  browser and follows the page as it changes. The configuration is compiled into the export, so
  a stored change reaches visitors with the next `manageCrest startExport`.
- **Both.** A project can collect through the proxy (crawls, previews) and serve through crest,
  or serve some languages each way. Translations belong to the project, not to the mechanism, so
  switching later is a serving change, not new translation work.
- `projects list` reports `activeTechnologies` (`proxyActive`, `crestActive` and others). It is
  set in the dashboard, not over MCP. The `useCrest` setting is on everywhere and does not
  answer this question.

## Side by side

| | Proxy | Crest |
|---|---|---|
| The customer adds | DNS records for a subdomain or domain, or a reverse proxy or CDN rule for a subdirectory | One script tag in the `<head>` of every page |
| Search engines see | Translated HTML at its own URL per language | Text translated in the browser, so only crawlers that run JavaScript see it; a URL per language only behind a CDN route (see below) |
| JavaScript-heavy sites, single-page apps | Text that scripts or API responses bring needs per-site rules | Works on the rendered page, usually without extra rules |
| First paint | Translated | The source text shows briefly before translation |
| Logins, carts, forms, cookies | Pass through the proxy; cookies, headers and cross-origin calls may need settings | Run on the origin as before |
| Usage | Every HTTP request through the proxy counts | Pages come from the origin; Easyling serves the scripts |
| A stored change goes live | On the next request | After the next export (the three ingestion flags excepted) |
| Staging | A staging host can be the origin for previews and crawls | The script must be on the staging site too |

## Decide

Go down the list; the first rule that fits usually decides.

1. **The customer cannot add a script to the pages** (a hosted site builder that strips or
   sandboxes custom scripts): proxy, on a subdomain.
2. **SEO needs a separate, indexable URL per language**: proxy on a subdomain or separate domain,
   or in a subdirectory behind the customer's reverse proxy or CDN. Crest comes closer only behind
   a CDN that sends the language folders to Easyling (the `-j` route, below): each language gets
   its own URL, but the text is still translated in the browser. A search engine sees a crest
   language only when it runs the page's JavaScript, which Google does in a later rendering pass,
   so crest languages are indexed later and less reliably than proxy pages. Say so whenever a
   crest recommendation meets an SEO requirement.
3. **WordPress**: the Easyling plugin from wordpress.org publishes in subdirectories from inside
   WordPress, in proxy or JavaScript mode, and adds a language selector, so no CDN or reverse
   proxy is needed. The customer enters the project code in the plugin.
4. **A single-page app or a hydrating framework** (React, Vue, Angular, Next.js, server-rendered
   or not): crest, recommended before any proxy trial. Through the proxy, the app overwrites the
   translated HTML with source text when it re-renders, and the proxy does not translate text
   compiled into the JavaScript bundles; every API response that carries text would also need its
   own rules. On such sites the usual setup is for the site to start crest after it has rendered
   (`crestConfig.manuallyStarted`; see [serving through crest](serving-crest.md)).
5. **The customer cannot change DNS and has no CDN**: crest on the origin, or the WordPress plugin.
6. **Very large sites** (hundreds of thousands of words): both work; crest then needs a small
   bootstrap export plus dynamic fetching so the script stays fast.
7. **Site search must search the translated text**: plan it now. Translated site search over the
   proxy, or a client-side search integration injected over it, is arranged with Easyling support
   or sales. On crest, search results the site inserts into the page are translated as standard, but
   translating a visitor's target-language query back into the source language before the site
   searches is custom development; scope it with Easyling sales.
8. **No preference**: crest is the simpler start for most sites; the proxy is the choice when SEO
   per language or full control of the served HTML matters most.

## Subdirectories (`example.com/de/`)

- **Proxy.** The customer's reverse proxy or CDN forwards each language folder to that language's
  Easyling host with a few headers. The publish wizard writes the snippet for nginx, Cloudflare
  Workers and AWS CloudFront; other reverse proxies follow the same pattern. Details in
  [serving through the proxy](serving-proxy.md).
- **Crest, with a CDN**: the CDN routes the language folders to the language's `-j` host, which
  serves the origin's page with the language's published crest script: a URL per language,
  translated in the browser. The crest script inserts `hreflang` alternates on every page it runs
  on, the `-j` route and the origin alike (`crestConfig.linkElementsDisabled` turns them off); the
  proxy adds none and passes the origin's own through unchanged.
- **Crest, without a CDN**: either copy the source pages into a folder per language and turn on
  `crestConfig.languageSelectedByPath`, so the path picks the language; or inject a small script
  that reads the path and selects the language (see [serving through crest](serving-crest.md)).

## Questions to settle with the customer

- The CMS and the hosting, before sending any reverse proxy, CDN or DNS instructions: some
  managed hosts allow no proxy rules, and then the WordPress plugin (or crest) is the route.
- Who changes DNS, the CDN or the reverse proxy, and how long their change process takes.
- Whether a script tag can go into the shared page template, high in `<head>`.
- Whether a firewall, bot manager or CDN rule in front of the origin needs to let Easyling in
  (proxy, and crawls in both modes).
- How the language switcher should look and where it sits.
