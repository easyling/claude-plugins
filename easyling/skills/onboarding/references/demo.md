# Preparing a demo

Given a project code, prepare a demo of the customer's site in a target language: a few
representative pages collected and translated, a serving-mode recommendation, and a document to
run the demo from, with the questions to ask the customer. Work the intake out from the project
and the site instead of asking the user for it; what neither can answer becomes a question for the
customer.

## Contents

1. Read the project
2. Read the site
3. Choose the pages
4. One plan, one approval
5. Set up translation before collecting
6. Collect and translate
7. Check the result
8. The demo document
9. Before and after the demo

## 1. Read the project

- **`projects list`.** If the project is missing or answers "Project is not accessible", the
  MCP's project list is older than the project: ask the user to reconnect the MCP (in Claude Code,
  `/mcp`) and stop until they have. Never carry on with a similar-looking project.
- From the listing: the domain (the origin), the source locale, the target locales and the active
  technologies. With no target language, stop: Dashboard → Target languages *(no MCP tool)*. With
  several, demo the one the request names, or the first, and say which.
- **`projects subscription`**: the word allowance left. The demo adds every word it collects;
  plan for headroom.
- **What is there already**: `projectSettings get` (scope, `autoTranslateConfig`, attributes,
  ignore rules), `crest getConfig` (the ingestion flags), `aiTranslationConfig listSlots`,
  `linguisticResources listProjectResources` (glossaries and memories), and `entries search` for
  content already collected. Reuse what exists; change only what the demo needs.

## 2. Read the site

Load the home page and one inner page, and read the response headers and the page source. Each
finding feeds the serving decision ([serving mode](serving-mode.md)) or a question.

| Signal | Means | What follows |
|---|---|---|
| `x-powered-by: Next.js`, `x-nextjs-*` headers, `/_next/static/` assets | Next.js | A hydrating framework: crest |
| `self.__next_f` in the HTML (and no `__NEXT_DATA__`) | Next.js App Router | Navigation fetches component payloads, not pages: the proxy cannot follow it. Crest |
| An almost empty `<body>` with a root element, `ng-version`, `data-v-` attributes | A single-page app | Crest |
| `/wp-content/`, `/wp-json/` | WordPress | The Easyling WordPress plugin is an option |
| `x-sc-*` headers, an `sc_site` cookie, `edge.sitecorecloud.io`; `/etc.clientlibs/`, `/content/dam/`; `X-Generator: Drupal`; `cdn.shopify.com` | Sitecore, Adobe Experience Manager, Drupal, Shopify | Ask whether the CMS's own language support is in use or planned |
| `x-vercel-id`, `x-nf-request-id`, `x-amz-cf-id`, `cf-ray`, `akamai-*` headers | Vercel, Netlify, CloudFront, Cloudflare, Akamai | Who changes routing, for subdirectories or a CDN route |
| `incap_ses_*` or `visid_incap_*` cookies, `x-iinfo`; a bot challenge page | Imperva or another firewall | Check that the preview loads (section 6); ask the customer to allow Easyling for crawls and the proxy |
| `hreflang` links, locale folders in the sitemap, a language switcher, a locale in some paths | The site is already multilingual somewhere | Ask why those languages are not used, and keep their pages out of scope |
| A consent banner, chat, review, booking or call-tracking widget | Third-party content | Usually localized by its vendor, or not at all: one question each |

`robots.txt` names the sitemaps. Group their URLs by the leading path segments: each group is
usually one page template, and the counts size the site.

## 3. Choose the pages

- **One visitor's story.** Six to ten views that follow the site's main purpose from the home
  page to the point of contact, for example for a hospital group: a department, a condition, a
  test, the specialist finder, a specialist's profile, a hospital, information for patients from
  abroad. The customer judges the demo by the pages their visitors use.
- **One page per template**, the templates with the most URLs first, so the demo also shows how
  the rest of the site will look.
- **At least one state behind an interaction**: search or finder results, a filter panel, a
  dialog ([content collection](content-collection.md), section 4). This is where single-page
  apps differ from what a crawl sees.
- **Leave out** pages behind a login, forms that send anything, error pages (opened in a preview
  they become content), and pages full of personal data.
- **Size it.** Count the words each chosen page shows, the navigation and footer once, and
  multiply by its template's URL count. Call the total an estimate: the figure for a quote comes
  from a Discovery ([assessment and quote](assessment-and-quote.md), section 1).

## 4. One plan, one approval

Before the first write, show one plan and wait for one explicit yes:

- every change from sections 5 and 6, each with its dry run where the tool has one, run now and
  shown in the plan;
- the cost: the source words the collection adds (from section 3), the AI translation of each of
  them, and the paid test calls.

That yes is the write gate's yes for the changes listed, and only for those. Make each one, read
it back and report what is stored; anything not in the plan, or a change whose dry run differed
from the plan, goes through the gate on its own. Ask the user only what blocks the plan: a missing
target language, an allowance too small for the pages, a site that refuses the preview.

## 5. Set up translation before collecting

A stored translation keeps the wording it was made with. The styleguide and the glossary reach
only translations made after them, so set them up first; otherwise the demo shows translations
that ignore them until the scope is re-translated.

1. **Scope.** `projectSettings checkScope` with the chosen URLs: each must be in scope.
2. **Settings that shape collection** ([setup and scope](setup-and-scope.md)): attributes that
   carry text the project does not translate yet (often `aria-label`), and a third-party consent
   banner kept out with `ignoreIds`, listed as a question for the customer.
3. **AI translation**: load the account's engine credentials into the project with
   `manageAiTranslationConfig loadAccountCredentials` (OpenAI is recommended); when its
   `effectiveEngine` is another engine, pin the loaded one as its warning says. Check the engine
   that actually runs with one `aiTranslationConfig testTranslate`. The linguistic-quality skill's
   AI translation reference has the steps.
4. **A styleguide** for the target language, written for the site's field: form of address,
   names of places, people and products, abbreviations, units, dates and times. Each rule is a
   proposal for the customer to confirm.
5. **A starter glossary** (the linguistic-quality skill's glossary reference): the brand, product
   and place names as do-not-translate terms, plus a handful of the field's key terms as
   proposals. Leave short abbreviations to the styleguide. Publish it, then check it with
   `linguisticResources lookupGlossary` and the same `aiTranslationConfig testTranslate`.
6. **Auto pre-translate and AI translation on** with `manageProjectSettings update`, so collected
   text is translated as it arrives; the linguistic-quality skill's AI translation reference names
   the switches.
7. **Collection on.** `enableCrestMissingReport` and `enableCrestMissingFetch` on with
   `manageProjectSettings update`.

## 6. Collect and translate

- **Open each chosen page in the target-language `-v` preview** in a browser, and exercise the
  chosen states ([content collection](content-collection.md), sections 3 and 4). If the preview
  shows a firewall's challenge or an error instead of the page, stop: the customer has to allow
  Easyling first.
- **Let crest finish before moving on.** A cold preview can take 15 seconds or more before the
  page is translated or reported. With a browser automation tool, open several pages as iframes
  inside one `-v` page of the same host, start the batch without waiting on it, and check back.
  Without one, give the user the links and the states to exercise, and wait for them.
- **The AI works in the background**, for minutes. Follow it with `entries listByPage` per page
  until nothing is left untranslated.
- **Then turn `enableCrestMissingReport` off** and keep `enableCrestMissingFetch` on. The `-v`
  preview carries no translations of its own: it fetches the stored ones through the endpoint
  Fetch keeps open.

## 7. Check the result

- **Per page, list what is still in the source language** once crest has finished, and find why:
  a state not collected, a third-party widget or frame, an excluded block, or a translation still
  on its way. Judging a page before crest has finished reports false gaps.
- **Read the translations for terminology**: names that were translated and should not have been,
  abbreviations, addresses, times and dates, units. Each one is either fixed now (glossary or
  styleguide, then the stored text corrected) or listed for the customer to decide.
- **Export only when the user asks.** The `-v` links need no export. If they want the script
  published (`manageCrest startExport`), the language stays hidden until its Show switch is
  turned on, so nothing changes for the customer's visitors.

## 8. The demo document

Write it where the user can share it (a document, a page or a file), with these sections:

1. **Recommendation**: the serving mode, with a short comparison for this site and the signals
   from section 2 behind it. Say what SEO looks like under the recommendation.
2. **Demo flow**: one `-v` link per page in story order, with what to show on each: a translated
   state, a term from the glossary, a styleguide rule at work.
3. **Questions for the customer**: a table with the question, why it matters and an empty answer
   column. Build it from the findings: every unknown from sections 1 to 7 is one row. Add the
   ones that apply from [assessment and quote](assessment-and-quote.md), section 3, and
   [serving mode](serving-mode.md), "Questions to settle": the language variant and its
   audience, SEO, the CMS's own languages, who approves terminology and tone, existing glossaries
   or memories, the sections in scope, third-party widgets, who places the script tag, the
   new-content policy and the timeline.
4. **Sizing**: templates and their URL counts, the words of the demo pages, the estimate and its
   limits. No prices: plans and fees come from Easyling sales.
5. **Before the demo**: the checklist in section 9.
6. **Known gaps**: what the demo does not show yet, and why.
7. **Terminology to confirm**: the glossary proposals and the open wording decisions.
8. **What is configured**: each setting, slot, glossary and flag the demo depends on.

## 9. Before and after the demo

Before:

- Open every demo link once, shortly before the meeting, so the first load is not the slow one.
- `crest getConfig`: Report off, Fetch on. `entries listByPage`: nothing left to translate.

After:

- Put the customer's answers in the document's answer column.
- Apply the confirmed terms and rules, then re-translate the demo pages so the stored text
  follows them: Dashboard → Pre-translate *(no MCP tool)*. Export again if a script was
  published.
