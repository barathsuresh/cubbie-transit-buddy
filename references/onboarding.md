# Onboarding: set up the student's commute profile

Open this file the first time the student uses the Skill, when they say "set up transit buddy", or when they
change something ("I moved", "new schedule", "change my buffer", "no shuttles").

Goal: collect the student's profile and class timetable, one question at a time, and remember them so nothing is
asked twice. Each question suggests a default the student can accept with "yes".

## Before you ask anything

Check what you already remember about the student for this Skill. Ask only for what is missing. If setup was
interrupted before, say "Picking up where we left off" and continue from the first missing item.

## Steps

### 1. Intro and privacy (one short message)

Say what the Skill does and where the data goes, in two or three lines. For example:

```text
I can tell you when to leave for class and which bus, Orbit or light rail to take, with a backup.
To plan trips I send your start address and class building to my trip planner (the Skill team's server) and to Google Maps. It doesn't keep them.
```

Never ask for passwords or keys in chat.

### 2. University and campus

Ask: "Are you at ASU Tempe?" Default yes.

- Yes: university Arizona State University, campus Tempe.
- Another ASU campus or another school: accept it. Say building codes may need their help, because the
  building list in this Skill covers ASU Tempe; destinations.md falls back to web search. Don't refuse.

### 3. Home address

Ask: "What's your home address? I'll plan trips from there."

- A street address: keep it as given.
- A place name ("Yugo Tempe Villas"): search the web for its street address, preferring the place's own site.
  Confirm in one line ("Yugo Tempe Villas, <street address>?") before remembering it.
- Coordinates: remember them only if a page you read gives them. Otherwise leave them out; the trip planner looks
  up the address, and directions.md remembers the coordinates it returns.
- Not found, or several matches: ask for the street address.

Also remember a short label for it ("Home" or the place name).

### 4. Class schedule

Try these sources in order. Stop as soon as you have every class with its days, start and end times, and room.

1. **Google Calendar.** If Google is connected, read the student's Google Calendar events for this week and next.
   Keep recurring events that look like classes: a course code (FSE 570, CSE 110), or a building and room in the
   location. If Google isn't connected, ask once: "Want to connect Google Calendar so I can find your classes?" If
   they say no, move on.
2. **Canvas.** If Canvas is connected, read the student's current Canvas courses. Look in each syllabus and the
   course pages for meeting days, times and the room. If Canvas isn't connected, move on without asking.
3. **Screenshot.** Ask: "Can you send a screenshot of your class schedule from My ASU?" Read the course, days,
   times and location from the image.
4. **Typed.** Last resort: "Type your classes like this: FSE 570 Mon/Wed 2:00-3:15 HLMK 101".

Many students have no class times in Calendar or Canvas, so steps 3 and 4 are the normal path, not extras.
Note which source each class came from. Skip online, remote or "TBA" classes for trips, but keep them in the list
so the student sees you didn't lose them.

### 5. Resolve every location

Before showing the timetable, open references/destinations.md and resolve each class location to a building name,
address and campus. Ask the student only about locations destinations.md can't settle.

### 6. Confirm the timetable

Send it as a short plain list with full building names, then ask "Is this right?":

```text
Here's your week:
- FSE 570, Mon/Wed 2:00 pm, Paul C. Helmick Center (HLMK) 101
- CSE 110, Tue/Thu 10:30 am, Brickyard Engineering Building (BYENG) 210
Is this right?
```

Remember the timetable only after they say yes. If they correct something, fix just that line and ask again.

### 7. Semester end

Search the web for the current ASU academic calendar and suggest the last day of classes: "Classes end <date>.
Stop reminders then?" If you can't find it, ask for the date. Remember it so reminders stop after it.

### 8. Arrival buffer

Don't ask. Use 10 minutes: the student arrives 10 minutes before class (references/commute-intelligence.md uses
the same rule). If the student asks for a different cushion ("I want to be 5 min early"), remember that instead,
from 0 to 60 minutes. The buffer is sent to the trip planner, which already builds it into the leave time, so
nothing else adds it again.

### 9. Travel preferences (one question)

Ask: "I'll plan with buses, light rail, campus shuttles and walking, up to 15 min of walking, transfers OK. Good?"

- Main way to travel: transit by default. If they say they bike, walk or drive, make that the main way.
- Other ways to compare: walking and biking by default. Include driving only if they say they drive.
- Which transit to use (bus, light rail, shuttle), longest walk they accept, and whether transfers are OK.

### 10. Reminders

Ask: "Want reminders? I can text you 20 min before you need to leave to get ready, and again when it's time to
go." Collect only the preferences here, one question at a time:

- Which reminders: departure only, get-ready and departure (default), an evening preview the night before, a
  daily commute check-in, or none.
- How long before the leave time to send the get-ready reminder (default 20 minutes).

Then follow references/notifications.md to schedule them, only after the student says yes.

### 11. Done

One line summary and the trigger phrase:

```text
All set: 4 classes, from Home, 10 min early, bus/rail/shuttle, reminders 20 min before. Text me "when do I leave?" any time.
```

## What to remember

Remember these for the student, in plain words, so later conversations can use them:

- University and campus.
- Home: label, street address, and coordinates when known.
- Each class: course, days, start and end time, location as written, the resolved destination from
  destinations.md, where the class came from (Google Calendar, Canvas, screenshot or typed), and that the student
  confirmed it.
- Arrival buffer in minutes.
- Travel preferences: main way to travel, other ways to compare, allowed transit types, longest walk, transfers OK.
- Reminder preferences: which reminders, and minutes before the leave time for the get-ready reminder.
- Semester end date.

## Changes later

Update only the item the student mentions, confirm it in one line, and remember it:

- "I moved": redo step 3.
- "New schedule" or "I dropped a class": redo steps 4 to 6 for the changed classes only.
- "Change my buffer to 5": update the buffer.
- "No shuttles", "I bike now": update travel preferences.
- "Stop reminders", "remind me earlier": update reminder preferences.

After any change, follow references/notifications.md to refresh scheduled reminders.

## When something fails (one line each)

- Address not found: "I couldn't find that address. What's the street address?"
- Screenshot unreadable: "I can't read that one. Can you send a clearer screenshot, or type your classes?"
- Location can't be resolved: ask the question destinations.md suggests, with the candidates.
- Student stops mid-setup: remember what's confirmed so far; next time continue from the first missing item.
- Google or Canvas not connected: offer Google once, skip Canvas, and go on to the screenshot.
