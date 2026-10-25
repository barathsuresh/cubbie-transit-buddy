# Destinations: turn a class location into a verified place

Open this file whenever a location needs to become a place to route to: class locations during onboarding, a
class whose remembered destination is missing, or a place the student says they are at ("I'm at Tempe
Marketplace"). Always do this **before** asking for directions: map searches often miss building codes like
"HLMK" or match the wrong place.

The result is a destination with: building code, room, building name, campus, street address, coordinates when
known, where it came from (this Skill's building list, a web page, or the student), the page link if from the
web, and whether the student confirmed it.

## Steps

### 1. Read the location

Split the location into a building code and a room:

- "HLMK 101" → HLMK, room 101
- "BYENG 210", "BYENG210" → BYENG, room 210
- "BYENG M1-09", "COOR L1-20" → BYENG, room M1-09; COOR, room L1-20
- "Tempe - COOR 170" or "COOR 170 (Tempe)" → campus Tempe, COOR, room 170
- A building name instead of a code ("Coor Hall", "the MU", "Hayden Library") → match by name in step 2

If the location says online, remote, Zoom, iCourse, ASU Online, Sync or TBA: there is no place to go. Tell the
student no trip is needed for that class, and don't resolve it.

### 2. Look it up in this Skill's building list

Open `data/asu-buildings.json` in this Skill's folder. Find the entry whose `code` matches (ignore case) and whose
`campus` matches the student's campus. For a name, match it against `name` ("Coor Hall" → "Lattie F. Coor Hall",
"the MU" → "Memorial Union"). Use the entry's name, address, coordinates and `source_url` as they are.

Known alias from ASU's own page: CAVC (College Avenue Commons) is the old name of the Paul C. Helmick Center,
HLMK.

The list covers 56 ASU Tempe buildings taken from ASU's building pages, where the code, address and map location
could be checked. Some common class buildings are deliberately not in it (for example the Engineering Center ECA
to ECG, Bateman Physical Sciences PSB to PSH, Life Sciences LSB to LSE, Stauffer STAUF, Social Sciences SS),
because ASU's pages share one address between several wings or their location couldn't be checked. Use step 3 for those.

### 3. Not in the list: search the web

Search the web for the code, official ASU sources first: "ASU building code <CODE>", the ASU campus map, and ASU's
building pages (tours.asu.edu building pages list a street address and building code). Then reputable pages such
as a department's room page.

From one page you actually read, take the building name, campus and street address. Take coordinates only if that
page or its map link gives them. Never estimate an address or coordinates. If you have no coordinates, leave them
out: the trip planner looks up the address, and directions.md remembers the coordinates it returns.

Remember the page link with the destination.

### 4. Still unsure: ask the student

Ask when there are two candidates, no street address, or the building is on a different campus from the
student's. Give the options and a default:

```text
Is ECG 237 in the Engineering Center G Wing on the Tempe campus? Or tell me the building name.
```

Never guess. If the student doesn't know, ask them to check the location in My ASU or their syllabus.

### 5. Confirm and remember

- During onboarding, the confirmation is part of the timetable check ("Is this right?"). Show the full name with
  the code: "Paul C. Helmick Center (HLMK) 101".
- Outside onboarding, confirm a new web or student resolution in one line before using it.
- Once confirmed, remember the destination with that class, so it is never resolved again. Check the list again
  only if the student says the room changed.

### 6. Places the student is at (not classes)

For "I'm at Tempe Marketplace" or "I'm at my friend's at <address>": if it's an ASU building, use steps 1 to 2;
otherwise search the web for its street address (the place's own site first). Use it as the starting point for
this trip only; don't replace home. Don't remember a friend's or another private address unless the student asks.

## When something fails (one line each)

- Code not in the list and no web result: "I can't find building <CODE>. What's the building name or address?"
- Two possible buildings: ask with both names, as in step 4.
- The student's campus isn't ASU Tempe: skip the list and go straight to step 3.
