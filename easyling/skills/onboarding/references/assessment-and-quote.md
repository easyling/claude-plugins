# Assessment and quote

Size the site before anything is stored. A quote is for the words that will be translated, and
every word a project stores counts against its plan, so measure first and collect second.

## Contents

1. Discover before you scan
2. Read the numbers
3. What a word count does not show
4. Traffic through the proxy
5. The plan size
6. What the quote should say

## 1. Discover before you scan

- **Discovery** (word count) crawls the site, lists its pages and counts words, but stores no
  content. **Scan** (content extraction) stores every new source word, and stored words count
  toward the project's word allowance. Start with a Discovery: Dashboard → Crawl *(no MCP tool)*.
- **Always set a page limit.** Start small (100 pages), read the result, add rules, raise the
  limit and run again. Forums, shops, calendars, filters and search result pages can generate
  pages without end; an unlimited crawl on an unknown site is the expensive mistake.
- **Before the first crawl**, keep duplicates and out-of-scope areas out (see
  [setup and scope](setup-and-scope.md)): excluded prefixes, page grouping, ignored query
  parameters. Pages excluded during a Discovery are not picked up again by changing the rules
  alone; add them back with a single-page crawl: Dashboard → Pages → Add new *(no MCP tool)*.
- **Read the crawl log**, not only the totals: pages skipped for their content type, pages that
  failed (externalized, too large, could not be parsed) and redirects all change the picture.
- **The site blocks the crawler.** Crawls come from Google's changing addresses with a user agent
  that contains `AppEngine-Google`. A firewall, bot manager or host-level rate limit can block
  them; the customer allows them, or asks Easyling support about a fixed outgoing address.
- **Content behind a login** can be crawled with the session cookie of a logged-in preview
  visit (see [content collection](content-collection.md)). Cookies expire, so this does not
  automate.

## 2. Read the numbers

- **Unique words = total minus 102% repetitions.** A 102% repetition is a whole block seen
  before, such as the navigation or footer on every page. It is stored once and translated once,
  so it never belongs in the quote.
- The other levels are partial savings: 101% (same segment, same neighbours), 100% (same segment
  and tags), 99% and 98% (fuzzy: case, numbers or tags differ).
- **Multiply by the number of target languages** for the translation volume.
- **After a Scan, the MCP can count what is left to translate.**
  `manageWorkPackageSets createFromScope` with `targetLanguages`, `translationStates` exactly
  `["notTranslated"]` and a scope (`pathPrefixes` or `urls`; a bare `/` is refused, because it
  means the home page only), then poll `workPackageSets list` until `generationFinished` and read
  `wordCountByLanguage`. It needs the export privilege, opens a new contract index on the
  project, and the set cannot be deleted over MCP, so give it a clear name and run it through the
  write gate.
- `projects subscription` reports the source words already used against the allowance.

## 3. What a word count does not show

Go through the site with the customer. Each "yes" is work beyond translation.

| Question | Why it matters |
|---|---|
| Is content rendered by JavaScript, or loaded as JSON or XML? | A crawl reads the HTML the server sends. Such text is missing from the count until it is configured (proxy) or collected in a browser (crest). |
| Is there text in images, video, PDFs or other files? | Files are not extracted. They are replaced per language with localized copies. |
| Are there widgets from other domains (forms, booking, chat, maps)? | Content from another domain needs its own linked project, or the vendor's own localization. Text inside an iframe from another domain is never collected. A widget its vendor localizes (a map, for example) shows the language the vendor detects for the visitor, not the one chosen on the site; tell reviewers, so they do not report it as a fault. |
| Will another vendor translate some languages outside Easyling? | Possible, but work on both sides: the other vendor's translated pages must be kept out of collection, or Easyling stores their text as new source. One route for all languages is simpler. |
| Is there content behind a login, per user, or by region? | Needs session cookies or a staging copy; personal data must stay out of translation. |
| Is there site search, a shop, a forum or a web app? | Search over translated text needs its own solution; shops and apps need their API calls checked. |
| Are there subdomains (`blog.example.com`)? | Each host with its own content is a separate, linked project. |
| Is any content in more than one language? | Decide which language is the source; text in other languages should be kept out. |
| Do target texts run much longer, or right to left? | Layout fixes: CSS per language, sometimes a dedicated right-to-left stylesheet. |
| Is there a translation memory to reuse? | Lowers the translation effort; it is attached to the project. |
| Are strings built in JavaScript (`"You have " + n + " items"`)? | Computed strings cannot be translated by the proxy. |
| How should new content be handled? | Shown in the source language until translated (bleedthrough), or held back. Decide now; it shapes the setup. |
| Are bots a large share of traffic? | On the proxy every bot request counts too. |
| Is there a chatbot? | Not supported and not counted: its dialog is per session, and visitors' questions would grow the word count without limit. The bot is localized in its own backend; quote only the page around it. |

## 4. Traffic through the proxy

Only for proxy serving; crest pages come from the customer's own server.

- **Every HTTP request that reaches the proxy counts**: HTML, scripts, styles, images, API calls,
  errors and bots. Page views in the customer's analytics are not the unit.
- **Estimate it from one page.** Open a typical page with the browser's network panel, reload,
  and keep only requests to the site's own host. By default the proxy sends scripts, styles and
  images straight to the origin (`mapResourcesToRemote`), so what remains is usually the HTML
  and the site's own API calls. Multiply by the expected visits per translated language, and add
  bot traffic.
- Publicly cacheable static files and a short cache on popular pages lower the count (see
  [serving through the proxy](serving-proxy.md)); dynamic responses and logged-in pages cannot be
  cached.

## 5. The plan size

- Size the plan on **unique source words** plus the growth expected before the next review, times
  the target languages, and on the proxy also on the expected page requests.
- **Leave headroom.** Over the word limit Easyling stops collecting new content, on the proxy and
  on crest alike, and nothing on the site says so: new text simply stays in the source language.
- **Keep text that need not count out of the project** before the Scan: user names, dates,
  prices, phone numbers, addresses (ignore rules and patterns in
  [setup and scope](setup-and-scope.md)).
- **Plans, fees and what each plan includes come from Easyling sales.** Never name a setup fee,
  an add-on or a price yourself; pricing changes, and a figure in a quote becomes a promise.

## 6. What the quote should say

1. Unique words, target languages, pages in scope, and what was excluded.
2. The technical items found in section 3, each with its effort.
3. The recommended serving mode ([serving mode](serving-mode.md)) and what the customer must do
   for it: DNS records, a script tag, a reverse proxy or CDN rule.
4. The new-content policy and how updates will be collected and translated.
5. The work beyond translation, without figures: layout adjustment where needed (always for
   right-to-left languages, often for Chinese, Japanese and Korean) and any custom work. The plan,
   its fees and what it includes come from Easyling sales.
