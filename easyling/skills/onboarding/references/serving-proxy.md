# Serving through the proxy

Each language gets its own host or folder. Visitors' requests reach Easyling, which fetches the
page from the origin, translates it and returns it. A stored change is live on the next request.

## Contents

1. Hosts and preview modes
2. Publishing on a subdomain or another domain
3. Publishing in a subdirectory
4. Staging domains
5. Traffic and caching
6. Headers, cookies and the origin
7. SEO
8. Changing pages on the way out

## 1. Hosts and preview modes

Every language has hosts of the form `<locale>-<projectCode>[-mode].app.easyling.com` on the
main installation; white-label installations use their own domain. The dashboard's Pages list
opens each mode for the selected language.

| Mode | Use it to |
|---|---|
| `-p` preview | Review translations in context, collect dynamic content by browsing, log in to copy a session cookie. Always shows the latest translations and is never cached. Never link it from a live site. |
| `-x` | See what the proxy handles: every text it would translate turns into x's. |
| X80, X130 | Simulate text 20% shorter or 30% longer to find layout breaks. |
| ABC | Show each text's state: `x` not collected, `a` collected but untranslated, `b` same as source, `c` translated. |
| Dummy | The origin's page through the proxy, untranslated: tells a proxy problem from an origin that treats the proxy differently. |
| Temporary domain (no suffix) | Behaves like the live site. Subdirectory publishing forwards to it. |

## 2. Publishing on a subdomain or another domain

Dashboard → Publish → the language → Publish wizard *(no MCP tool)*, with the customer's DNS.

- **One domain per language.** A language is served on one domain at a time (`fr.example.com` or
  `example-fr.com`), and each domain serves one language of one project. Locale variants need a
  domain each. Redirect the variant you do not use (`www` or the naked domain) with a 301.
- **DNS records.** The wizard lists them as the serving domain is typed: a few CNAME records,
  more for a naked domain. One record proves ownership and is computed for the user looking at
  the page, so the same person sends the records and presses Verify. Propagation can take up to
  a day. Easyling never manages the customer's DNS zone: the domain owner or their contractor
  enters the records, and Verify reads public DNS only, so whoever presses it needs no access to
  the zone.
- **SSL.** Managed certificates are set up as part of publishing. Any other certificate question
  goes to Easyling support.
- **Turning a language off**: deactivating it in the wizard stops serving, as does removing the
  DNS records. Translations stay in the project.
- **"Welcome to the Translation Proxy … configure what to serve on this domain"** (a 404,
  "Unrecognized domain") on a language host means its DNS still points at Easyling but no
  published language serves that host: the language was unpublished or its domain changed. It is
  self-service: republish it in the Publish wizard, have the domain owner enter any DNS records
  the wizard lists, and let the same user verify. The dashboard's audit log shows who changed it.
- **Before sending forwarding snippets or DNS records, ask for the CMS and the host.** Some
  managed WordPress hosts allow no reverse proxy or CDN rules; the WordPress plugin is the route
  there, and it works under the host's page cache. Subdirectory publishing needs no DNS change,
  and the site's own certificate covers the language folders.
- **Before DNS can change** (a slow change process, a locked registrar account), the language's
  temporary domain can be linked from the site as a stopgap. Never link a `-p` preview.
- **Linked projects** (a blog or shop on its own subdomain) are published together, in the same
  languages, or links between them break.

## 3. Publishing in a subdirectory

The translations appear under the origin's own domain (`example.com/fr/`). The customer's reverse
proxy or CDN sends each language folder to that language's temporary domain; everything else goes
to the origin as before.

- **The snippet**: Dashboard → Publish → the language → Publish wizard, subdirectory mode
  *(no MCP tool)* generates the configuration for nginx, Cloudflare Workers and AWS CloudFront,
  with the project's own hosts. Copy it from there. The forwarded request sets `Host` to the
  temporary domain and carries `X-TranslationProxy-ServingDomain` (the public host),
  `X-TranslationProxy-EnableDeepRoot: true`, `X-TranslationProxy-AllowRobots: true` and
  `X-TranslationProxy-Cache-Info: disable`.
- **Cloudflare**: turn Rocket Loader off. **CloudFront**: cache on the headers the wizard lists,
  use the origin's cache headers, forward all query strings.
- **WordPress**: the Easyling plugin does this forwarding from inside WordPress, with no CDN.
- Publishing fills `restrictions.translationPathPrefixes` with the language folders, so the
  proxy never treats a translated page as source; it answers 410 for those folders when asked to
  fetch them from the origin.
- **Not at the root** (translations under `/site/section/fr/` for a project scoped to
  `/site/section/`): set the custom subdirectory prefix in the wizard, then the original path
  prefix in the language's settings tab. The link transformation preview shows the resulting URLs
  before publishing.
- **Translated URL segments** (`/products/` → `/produits/`) are set per language in the same
  settings tab, up to 50 segments.
- `mapResourcesToRemote` must stay on: subdirectory publishing relies on scripts, styles and
  images loading from the origin.
- **A site on its bare domain** (`example.com` with no `www`) cannot point a CNAME record at a CDN.
  Its DNS provider has to support CNAME flattening (ALIAS or ANAME records, by provider) before a
  CDN can carry the subdirectory forwarding; check that early.
- **A local cache build** (a Scan that stores a snapshot of the origin) fails with a crawl root
  depth of 1 on a subdirectory-published project; set the root depth to 0.
- **Test**: a language folder that answers 404 without an `x-translationproxy-trace-id` response
  header never reached Easyling; the customer's forwarding rule is missing. A staging site needs
  its own forwarding, and its host added to the project.

## 4. Staging domains

Dashboard → Project overview → Staging domains *(no MCP tool)*.

- A staging domain set as **default** is what previews and crawls fetch from; set as **live
  default**, the published site is served from it too.
- Translations carry over only where the staging site's paths match the live site's exactly.
- Use one to translate content before it is released, or to follow a change of the origin's
  domain without a new project.

## 5. Traffic and caching

Every HTTP request through the proxy counts, so keep what need not pass through out of it.

- **Without a snapshot or a cache rule, every request is fetched from the origin**, and the page
  is held only in memory while it is translated; the project stores the page list, the collected
  text and its translations, not the pages. A CDN the customer runs in front of the language
  hosts can cache translated pages and be purged by the customer.

- `mapResourcesToRemote` (on for new projects) sends scripts, styles and images straight to the
  origin. The class `__ptNoRemap` on an element keeps its link pointing at the origin.
- **Public caching** for static files, per path, with `managePathPrefixOverrides setOverrides`:
  `cacheOverride` with mode `public` and a `maxAge`, together with `cookieOverride` (a response
  that sets a cookie is never cached publicly) and `varyOverride` mode `restrict` (a `Vary` on
  anything but `Accept` and `Accept-Encoding` also blocks it). First read
  `pathPrefixOverrides describeSlots` for the value shapes and `pathPrefixOverrides resolve` for
  the record a URL gets now: exactly one record applies per request, and a new, narrower path
  takes requests away from a broader one together with all its slots.
- **A cached copy cannot be recalled.** Browsers and caches outside the customer's control keep
  it until `max-age` runs out. Cache
  versioned files for long, unversioned files for hours, popular HTML pages for 10 to 60 minutes
  at most, and never cache logged-in areas, carts, search results or API responses.
- `allowCachedRemoteContent` lets the origin's own CDN answer the proxy: less load on the origin,
  but a changed page can be served stale until that cache expires.
- **Snapshots** (Dashboard → Snapshot *(no MCP tool)*) decide what is shown while translation
  catches up:
  - an *origin snapshot* is a stored copy of the source pages, built by a Scan, that the proxy
    translates instead of the live origin, so new source content does not appear until the
    snapshot is rebuilt;
  - a *translation snapshot* stores translated pages as live visitors request them and serves
    them while the origin page is unchanged: faster, but new translations show only after the
    page is cleared from it;
  - its *keep cache* strategy, when the origin page changes, serves whichever version is better
    translated, so untranslated text does not bleed through.
- **Bots**: stale content for good bots, blocking bad bots by user agent (a Java regular
  expression; never `||`, which blocks everyone), and how excluded pages answer (source,
  redirect, 404) are set in Dashboard → Publish → Global settings *(no MCP tool)*.

## 6. Headers, cookies and the origin

- **The site's API fails through the proxy but works on the origin**: the proxy forwards only
  known request headers. Add the missing ones (lowercase) to
  `customHeaders.allowedRemoteRequestHeaders`.
- **Response headers**: Content-Security-Policy, X-Frame-Options and custom API headers are dropped
  unless listed in `customHeaders.allowedLocalResponseHeaders`. A forwarded policy that names only
  the original domain can block the translated page's own resources.
- **Cross-origin calls**: a page script that calls the origin's host from the translated host is
  blocked by the browser; find the URL with `projectSettings testJsonPaths` and
  mark it as a `url` rule in `jsonSearchPaths` (`manageProjectSettings update`) so it points at
  the translated host.
- **Shared login, cart or consent across languages** on subdomains: `allowLiveUpperDomainCookieSetting`
  keeps cookies set for the main domain.
- **An origin that varies content by language** reads the `X-TranslationProxy-Translating-To`
  request header, or the cookie `sendTargetLanguageCookie` adds.
- **Firewalls and bot protection** in front of the origin must let the proxy through. Requests
  come from Google's changing addresses with `AppEngine-Google` in the user agent; ask the
  customer to tell their security provider. A fixed outgoing address (a gateway) is arranged by
  Easyling support.
  - The proxy fetches through the origin's public hostname; an origin reachable only at a private
    or internal address cannot be used.
  - The proxy passes on every visitor request and never throttles or backs off by itself, so a
    rate limit or a bot challenge on its traffic breaks translated pages. Exempt that traffic
    rather than tune the limit.
  - **Allowlisting Easyling opens a path to the origin.** Whatever the allowlist matches (the
    user agent, a secret header, the gateway address), anyone who can reach a translated host
    passes it. Pair it with filtering in front of the language hosts: a WAF or CDN the customer
    runs there is supported and recommended, as long as it forwards to Easyling with the request
    headers the Publish wizard lists.
- **Streaming responses** are not supported.
- **Password protection** for previews or the live site: Dashboard → Publish → Access control
  *(no MCP tool)*.

## 7. SEO

- **The proxy adds no `hreflang` links to translated pages**; the origin's own `hreflang` links
  pass through unchanged. Language alternates come from the multilingual sitemap the proxy offers,
  from the site's own template (which must then list every language, reciprocally), or from the
  crest script, which inserts them wherever it runs. The proxy does translate meta descriptions.
- `canonicalLinkInExternalizedPages` (on for new projects) points excluded pages' canonical link
  at the original, so the untranslated copies are not indexed as duplicates.
- **SEO overrides**: per-path, per-language title and description, edited in a linked Google
  Sheet: Dashboard → SEO overrides *(no MCP tool)*. Keep the toggle off until the sheet is
  imported.
- **The `<html lang>` value** can be shortened per language (`de` instead of `de-DE`) in the
  language's publishing settings.
- Search engines find the languages only after publishing; preview hosts are not for indexing.

## 8. Changing pages on the way out

| Need | How |
|---|---|
| CSS or JavaScript on every page | `injectedStylesheet`, `injectedStylesheetURLs`, `injectedJavascript`, `injectedJavascriptURLs` with `manageProjectSettings update`. Writing inline CSS or JavaScript replaces what is there; make CSS rules language-specific with `html[lang="de-DE"]`. A broken script breaks every translated page. |
| CSS or JavaScript under one path | The `contentInjection` slot of `managePathPrefixOverrides setOverrides`. |
| A different text or embed per language (a video id, a form id) | The `contentSearchAndReplace` slot, with `targetLanguages`. Test with a throwaway query string (`?test=1`) to get past caches. |
| A page or file that does not exist on the origin (a verification file, a script to inject, a placeholder page) | `managePageContentOverrides put`. It replaces the whole response at one exact URL and the stored body is the only copy: read it with `pageContentOverrides list` (`exactUrl`, `includeBodies`) first. Omit `targetLanguage` for all languages. Text only; give it a public cache header, because each request to it counts. |
| A translated image or file | Dashboard → Pages → Resources *(no MCP tool)*; see [launch](launch.md). |
| A language selector | Dashboard → Language selector *(no MCP tool)*: a sidebar or a dropdown added with one script tag on the origin, or the site's own links. Give the link back to the source language the class `__ptNoRemap` so the proxy does not rewrite it. |
