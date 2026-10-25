# Never Late API (copy of the backend's docs page)

Copied from `GET /` on https://never-late-api-966291054830.us-west1.run.app on 2026-10-24, first at `/health`
version `never-late-api-00006-rkf` (v1 only), then updated at `never-late-api-00008-8nc` (adds v2), converted from
HTML to Markdown. **This Skill uses v2** (requests include `modes`); the v1 sections below are kept for reference. The live page is
authoritative; if it changes, re-copy it. This file is for the team; Cubbie does not need to read it.

Before each class, ask this API *when to leave*. It returns the route for the student's travel mode, a backup,
other modes, and weather for the trip. Cubbie turns the answer into a short alert. v1, JSON over HTTPS.

## Quick start

Two endpoints do the work. `POST /v2/plan` returns candidate journeys and lets the skill choose; `POST /v1/plan`
picks for you. The example below is v1; the v2 request is in its own section.

```bash
curl -s -X POST "$BASE/v1/plan" \
  -H "x-skill-token: $TOKEN" -H "content-type: application/json" \
  -d '{
    "origin":      {"label": "Home",     "address": "1111 E Apache Blvd, Tempe, AZ 85281"},
    "destination": {"label": "HLMK 120", "address": "660 S College Ave, Tempe, AZ 85281"},
    "arrive_by": "2026-10-26T09:00:00-07:00",
    "primary_mode": "TRANSIT",
    "alternative_modes": ["WALK", "BICYCLE"]
  }'
```

| Endpoint | Auth | Purpose |
| --- | --- | --- |
| `POST /v2/plan` | `x-skill-token` header | Recommended. Candidate journeys with ISO times; the skill chooses |
| `POST /v1/plan` | `x-skill-token` header | Backend picks a primary route and a backup |
| `GET /health` | none | Liveness check, returns version |
| `GET /client.py` | none | Ready-made Python client for Cubbie's sandbox |
| `GET /` | none | This page |

> **About the token.** It is a speed bump, not real security, because a Skill repo is public. Abuse protection is
> the rate limit (10 requests/min per token and IP), a cap on instances, and Google quotas. Keep the token in
> Cubbie's secrets, not in the repo, if you can. Ask the service owner for the token; it is never shown on this page.

## Recommended: `POST /v2/plan` (journeys, you choose)

v2 does not pick a primary, a backup or a suggestion. It returns the candidate journeys with exact ISO times and
honest `on_time` flags, and the skill decides what to tell the student. `/v1/plan` (below) still exists if you
want the backend to choose.

### Request

```json
{
  "origin":      { "label": "Home", "address": "full address", "lat": null, "lng": null },
  "destination": { "label": "HLMK 120", "address": "660 S College Ave, Tempe, AZ 85281", "lat": 33.4195, "lng": -111.9365 },
  "arrive_by": "2026-10-26T08:50:00-07:00",
  "modes": ["TRANSIT", "WALK"],
  "buffer_min": null,
  "now": null
}
```

| Field | Rules |
| --- | --- |
| `origin`, `destination`, `arrive_by`, `now` | Same as v1 (address or lat/lng; `arrive_by` needs a UTC offset). |
| `modes` | 1-4 unique values of `TRANSIT`, `WALK`, `BICYCLE`, `DRIVE`. Default `["TRANSIT","WALK"]`. Every requested mode that has a route comes back as journeys. |
| `buffer_min` | Optional 0-60. How early the student wants to arrive. Transit options are searched so the last bus arrives this long before `arrive_by`; walk/bike/drive `leave_by` includes it. Defaults: TRANSIT 3, WALK 3, BICYCLE 5, DRIVE 10. |

### Response

| Field | Meaning |
| --- | --- |
| `ok`, `data_quality`, `fallback_needed`, `fallback_hint`, `degraded`, `error`, `maps_link` | Same meaning and same error codes as v1. `data_quality` is `scheduled`, `no_transit` or `error`. |
| `generated_at` | ISO time with offset. |
| `trip` | `origin_label`, `destination_label`, `arrive_by` (ISO), `timezone` (IANA name such as `America/Phoenix`, when known). |
| `journeys[]` | Candidate options, each with `id` (`journey_1`...), `mode`, `provider` and `route` (transit), `leave_by`, `arrive_at` (ISO), `total_min`, `on_time`, `steps[]`. Transit options come first, latest departure first, then the other modes in the order you asked. The order is a convenience, not a recommendation. |
| `steps[]` | Walks: `type`, `minutes`, `text`. Transit steps: `provider`, `route`, `direction`, `boarding_stop`, `destination_stop`, `depart_at`, `arrive_at` (ISO), `realtime` (false), `source` (`google_routes`), `availability` (`UNCERTAIN`), `service_alerts_checked` (false). |
| `weather` | Taken from the first journey's times: `at_departure` / `at_arrival` (ISO `time`, `temp_f`, `condition`, `precip_pct`, `wind_mph`), `severity`, `impact`, `alerts[]` (NWS warnings: `event`, `headline`, `severity`, `starts`, `ends`). Each journey's `leave_by` already includes its own weather buffer. |
| `verification` | Present when there is a transit journey: `transit_schedule_source`, `service_alerts_checked`, `live_vehicle_tracking`, `official_schedule_verified` (all false except the source). Use it to word certainty honestly. |

### What the backend does and does not do

**Does:** ask Google for up to several transit routes that arrive by the deadline, drop any that the student can
no longer catch (the bus has left or the walk to the stop is too long), keep up to 3 on-time transit options (or
the 2 earliest late ones if none are on time), compute exact `leave_by`/`arrive_at` with weather buffer, and
attach provenance flags.

**Does not:** choose a primary, pick a backup, compare modes or write a suggestion. The skill decides: for example
take the first on-time journey as the plan, the next on-time one as the backup, and word urgency from `arrive_at`
versus `arrive_by`.

**Backup is now just another journey.** Any later on-time journey in the list is a backup; if there is only one
on-time transit journey, there is no on-time backup.

**Different providers:** `provider` is whatever Google reports (for example Valley Metro, even for Orbit lines).
Don't hardcode names.

### Client with v2

Put `"modes"` in the request body and `never_late.py` calls `/v2/plan` automatically. It prints
`action: "journeys"` with `options` (one short line per journey) and the full `data`. No alert text is written for
you; the skill words it. Fallback and error handling are the same as v1.

The docs page shows a trimmed live response; our full captures are `../assets/sample_ok.json` (three transit
journeys plus walk and bike), `../assets/sample_short_trip.json`, `../assets/sample_no_transit.json` and
`../assets/sample_error.json`.

## v1: `POST /v1/plan` (backend picks primary and backup)

Everything below describes v1. It still works unchanged; this Skill no longer uses it.

## Using it in a Cubbie Skill (v1)

Cubbie runs a small Python script in its sandbox. The script calls this API and returns one JSON object with an
`action`, so the Skill only needs to branch on three values.

1. **Collect** the student's next class: place, address (or lat/lng) and start time, plus where they are leaving
   from and how they travel.
2. **Build** the request body. `arrive_by` is the class start time with the local UTC offset.
3. **Run** `never_late.py` with the body. It retries once and never crashes.
4. **Branch** on `action`: send the alert, or run Cubbie's own web search.

| `action` | Exit | What Cubbie does |
| --- | --- | --- |
| `send_alert` | 0 | Text `message` to the student. Optionally add `maps_link`. |
| `web_search_fallback` | 3 | Do a web search guided by `search_hint`. If `message` is present it lists alternatives the API did find (for example, driving time). |
| `fix_input` | 2 | Bad request or bad token. Don't retry or search; fix the call. |

### Paste into your Skill instructions

```text
When the student asks "when should I leave?" or before a class alert:
1. Build a JSON request: origin (address or lat/lng), destination (address or lat/lng),
   arrive_by (class start, ISO 8601 WITH UTC offset, e.g. 2026-10-26T09:00:00-07:00),
   primary_mode (TRANSIT, WALK, BICYCLE or DRIVE; default TRANSIT),
   alternative_modes (0-3 of the others).
   Use labels like "Home" or "HLMK 120" for display only. Never put school-specific data in code.
2. Run: python3 never_late.py request.json   (env NEVER_LATE_URL and NEVER_LATE_TOKEN set)
3. Read the JSON it prints:
   - action = send_alert          -> send "message" as the alert. Keep it to 1-3 short lines.
   - action = web_search_fallback -> search the web using "search_hint", then answer. Mention the
                                     alternatives in "message" if present. Say the info is less exact.
   - action = fix_input           -> do not retry; tell the developer, not the student.
4. If primary.on_time is false in data, say so plainly and lead with the faster option.
```

> **Tip: use the raw data too.** The script's output includes `data`, the full API response. Use it when you want
> to word the alert yourself: `primary.leave_by`, `primary.steps`, `primary.backup`, `weather.impact`, `suggestion`.

## Request: `POST /v1/plan`

```json
{
  "origin":      { "label": "Home", "address": "full address", "lat": null, "lng": null },
  "destination": { "label": "HLMK 120", "address": "660 S College Ave, Tempe, AZ 85281", "lat": 33.4195, "lng": -111.9365 },
  "arrive_by": "2026-10-26T09:00:00-07:00",
  "primary_mode": "TRANSIT",
  "alternative_modes": ["WALK", "BICYCLE"],
  "buffer_min": null,
  "now": null
}
```

| Field | Type | Rules |
| --- | --- | --- |
| `origin`, `destination` | object | Each needs `address`, **or** both `lat` and `lng`. If coordinates are given they are used for routing; otherwise the address is. Giving `destination` coordinates lets weather load in parallel (faster). |
| `….label` | string | Display only. Echoed back in `trip`. Never used for routing. |
| `arrive_by` | ISO 8601 | **Must include a UTC offset.** Not more than 7 days ahead or 1 hour in the past. Every time in the response is shown in this offset. |
| `primary_mode` | enum | `TRANSIT` (default), `WALK`, `BICYCLE`, `DRIVE`. |
| `alternative_modes` | array | Up to 3, unique, must not include `primary_mode`. Default `[]`. |
| `buffer_min` | int 0-60 | Optional. The student's cushion in minutes: how early they want to arrive. Overrides the default for *every* mode (defaults: TRANSIT 3, WALK 3, BICYCLE 5, DRIVE 10). For transit, the last bus is chosen to arrive at least this long before `arrive_by`. |
| `now` | ISO 8601 | Testing only. Overrides the clock. Needs a UTC offset. |

## Response

Null fields are left out. Typical size is 1-2 KB (target under 3 KB). Degraded results are still HTTP 200 so the
body always parses.

| Field | Meaning |
| --- | --- |
| `ok` | `false` only for hard failures; see Errors. |
| `data_quality` | `scheduled` transit uses posted schedules (Google exposes no live-bus flag). `live` DRIVE with traffic-aware routing. `no_transit` no transit route found. `error` hard failure. |
| `fallback_needed` | `true` = **Cubbie should do its own web search**. `fallback_hint` says what to look for. |
| `generated_at` | Request time in the trip's offset. |
| `trip` | `origin_label`, `destination_label`, `arrive_by` as `h:mm AM/PM`, and `arrive_by_iso`. |
| `…_iso` fields | Every displayed time has an exact twin with the date and UTC offset, such as `leave_by_iso: "2026-10-27T08:40:00-07:00"`. Use these to compare re-checks and for classes on other days; use the short `h:mm AM/PM` strings only for wording. |
| `resolved` | Geocoded `origin` and `destination` as `{lat, lng}`. |
| `primary` | `mode`, `leave_by` (+`_iso`), `arrive_at` (+`_iso`), `total_min`, `buffer_min`, `spare_min`, `on_time`, `steps[]`, `backup`, `alerts[]`. Missing when `data_quality` is `no_transit`. |
| `primary.buffer_min` / `spare_min` | `buffer_min` is the cushion the plan *aims for*: the student's `buffer_min` (or the mode default) plus any weather buffer. `spare_min` is the time actually left: `arrive_by` minus `arrive_at`, in minutes (negative when late). Example: `buffer_min: 3`, `spare_min: 6` means they arrive 6 minutes early. |
| `primary.steps[]` | `type` (`walk`, `transit`, `bike`, `drive`), `text`, `minutes`. Transit steps also have `line`, `vehicle`, `stop`, `depart_at` (+`depart_at_iso`), `get_off`, `realtime` (always `false`). Walks under 1 minute are dropped and consecutive walks are merged. |
| `primary.backup` | TRANSIT only, and **only when it still gets the student there on time**. A later trip with the same shape as `primary`: `text`, `leave_by`, `arrive_at` (+ `_iso`), `on_time` (always true), full `steps[]`. Absent when no later trip makes it, so absent means "if you miss this one, you're late". |
| `primary.alerts` | Always empty today: Google's Routes API has no transit service alerts. |
| `alternatives[]` | Other modes: `mode`, `minutes`, `leave_by` (+`_iso`), `on_time`. |
| `weather` | `at_departure` and `at_arrival` (`time`, `temp_f`, `condition`, `precip_pct`, `wind_mph`), `severity` (`none`, `notable`, `severe`), `impact` text, and `alerts[]`: active US National Weather Service warnings, each `{event, headline, severity, starts, ends}` (for example `event: "Dust Storm Warning"`; `starts`/`ends` are ISO times). Up to 2; the field is absent when there are none or outside the US. The whole `weather` block is left out if the forecast failed. |
| `suggestion` | One line comparing modes, only when useful. For example "Biking is 11 min faster than bus". |
| `maps_link` | Google Maps link. In **every** response, including errors. Handy to include in the text. |
| `degraded` | Parts that failed: `weather`, `transit`, `alternatives`. Empty when everything worked. |

## What to do with each response

| You get | Do this |
| --- | --- |
| `ok: true`, `fallback_needed: false` | Write the alert from `primary`. Add `weather.impact` and `suggestion` if present. |
| `primary.backup` present | Mention it as the fallback if they miss the first trip: it is guaranteed on time. |
| No `backup` and a transit primary | This is the last workable trip. Say there is no later bus that gets them there on time. |
| `primary.on_time: false` | Say they will be late on this plan; lead with the alternative that is `on_time`. |
| `data_quality: "no_transit"` | Search the web for the campus shuttle or local transit tracker (`fallback_hint`). Walk, bike or drive times in `alternatives` are still valid. |
| `ADDRESS_NOT_FOUND` | Ask the student to confirm the `error.field` address. A web search will not help. |
| `UPSTREAM_TIMEOUT` / `UPSTREAM_ERROR` | Web search fallback; mention it may be less exact. |
| HTTP 400 / 401 | The call is wrong. Fix it; don't retry. |
| HTTP 429 | Wait `Retry-After` seconds, then try again. |

## Real examples (v1)

The docs page shows a TRANSIT success, a backup with a weather warning (illustrative, mocked heat warning), a
no-transit result and an address-not-found error. The page's example with a backup and a weather warning:

```json
"primary": {
  "mode": "TRANSIT", "leave_by": "8:37 AM", "leave_by_iso": "2026-10-26T08:37:00-07:00",
  "arrive_at": "8:54 AM", "arrive_at_iso": "2026-10-26T08:54:00-07:00",
  "total_min": 17, "buffer_min": 8, "spare_min": 36, "on_time": true,
  "steps": [ ... ],
  "backup": {
    "text": "Orbit Mars at 9:01 AM",
    "leave_by": "8:52 AM", "leave_by_iso": "2026-10-26T08:52:00-07:00",
    "arrive_at": "9:09 AM", "arrive_at_iso": "2026-10-26T09:09:00-07:00",
    "on_time": true,
    "steps": [ { "type": "walk", "text": "...", "minutes": 5 }, { "type": "transit", "...": "..." } ]
  }
},
"weather": {
  "severity": "severe",
  "impact": "Dangerous heat on 6 min of walking, +5 min added",
  "alerts": [ { "event": "Excessive Heat Warning", "severity": "Severe",
                "starts": "2026-10-26T06:00:00-07:00", "ends": "2026-10-26T20:00:00-07:00" } ]
}
```

A finished alert text (what Cubbie sends):

```text
Leave by 8:40 AM for HLMK 120 - Orbit Mars from Terrace Rd & Spence Av (Flag Zone) at 8:46 AM. Arrive ~8:54 AM. Backup: Orbit Mars at 9:01 AM (would be late).
```

## Errors

| Code | HTTP | Meaning |
| --- | --- | --- |
| `BAD_REQUEST` | 400 | Invalid body. `error.field` names the field when known. |
| `UNAUTHORIZED` | 401 | Missing or wrong `x-skill-token`. |
| `RATE_LIMITED` | 429 | More than 10 requests/min per token and IP. See the `Retry-After` header. |
| `ADDRESS_NOT_FOUND` | 200 | Google could not locate an address. `error.field` is `origin` or `destination`. |
| `NO_ROUTE` | 200 | No route exists for a non-transit mode. |
| `UPSTREAM_TIMEOUT`, `UPSTREAM_ERROR` | 200 | The routing service failed. `alternatives` may still be present. |

```json
{ "ok": false, "data_quality": "error", "fallback_needed": true,
  "error": { "code": "…", "message": "…", "field": "…" },
  "maps_link": "https://www.google.com/maps/search/?api=1&query=…", "degraded": ["transit", "weather"] }
```

## How the times are worked out

| Mode | `leave_by` | `arrive_at` |
| --- | --- | --- |
| TRANSIT | first departure − walk to the stop − weather buffer − 1 min slack. The trip is chosen to reach its last stop (plus the final walk) by `arrive_by` − buffer. | last arrival + remaining walk |
| WALK / BICYCLE / DRIVE | `arrive_by` − (duration + mode buffer + weather buffer) | `leave_by` + duration |

- **Buffers:** the student's `buffer_min` if sent, else TRANSIT 3, WALK 3, BICYCLE 5, DRIVE 10 minutes. The
  response's `buffer_min` adds the weather buffer on top. For transit, the buffer decides which trip is picked (it
  should arrive at least that early); `spare_min` reports how early it actually arrives.
- **On time:** `arrive_at` ≤ `arrive_by`. Trips can't start in the past, so late starts show as late. If the best
  bus is already gone, the plan uses the next one.
- **Weather buffer** is the single largest of: ≥ 100°F +3 min, ≥ 110°F +5, rain chance ≥ 50% +5 (+10 driving),
  wind ≥ 30 mph +5, any US weather alert +5. They are not added together.
- **Suggestion** appears when the primary is late but another mode is not, when bad weather meets 10+ outdoor
  minutes, or when another mode saves 10+ minutes.

## Limits and honest caveats

- **Not live bus tracking.** Times are the posted schedule. `realtime` is always `false` and there is no delay or
  service-alert data.
- **Campus shuttles are often missing** from Google's transit data. Expect `no_transit` sometimes; that is what the
  web-search fallback is for.
- **Transit alternatives** do not include waiting time.
- **HTTP status:** everything that can degrade (address not found, no route, upstream timeouts) is **HTTP 200 with
  `ok: false` or `fallback_needed: true`**, so the body always parses. Only 400 (bad request), 401 (bad token) and
  429 (rate limit) are non-200. The server never returns 5xx on purpose; treat any 5xx or non-JSON body as a network
  failure and fall back (the client script does).
- **Weather alerts** come from the US National Weather Service. Outside the US they are skipped silently; forecasts
  still work.
- **Rate limit** is 10 requests/min per token and client IP, counted per server instance.
- **Privacy:** addresses and coordinates are never logged. Only request id, status, timing, cache hit/miss and
  upstream status codes.
- **Nothing is school-specific.** It works anywhere Google routes; just pass different addresses.

## Client script for Cubbie's sandbox

Standard library only (no installs), served at `/client.py`. Our vendored, modified copy is
`../scripts/never_late.py` (its header lists the changes). It prints one JSON object: `action` (`send_alert`,
`web_search_fallback` or `fix_input`), plus `message`, `search_hint`, `maps_link` and the full `data`.
Exit codes: 0, 3, 2.

Routing by Google Routes API, weather by Open-Meteo, alerts by the US National Weather Service.

## Observed behavior (our captures, not from the docs page)

- A short on-campus trip (Memorial Union → Helmick Center, 9 min walk) returns `data_quality: "no_transit"` and
  `fallback_needed: true`, but v2 still lists on-time WALK and BICYCLE journeys
  (`../assets/sample_short_trip.json`): Google gives no transit route when walking is clearly faster.
- Tempe Marketplace → Helmick (v2) returned three on-time Valley Metro journeys, one with a transfer and one with
  an 18-minute walk to the stop. The backend doesn't filter by the student's longest walk; the Skill must.
- v2 adds no ASU campus shuttle data; shuttles still need the web fallback.
- Bug in `never-late-api-00008-8nc`, fixed in `never-late-api-00011-njh`: WALK/BICYCLE/DRIVE `leave_by` ignored
  the current time (`now` 8:58 for a 9:00 class gave walk "leave 8:36, arrive 9:12"). Verified fixed live: now
  "leave 8:58, arrive 9:12". Our client still guards against it (CHANGE 7 in `scripts/never_late.py`).
  The docs page and `/client.py` did not change with the fix.
