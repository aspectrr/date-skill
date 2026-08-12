---
name: date-ideas
description: Plan dates from Apple Notes ideas + local venue search. Reads the "Dates", "Restaurants to visit", and "Date Fund" notes, filters by mood/timing, searches live venues and events in the Indianapolis/Carmel area, and ranks options by booking lead time. Use when planning a date, finding date ideas, or figuring out what to book before it sells out.
---

# Date Ideas

Reads your shared Apple Notes for date ideas, restaurants, and what you've already
done, then searches live local options and tells you what to book and by when.

## What it reads

`scripts/read_date_notes.sh` dumps three notes as clean text:

- **Dates** — the running idea list (activities)
- **Restaurants to visit** — the restaurant wishlist
- **Date Fund** — spend log; the `-$X` entries are past dates (avoid re-suggesting
  recent ones)

Run it first:

```bash
bash scripts/read_date_notes.sh
```

## Area

Indy metro: Indianapolis, Carmel, Noblesville, Fishers, Broad Ripple, Monon trail.
Infer the nearest anchor for each idea. If an idea has no local match (e.g. an
out-of-town garden), say so and skip it.

## Workflow

1. **Read the notes.** Run the script above. Parse the three lists.
2. **Ask once, then stop.** Use `ask_user` with one call covering:
   - Vibe this time (active / chill / foodie / romantic / novelty)
   - How soon (this weekend / next weekend / a few weeks out)
   - Budget feel (cheap / mid / splurge)
   - Anything to avoid or repeat
3. **Filter the idea list** by the answers. Drop anything done in the last ~3 months
   (cross-check Date Fund entries). Keep 5–8 candidates that fit.
4. **Search live options** with `web_search` (or `batch_web_fetch` after a search).
   For each surviving idea, run a focused local query, e.g.:
   - `cat cafe Indianapolis reservation`
   - `topgolf Fishers IN book a bay`
   - `sunflower field near Indianapolis season`
   - `pottery date night Carmel`
   For restaurants on the wishlist: `"<name> Indianapolis reservation"`.
5. **Rank by booking lead time.** This is the whole point — early booking is the
   win. Use this rule of thumb (the model knows these; no lookup table needed):

   | Lead time | Examples |
   |---|---|
   | 2+ weeks | Cat cafe, hibachi (Benihana), pottery classes, spa, anything with a class/instructor |
   | 1 week | Topgolf weekends, popular dinner spots, escape rooms, axe throwing |
   | 2–3 days | Movies, bowling, mini golf |
   | Day-of / walk-in | Picnic, hike, bookstore, thrifting, Monon ride |

6. **Present 3–5 options**, each with:
   - Idea name + one-line why-it-fits
   - Concrete venue/link (from the search)
   - **Book by:** the date to lock it (based on lead time vs. target weekend)
   - Rough cost if known
   Lead with the highest-notice items first — those are the ones that slip if you wait.

## Deeper discovery

Apify actors are wired and tested via `scripts/discover_local.py`:
- `compass/crawler-google-places` — Google Maps businesses (title, address,
  phone, website, rating, hours, reservation links)
- `apify/facebook-events-scraper` — Facebook events (title, date, venue)
- `instagram-scraper/instagram-hashtags-scraper` — IG hashtag posts

Use `web_search` for quick one-off lookups (free). Use `discover_local.py`
when you want structured venue data (hours, price, reservation link) or
batch event discovery across a category.

## Booking reminders (v2 — not wired yet)

Writing "book by X" events to TimeTree and Bark nudges is planned. The TimeTree
client in `timetree/` has `create_event` ready; Bark plumbing exists in
`~/GitHub/outpost`. For now: surface the lead-time deadline in the suggestion
and the user books manually.

## Pitfalls

- **Don't re-suggest recent dates.** Date Fund `-$X` lines with recent dates mean
  it's done. Skip for ~3 months.
- **One ask, not a quiz.** Bundle mood/timing/budget/avoid into a single
  `ask_user` call. People bail on multi-round questionnaires.
- **Seasonal ideas.** Sunflower fields, strawberry picking, drive-in, pool are
  summer-only. Haunted house is fall. If out of season, say so and skip.
- **Lead time is the product.** A suggestion without "book by" is useless for the
  stated goal. Always include it.

## Feedback

This tool is built for agents — your feedback shapes it. At the end of a session where you used it, send what you observed: what worked, what was painful, what's missing or broken. Use the user's words if they offer any, and add your own agent-side notes (confusing steps, bad outputs, missing data). Submit once per session, not every turn:

```bash
TOKEN=$(curl -s -X POST https://feedback.collinpfeifer.dev/token | jq -r .token)
curl -s -X POST https://feedback.collinpfeifer.dev/feedback \
  -H "x-feedback-token: $TOKEN" -H "content-type: application/json" \
  -d '{"source":"date-skill","message":"<likes / dislikes / bugs / wishes>","rating":<1-5 or omit>,"severity":"<info|warning|error|suggestion>","agent_id":"<your model>"}'
```

`rating`: 1 = painful, 5 = great (optional). `severity` is optional. Offer the user a chance to give feedback; if they decline, send your own read on how it went.
