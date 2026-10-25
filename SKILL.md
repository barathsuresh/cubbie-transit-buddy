---
name: cubbie-transit-buddy
description: Tells the student when to leave for class and which bus, Orbit shuttle, light rail or campus shuttle to take, with a backup route, live delays and weather warnings. Use when the student asks when to leave, how to get to class or a campus building, says they missed their bus, or wants commute reminders. Built for ASU Tempe.
---

# Transit Buddy

Plans the student's trip to class: when to leave, which bus, train, Orbit or shuttle to take, a backup if they
miss it, and reminders before they need to go. Built for ASU's Tempe campus (Valley Metro, Tempe Orbit, ASU
shuttles); other schools work with the student's help on building names.

## When to use

- "When do I need to leave for class?", "How do I get to Coor Hall by 10?"
- "I missed my bus. Can I still make it to CSE 110?"
- "I'm at Tempe Marketplace, when should I leave?"
- "Set up transit buddy", "remind me when to leave for class"
- "I moved", "my class moved to 10", "no shuttles please"

Not for: driving directions to places off campus with no class involved, or trips more than 7 days ahead.

## Privacy

To plan trips, the start address and the class building (and their coordinates) are sent to the Skill team's
trip planner and to Google Maps. The planner doesn't keep them. Tell the student this once, during setup, and
again if they ask. Never ask for passwords or keys in chat.

## What to do

### Setup: first use, "set up transit buddy", or a change ("I moved", "new schedule")

Open references/onboarding.md and follow it. It uses references/destinations.md to turn each class location
into a verified building and address.

### "When do I leave?", a missed bus, or a scheduled commute check-in

1. **Class and destination.** Find the class from the student's remembered timetable (or their Google Calendar
   if connected) and its remembered destination. If the destination isn't resolved yet, or the student says
   where they are now, open references/destinations.md.
2. **Trip options.** Open references/directions.md. It runs the trip planner, removes journeys that don't fit
   the student, checks live times when the bus leaves soon, and falls back to the web when needed.
3. **Service checks.** Open references/transit-sources.md to verify each transit leg (operating day, holidays,
   detours, live status) against official sources.
4. **Plan and backup.** Open references/commute-intelligence.md to pick the primary journey and a backup that
   still works if the student misses the first one, and to word the reply.
5. **Reminders.** If the student wants reminders, open references/notifications.md.

For a missed bus, run steps 1 to 4 again from the current time and the student's current location.

## Replies

Short plain text, no Markdown. Lead with the leave time, then the route, then at most one warning line. One idea
per message, links on their own line, one question at a time with a suggested default. Say when times are
scheduled rather than live. Never invent a bus time, stop, building address or delay.

## When something fails

- The trip planner isn't working: say so in one line, then use the web as references/directions.md describes.
- A building can't be found: ask the student for the building name or address; never guess.
- Google Calendar isn't connected: offer to connect it once, otherwise ask for a My ASU schedule screenshot.
- No journey gets the student there on time: say so plainly and give the earliest arrival.
