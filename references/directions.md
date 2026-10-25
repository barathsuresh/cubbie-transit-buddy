# Directions: get the trip options

Open this file when the student asks when to leave or how to get to a class, and when a scheduled check-in needs
a fresh plan. It gets candidate journeys from the Skill's trip planner (the team's server, which uses Google
Maps), removes the ones that don't fit the student, adds live times when it can, and falls back to the web when
the planner can't help.

The trip planner does **not** pick a plan or a backup. This file hands the remaining journeys to
references/commute-intelligence.md, which picks the plan and the backup and writes the reply. Scheduling is in
references/notifications.md.

Privacy: the start and destination addresses (and coordinates) go to the trip planner and to Google Maps. The
planner doesn't log them. Say so if the student asks.

## 1. Inputs

- **Start:** home from memory, unless the student said where they are now ("I'm at the MU"); then resolve that
  place with references/destinations.md step 6 and use it for this trip only.
- **Destination:** the class's remembered destination. If it isn't resolved yet, open
  references/destinations.md first.
- **Arrive by:** the class start, as date and time with the Phoenix offset -07:00 (Arizona has no daylight saving
  time), for example `2026-10-26T14:00:00-07:00`. Work out the date from the student's local time, not the
  sandbox clock, which may be in another time zone. The planner accepts up to 7 days ahead.
- **Buffer:** 10 minutes, unless the student asked for a different arrival cushion (remembered by
  references/onboarding.md).
- **Ways to travel:** the student's main way first, then the others to compare, at most 4 in total, from TRANSIT,
  WALK, BICYCLE and DRIVE. Default `["TRANSIT", "WALK", "BICYCLE"]`. Add DRIVE only if the student drives.

## 2. Run the trip planner

Run this from the Skill's folder, filling in the request on standard input. `label` is display text only: put the
building name, code and room there, and the real address in `address`. Leave out `lat` and `lng` when you don't
have them; never make them up. Including `modes` is what makes the planner return journeys.

```bash
python3 scripts/never_late.py - <<'JSON'
{"origin": {"label": "Home", "address": "<street address>", "lat": <lat>, "lng": <lng>},
 "destination": {"label": "<Building name> (<CODE>) <room>", "address": "<street address>", "lat": <lat>, "lng": <lng>},
 "arrive_by": "<YYYY-MM-DDTHH:MM:00-07:00>",
 "modes": ["TRANSIT", "WALK", "BICYCLE"],
 "buffer_min": <buffer>}
JSON
```

Offline demo, no network: `python3 scripts/never_late.py --sample` (also `--sample no_transit`,
`--sample error`, `--sample short_trip`).

The script prints one JSON object: `action`, `options` (one short line per journey), `search_hint`, `maps_link`,
`reason` (an error code), `live_check_needed`, and `data` (the planner's full answer).

What's in `data.journeys`: each journey has an `id`, `mode`, for transit a `provider` and `route`, `leave_by`,
`arrive_at`, `total_min`, `on_time` and `steps`. Transit steps name the `route`, `direction`, `boarding_stop`,
`destination_stop`, `depart_at` and `arrive_at`. Transit journeys come first, latest departure first, then the
other ways in the order asked. That order is not a recommendation.

- All times are full ISO times with date and offset. Compare them as they are; in replies write them short, in
  Phoenix time ("8:28 am").
- Each journey's `leave_by` **already includes** the student's buffer and any weather buffer. Don't add another.
- `provider` is whatever Google reports (Orbit lines show as Valley Metro). Use the `route` name in replies.
- Transit times are posted schedules: `realtime` is false and `availability` is UNCERTAIN on every step, and
  `data.verification` says no live tracking and no service alerts were checked. Step 5 is the only live check.

If the planner returned coordinates for a place that had none (`data.resolved.origin` or
`data.resolved.destination`), remember them with that place.

## 3. Act on the result

| Exit | `action` | `reason` | What to do |
| --- | --- | --- | --- |
| 0 | journeys | none | Filter (4), live check (5), then references/commute-intelligence.md with what's left |
| 2 | fix_input | any | A Skill problem, not the student's. Say "My trip planner isn't working right now", use the web fallback (6), don't retry. |
| 3 | web_search_fallback | `ADDRESS_NOT_FOUND` | Re-resolve the place named in `data.error.field` with references/destinations.md (ask the student if unclear), then run once more. |
| 3 | web_search_fallback | `RATE_LIMITED` | Wait a minute, run once more; if it fails again, web fallback (6). |
| 3 | web_search_fallback | anything else, or none | Short trip check (7) first; otherwise web fallback (6) and weather (8). |

## 4. Filter the journeys

Remove journeys that don't fit the student, before anyone chooses:

- A walk step longer than the student's longest walk (default 15 min). The planner doesn't know that limit and
  does return long walks to a stop.
- More than one transit step when the student said no transfers.
- A way to travel the student doesn't use, and a transit route the student excluded (for example no light rail),
  when the route name makes that clear. If it isn't clear, keep it.
- A last walk from the stop to the building longer than 15 minutes.
- A transit journey whose first bus or train leaves before now (it can no longer be boarded).

A walk, bike or drive journey marked `leave_by_adjusted` means its planned leave time had already passed: the
script has moved it to leave now and recomputed its arrival and `on_time`. Say "leave now" for it. Never tell the
student a leave time that has passed.

Then look at what's left:

- No on-time transit journey: transit doesn't get them there on time. Check the other ways (7); if none is on
  time either, say they will be late on every option and give the earliest arrival.
- Only one on-time transit journey: there is no on-time backup by bus. Say so rather than offering a late one.
- Nothing left at all: use the web fallback (6).

## 5. Live check

When `live_check_needed` is true and an on-time transit journey's first transit step leaves within the next 45
minutes (check at most the first two such journeys):

1. Take that step's `route`, `direction`, `boarding_stop` and `depart_at`.
2. Read a live arrivals page for that stop and route. The agency's own page first (see
   references/transit-sources.md); TransSee pages have worked for Tempe Orbit before.
3. If the page shows the bus running late or early, move that journey's leave and arrival times by the same
   amount, mark it as live, and note the page's link. If it now arrives after the class starts, mark it late.
4. If no live page is available, keep the journey and note that its times are scheduled, not live.

Never invent a delay. Pass the adjusted journeys, with which ones are live, to references/commute-intelligence.md.

## 6. Web fallback

Use `search_hint` (or `data.fallback_hint`) to search the web for the route, or the nearest stop and a live
arrivals page. For ASU shuttles and Orbit, see references/transit-sources.md for the official pages. Work out the
leave time as: walk to the stop + time until departure + ride + walk to the building + the student's buffer.
Tell the student the times came from that page, with its link on its own line. Add `maps_link` on its own line
when present. If nothing gives departure times, say so in one line and send `maps_link`.

## 7. Short trips and other ways

A `no_transit` answer is normal for short campus trips: the planner gives no bus when walking is clearly faster,
but still returns walk and bike journeys in `data.journeys`. If a WALK journey is on time and no longer than the
student's longest walk, tell them to walk, with its leave time; no web search is needed. Mention a BICYCLE journey
if the student bikes.

When transit doesn't make it, mention an on-time walk or bike journey in one line with its leave time. Don't
suggest driving unless the student said they drive.

## 8. Weather when the planner has none

`data.weather` is taken at the first journey's times. If `data.degraded` lists weather, or there is no `data`,
read the current National Weather Service alerts for the start location on weather.gov, so dust storm, severe
thunderstorm and extreme heat warnings still reach the student. Skip the forecast rather than guess it.

## When something fails (one line each)

- Planner not working (exit 2): "My trip planner isn't working right now. Here's what I found on the web:"
- No route anywhere: "I couldn't find a bus or train for that trip. Here's the map:" with `maps_link` on its own
  line.
- Class more than 7 days away: "I can plan that from <date>; ask me closer to the day."
