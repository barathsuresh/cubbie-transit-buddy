# Cubbie Transit Buddy — Test Cases

Team test plan. Not read by Cubbie. Each case says which reference file owns the behavior and which parts are
automated in `tests/`. Everything else is run by hand on Cubbie and recorded in the execution record (section 5).

Run the automated parts from the Skill folder:

```bash
python3 -m unittest discover -s tests -v                              # offline
LIVE=1 NEVER_LATE_TOKEN=<token> python3 -m unittest discover -s tests -v   # plus live backend calls
```

The live run makes about 6 backend requests (limit: 10 per minute per token and IP).

## 1. Test Overview

This document defines test scenarios for Cubbie Transit Buddy using a fictional Arizona State University
student's weekly calendar.

The goal is to verify that Cubbie can:

1. Retrieve upcoming events from Google Calendar.
2. Resolve ASU building names and abbreviations.
3. Retrieve transportation alternatives.
4. Verify transportation availability.
5. Select primary and backup journeys.
6. Schedule appropriate departure reminders.
7. Replan when circumstances change.

## 2. Test Student Profile

- University: Arizona State University
- Campus: Tempe
- Starting location: Yugo Tempe Villas, Tempe, Arizona (1111 E Apache Blvd, Tempe, AZ 85281, from ASU's
  off-campus housing listing)
- Preferred arrival buffer: 10 minutes
- Transportation preference: Public transit, campus transportation, or walking
- Preparation reminder: 20 minutes before recommended leave-home time
- Departure reminder: At recommended leave-home time
- Time zone: America/Phoenix

All student details are fictional test fixtures. Yugo Tempe Villas is a public apartment complex used only as a
test starting point; it is not saved in the Skill's sample files.

## 3. Sample Calendar

The test schedule is based on a sample calendar screenshot dated August 19–23, 2024. For live testing, create
equivalent events on future dates (the automated live tests use the next Monday and Tuesday).

### Monday, Wednesday, Friday

| Time | Event | Location |
|---|---|---|
| 9:00–9:50 AM | CSE 110 | ISTB4 101 |
| 11:00–11:50 AM | MAT 210 | PSF 201 |
| 1:00–2:00 PM | Study Time | Hayden Library |
| 3:00–4:00 PM | Club Meeting | Memorial Union |

### Tuesday, Thursday

| Time | Event | Location |
|---|---|---|
| 10:00–10:50 AM | ENG 102 | Lattie F. Coor 4403 |
| 12:00–1:00 PM | Lunch or Meeting | Memorial Union / ISTB4 |
| 2:00–3:15 PM | CSE 110 Lab | ISTB4 130 |

How these resolve with `data/asu-buildings.json`:

| Location | Resolves to | How |
|---|---|---|
| ISTB4 101 / 130 | Interdisciplinary Science and Technology IV, 781 E. Terrace Mall | building list |
| Lattie F. Coor 4403 | Lattie F. Coor Hall (COOR), 976 S. Forest Mall | building list, by name |
| Hayden Library | Hayden Library (LIB), 300 E. Orange Mall | building list, by name |
| Memorial Union | Memorial Union (MU), 1290 S. Normal Ave. | building list, by name |
| PSF 201 | Bateman Physical Sciences Center, F wing | **not in the list**: web search, then the student confirms (see TC02) |
| Memorial Union / ISTB4 | two places | ask the student which one |

Other calendar events may be included as additional test scenarios.

## 4. Test Cases

### TC01 — First Class Commute

Owner: directions.md, then commute-intelligence.md. Automated: `test_scenarios.LiveScenarios.test_tc01_*`
(destination resolves to ISTB4, transit journeys include walking, sources are `google_routes`, at least one
on-time transit journey arrives by 8:50, times are self-consistent).

**Scenario:** Student needs to reach their first class of the day.

Input:
- Origin: Yugo Tempe Villas
- Destination: ISTB4 101
- Class start: 9:00 AM
- Arrival buffer: 10 minutes

Expected behavior:

1. Cubbie identifies the upcoming CSE 110 class.
2. Resolves ISTB4 to a verified campus destination.
3. Retrieves available journeys.
4. Verifies relevant transportation schedules.
5. Selects a primary journey arriving by 8:50 AM when possible.
6. Identifies a feasible backup.
7. Calculates the leave-home time.

Pass criteria:
- Destination is correct.
- Journey times come from an identifiable source.
- Walking time is included.
- The recommended departure time is feasible.
- No route or arrival time is invented.

### TC02 — Campus Building Resolution

Owner: destinations.md. Automated: `test_scenarios.BuildingData` (sample-calendar buildings resolve, PSF is
deliberately absent, every entry has an ASU source and an address).

**Scenario:** Calendar contains an abbreviated building location.

Input:
- Event: MAT 210
- Location: PSF 201

Expected behavior:

1. Extract the building code PSF.
2. Look up the building in the verified campus directory.
3. Preserve room number 201.
4. Use the verified building location for routing.

Transit Buddy specifics: PSF is not in `data/asu-buildings.json`, because ASU's pages list only the Bateman B wing
street address and give PSF only as a shipping address. Expected on Cubbie: it finds "Bateman Physical Sciences
Center, F wing" on the web and asks the student to confirm before routing, keeping room 201. It must not invent a
street address or coordinates for PSF.

Pass criteria:
- Correct building is identified.
- Room number is preserved.
- Ambiguous locations trigger clarification.

### TC03 — Multiple Transportation Options

Owner: directions.md (journeys) and transit-sources.md (Orbit, Valley Metro, ASU shuttles). Automated:
`test_scenarios.LiveScenarios.test_tc03_*` (every transit step names its provider and route, transfers don't leave
before the previous leg arrives, `live_check_needed` is set). Manual: the provider checks and shuttle coverage.

**Scenario:** More than one transportation option is available.

Input:
- Origin: Yugo Tempe Villas
- Destination: ISTB4
- Class start: 9:00 AM

Expected behavior:

1. Retrieve available public transit journeys.
2. Check relevant Orbit and Valley Metro information.
3. Consider university transportation if it serves the journey.
4. Compare feasible journeys.

Note: the backend reports Orbit lines and the Streetcar under the provider "Valley Metro", and has no ASU
shuttle data; shuttles come from transit-sources.md and the web.

Pass criteria:
- Different transportation providers are not confused.
- Unavailable services are excluded.
- Journey comparisons use consistent timing information.

### TC04 — Primary and Backup Selection

Owner: commute-intelligence.md. Automated: `test_scenarios.TC04PrimaryAndBackup` passes the fixed journeys
(`tests/fixtures/tc04_journeys.json`) through the client and checks the facts the choice depends on. Manual:
feed the same situation to Cubbie and check its wording.

**Scenario:** Multiple candidate journeys are available.

Use fixed, fictional journey data:

| Journey | Leave Home | Arrive | Transfers |
|---|---|---|---|
| A | 8:00 AM | 8:40 AM | 1 |
| B | 8:10 AM | 8:45 AM | 0 |
| C | 8:20 AM | 9:05 AM | 0 |

Class starts at 9:00 AM. Preferred arrival is 8:50 AM. Assume all three journeys are available, accessible, and
have comparable service reliability.

Expected behavior:

- Journey B is a reasonable primary recommendation because it meets the preferred arrival deadline, requires
  no transfers, and allows a later departure.
- Journey A is not a usable backup after missing Journey B because it departs earlier.
- Journey C arrives late.
- Cubbie must not invent a feasible post-miss backup.

Pass criteria:
- The selected primary is justified.
- Backup feasibility is evaluated independently.
- Expired alternatives are rejected.

### TC05 — Missed Bus Recovery

Owner: directions.md (re-plan from now, filter expired journeys), commute-intelligence.md (recommendation).
Automated: `test_scenarios.LiveScenarios.test_tc05_*` re-plans one minute after the planned bus leaves and checks
no expired bus is offered.

**Scenario:** Student misses the recommended bus.

Student message: "I missed my bus. Can I still make it to CSE 110?"

Expected behavior:

1. Obtain the current time.
2. Confirm the student's current location if needed.
3. Retrieve updated transportation alternatives.
4. Exclude journeys that can no longer be boarded.
5. Recommend a feasible alternative.
6. Warn the student if no alternative arrives before class.

Fixed backend issue: walk/bike/drive journeys used to come back with a `leave_by` already in the past (see
section 7). Check Cubbie never quotes a past leave time.

Pass criteria:
- Expired routes are excluded.
- The new recommendation uses the current time.
- Arrival feasibility is recalculated.

### TC06 — Weekend Shuttle Availability

Owner: transit-sources.md. Manual only.

**Scenario:** Student needs to travel between ASU campuses on Saturday.

Expected behavior:

1. Identify the relevant shuttle route.
2. Search the official ASU transportation schedule.
3. Check whether that specific route operates on Saturday.
4. Exclude it if the official schedule confirms no service.
5. Consider other available transportation options.

Pass criteria:
- Weekend service is verified for the specific route.
- Cubbie does not assume every ASU shuttle operates on weekends.

### TC07 — Service Disruption

Owner: transit-sources.md, commute-intelligence.md. Manual only (the backend checks no service alerts:
`service_alerts_checked` is false).

**Scenario:** A relevant route has a service alert.

Expected behavior:

1. Identify the affected route.
2. Verify the alert using an appropriate source.
3. Determine whether it affects the student's boarding stop and travel time.
4. Reconsider the primary journey.
5. Recommend an unaffected alternative when available.

Pass criteria:
- Irrelevant alerts are not applied.
- A canceled route is not recommended.
- Unverified disruptions are not presented as confirmed.

### TC08 — Preparation and Departure Reminders

Owner: notifications.md (preferences collected by onboarding.md). Manual only.

**Scenario:** Student opts into commute reminders.

Use a fictional calculated leave-home time of 8:05 AM. Preparation lead time: 20 minutes.

Expected behavior:

- Preparation reminder at 7:45 AM.
- Departure reminder at 8:05 AM.

Pass criteria:
- Reminders are scheduled for the correct date and time zone.
- Cubbie confirms scheduling only after success.
- No duplicate reminders are created.

### TC09 — Calendar Change

Owner: notifications.md (re-check), onboarding.md (timetable update). Manual only.

**Scenario:** The student's 9:00 AM class moves to 10:00 AM.

Expected behavior:

1. A subsequent scheduled check retrieves the updated event.
2. Cubbie recognizes the changed start time.
3. The commute plan is recalculated.
4. Existing reminders are updated or canceled where supported.
5. New reminders reflect the revised departure time.

Pass criteria:
- Outdated reminders are not intentionally retained.
- The student is informed of meaningful changes.
- Unsupported automatic update capabilities are not claimed.

### TC10 — No Feasible Route

Owner: directions.md (step 4: no on-time journey), commute-intelligence.md (wording). Automated:
`test_scenarios.LiveScenarios.test_tc10_*` plans from home at 8:58 for a 9:00 class and checks nothing claims to
be on time and the earliest arrival is reportable.

**Scenario:** All available journeys arrive after class starts.

Expected behavior:

1. Cubbie identifies that no journey meets the deadline.
2. Reports the earliest realistic arrival.
3. Clearly warns the student that they may be late.
4. Avoids claiming an on-time arrival.

Pass criteria:
- No fabricated alternatives.
- No misleading departure reminder.
- Clear explanation of the limitation.

### TC11 — Between-Class Movement

Owner: directions.md (origin = previous class), commute-intelligence.md. Automated:
`test_scenarios.LiveScenarios.test_tc11_*` uses the Tue/Thu pair (ENG 102 at COOR ends 10:50, next at ISTB4
12:00): origin resolves to COOR, a walk journey exists and is on time. Manual: the Mon/Wed/Fri pair below, once
PSF is confirmed (TC02).

**Scenario:** Student finishes CSE 110 at ISTB4 at 9:50 AM and has MAT 210 at PSF at 11:00 AM.

Expected behavior:

1. Identify the previous class's end time and location.
2. Identify the next class's start time and location.
3. Calculate the available travel window.
4. Consider walking and transit where appropriate.
5. Recommend a practical departure time.

Pass criteria:
- The origin is the previous class location, not the student's home.
- The full journey fits the available time when possible.
- Walking is considered when appropriate.

### TC12 — Unknown Destination

Owner: destinations.md (steps 3–4). Automated: `test_scenarios.BuildingData.test_unknown_code_is_absent`.
Manual: put an event at "XYZQ 101" on the calendar and check Cubbie asks instead of routing.

**Scenario:** Calendar location contains an unrecognized building abbreviation.

Expected behavior:

1. Attempt destination resolution.
2. Avoid guessing coordinates.
3. Ask the student to clarify the location.
4. Continue planning after clarification.

Pass criteria:
- No fabricated building.
- No navigation to an unverified destination.

## 5. Test Execution Record

For every test, record:

| Field | Value |
|---|---|
| Test ID | |
| Test date | |
| Skill commit | |
| Input message | |
| Actual Cubbie response | |
| Expected behavior | |
| Pass / Fail / Blocked | |
| Notes or observed limitations | |

A test is **Blocked** when a required integration or Cubbie capability is not yet available (for example, a
teammate's reference file isn't written yet).

## 6. End-to-End Acceptance Test

The main hackathon demonstration should show this complete workflow:

1. Student installs Transit Buddy.
2. Student provides or confirms their starting location.
3. Cubbie reads the student's upcoming calendar event.
4. Cubbie resolves the ASU building.
5. Cubbie retrieves transportation options.
6. Cubbie checks relevant service availability.
7. Cubbie recommends a primary journey.
8. Cubbie identifies a feasible backup or explains why none exists.
9. Student enables commute reminders.
10. Cubbie successfully delivers a scheduled reminder.

The test passes when the complete flow works without invented transportation information or unsupported
capability claims.

## 7. Findings from the automated runs

- **Backend: past `leave_by` for walk/bike/drive** (found 2026-10-24 in `never-late-api-00008-8nc`; **fixed** in
  `never-late-api-00011-njh`, verified live: now 8:58 → walk "leave 8:58, arrive 9:12"). With
  `now` = 8:58 for a 9:00 class, the walk journey came back as "leave 8:36, arrive 9:12". The arrival uses the
  current time; the leave time doesn't. Transit journeys are correct. Fixed on our side in
  `scripts/never_late.py` (CHANGE 7): such a journey becomes "leave now" with `leave_by_adjusted: true`, covered
  by `test_never_late.MockServer.test_past_leave_by_moved_to_leave_now`; now a no-op, kept as a guard.
  `test_backend_walk_leave_by_respects_now` fails if the backend regresses.
- Yugo Tempe Villas → ISTB4 around 9:00 returns Valley Metro Streetcar journeys; the provider is "Valley Metro".
