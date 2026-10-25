# Cubbie Transit Buddy

A [Cubbie](https://cubbie.ai) Skill that tells ASU Tempe students when to leave for class and which bus, Tempe
Orbit, light rail or campus shuttle to take, with a backup route, live delays, weather warnings and reminders.

## Install

Text this repository's link to Cubbie:

```text
https://github.com/barathsuresh/cubbie-transit-buddy
```

Cubbie asks before fetching it; reply "yes". Then, in a new message: "set up transit buddy".

## How it works

1. **Onboarding** (`references/onboarding.md`): campus, home address, class schedule (Google Calendar, Canvas,
   a My ASU screenshot, or typed), travel and reminder preferences. One question at a time.
2. **Destinations** (`references/destinations.md`): turns "HLMK 101" into "Paul C. Helmick Center (HLMK) 101"
   with a verified address, using `data/asu-buildings.json` (56 ASU Tempe buildings from ASU's own pages), then
   the web, then the student.
3. **Directions** (`references/directions.md`): asks the team's trip planner (Never Late API on Google Cloud
   Run, using Google Maps) for candidate journeys through `scripts/never_late.py`, filters them by the
   student's preferences, checks live times, and falls back to the web.
4. **Transit sources** (`references/transit-sources.md`): verifies each transit leg against Valley Metro, Tempe
   Orbit, ASU shuttle and FLASH sources.
5. **Commute intelligence** (`references/commute-intelligence.md`): picks the primary journey and a backup that
   still works after a missed bus, and words the reply.
6. **Notifications** (`references/notifications.md`): get-ready and departure reminders through Cubbie.

## Privacy

The start address and class building go to the team's trip planner and to Google Maps to plan trips. The planner
doesn't log addresses or coordinates. Everything else stays in Cubbie's memory for the student.

## Repository layout

```text
SKILL.md                 entry point Cubbie reads
references/              the six workflow files above
scripts/never_late.py    trip planner client (Python 3 standard library only)
data/asu-buildings.json  verified ASU Tempe buildings
assets/                  sample requests and responses for offline runs
docs/backend-api.md      the trip planner's API, for the team
tests/                   automated tests and the team test plan (not needed by Cubbie)
```

## Testing

From the repository folder:

```bash
python3 scripts/never_late.py --sample              # offline demo (also: no_transit, error, short_trip)
python3 -m unittest discover -s tests -v            # automated tests, offline
LIVE=1 NEVER_LATE_TOKEN=... python3 -m unittest discover -s tests -v   # plus live trip planner calls
```

The on-Cubbie test plan is `tests/test-cases.md`.

Built for the Cubbie Hackathon.
