# Commute Intelligence — Primary and Backup Route Selection

## Purpose

This document defines how Cubbie Transit Buddy evaluates transportation options and recommends a primary and backup journey.

The objective is to help students arrive at classes and campus events on time while accounting for service availability, walking time, transfers, arrival preferences, and transportation disruptions.

Do not simply recommend the fastest journey. Recommend the most suitable journey that meets the student's arrival deadline.

## 1. When to Use This Workflow

Use commute intelligence when:

- A student asks how to get to an upcoming class or event.
- Cubbie prepares a commute plan from the student's calendar.
- Multiple transportation options are available.
- A student asks for a backup journey.
- A student reports missing a bus or shuttle.
- A new commute check reveals a relevant service change.

For routine commute planning, use the student's saved preferences when available.

## 2. Required Inputs

Obtain the following information before evaluating journeys.

### Event Information

- Event title
- Event start time
- Event date
- Event location
- Campus
- Local time zone

### Student Information

- Starting location
- Preferred arrival buffer
- Transportation preferences
- Accessibility requirements, if provided
- Current location, when different from the saved starting location

### Journey Information

Receive the Never Late API's journeys[] response through directions.md, together with the verification results from transit-sources.md.

Match verification results to journeys using each journey's `id`.

Evaluate every candidate journey independently. Do not assume the first entry in journeys[] is the recommended primary route.

Each journey should contain, where available:

- Journey identifier
- Transportation provider
- Route name or number
- Origin and destination
- Departure time
- Arrival time
- Walking duration
- Walking time to the first boarding stop
- Boarding and alighting stops
- Number of transfers
- Transfer connection times
- Service availability
- Applicable service alerts
- Source of arrival information

Use `transit-sources.md` to verify operating schedules and service disruptions.

If essential information is missing, request clarification or mark the journey as uncertain.

## 3. Calculate the Arrival Deadline

Determine when the student should arrive.

Formula:

Latest preferred arrival = Event start time - Preferred arrival buffer

Example:

Class starts: 9:00 AM

Preferred arrival buffer: 10 minutes

Latest preferred arrival: 8:50 AM

Use a fixed 10-minute arrival buffer for calendar events. The preferred arrival deadline is the event start time minus 10 minutes. Do not prompt the student to configure this buffer. If the student explicitly requests a different arrival deadline, honor that request.

Distinguish between:

- Preferred arrival deadline: the student's desired arrival time.
- Hard deadline: the actual class or event start time.

A journey arriving after the preferred deadline but before the hard deadline may still be useful, but it must be labeled as having a reduced arrival buffer.

## 4. Validate Candidate Journeys

Before ranking journeys, verify that each option is usable.

### A. Service Availability

Use `transit-sources.md` to classify each journey.

Possible statuses:

- AVAILABLE
- UNAVAILABLE
- UNCERTAIN

Exclude journeys confirmed as unavailable.

Do not silently treat uncertain journeys as confirmed available.

### B. Departure Feasibility

Verify that the student has enough time to reach the boarding stop.

Account for:

- Current time
- Walking time to the stop
- Student's starting location
- Boarding time
- Reasonable walking or boarding buffer

Do not recommend a journey whose boarding time has already passed or cannot realistically be reached.

### C. Arrival Feasibility

Compare each journey's arrival time against the preferred arrival deadline and event start time.

Classify journeys as:

**ON_TIME**

Arrives by the preferred arrival deadline.

**REDUCED_BUFFER**

Arrives after the preferred deadline but before the event starts.

**LATE**

Arrives at or after the event start time.

Do not describe a reduced-buffer journey as meeting the student's preferred arrival time.

### D. Accessibility

Exclude journeys that conflict with the student's stated accessibility requirements.

If accessibility information is missing or cannot be verified, communicate the uncertainty instead of assuming the journey is accessible.

## 5. Evaluate Transfer Risk

For journeys involving transfers, consider:

- Number of transfers
- Walking distance between transfer stops
- Time available for each connection
- Scheduled versus live arrival predictions
- Relevant service disruptions
- Availability of later connections

A journey with a short transfer window may be less reliable than a slightly longer journey with fewer transfers.

Do not invent a probability of missing a connection.

Use qualitative risk classifications:

- LOW
- MODERATE
- HIGH
- UNKNOWN

Mark transfer risk as UNKNOWN when there is insufficient information.

## 6. Select the Primary Journey

Prioritize journeys in the following order:

1. Meets the student's accessibility requirements.
2. Is confirmed to operate at the required time.
3. Can realistically be boarded from the student's starting location.
4. Arrives by the preferred arrival deadline.
5. Has manageable transfer risk.
6. Respects the student's transportation preferences.
7. Offers a reasonable total journey duration.

If multiple journeys satisfy these conditions, prefer the one with fewer risky transfers and a comfortable arrival buffer.

Do not automatically choose the earliest departure or shortest travel duration.

If no journey meets the preferred deadline, consider reduced-buffer journeys.

If no journey arrives before the event starts, tell the student that the available options are late.

## 7. Select the Backup Journey

The backup must be independently evaluated.

Do not automatically select the next departure on the primary route.

Consider alternatives across:

- Valley Metro buses
- Valley Metro light rail
- Tempe Orbit
- ASU-operated shuttles
- FLASH
- Walking, when practical
- Multimodal journeys

A backup can use the same transportation provider or a different provider.

### Backup Feasibility

A useful backup should:

1. Be operational on the travel date.
2. Be reachable from the student's likely location.
3. Have a departure that can still be caught.
4. Meet accessibility requirements.
5. Preferably arrive before the student's preferred deadline.
6. Otherwise, arrive before the event starts.

### Missed-Primary Scenario

When selecting a backup, consider whether it would remain usable if the student misses the primary vehicle.

For example:

Primary bus departs at 8:05 AM.

Backup bus departs at 8:12 AM.

The backup may be feasible if the student can reach its boarding stop in time.

However, a backup departing at 8:00 AM would not be useful after missing the 8:05 AM primary bus.

Do not select a journey as the missed-primary backup if its required departure or boarding time occurs before the primary journey's boarding time.

A backup must remain feasible from the student's likely location at the time the primary is missed.

If none of the returned journeys is a feasible backup, request fresh journey candidates when needed rather than selecting an earlier departure.

### Backup Independence

When possible, prefer an alternative that does not depend on the same potentially disrupted transit segment as the primary journey.

For example, if the primary route is affected by a light rail suspension, a backup that uses the same suspended light rail segment is not independent.

If no feasible backup exists, say so clearly.

## 8. Replanning After a Missed Ride

If the student says:

- "I missed my bus."
- "My shuttle didn't come."
- "I'm still at home."
- "Can I still make it?"
- "Find another way."

Recalculate the commute using:

1. The current local time.
2. The student's current or confirmed location.
3. The original event start time.
4. Current transportation availability.
5. Updated journey alternatives.

Do not reuse an expired backup recommendation.

If the student has moved to another stop or location, use that location as the new origin.

If no available journey can arrive before class, explain the earliest realistic arrival instead of promising an on-time arrival.

## 9. Handling Service Disruptions

When a relevant disruption is discovered:

1. Identify the affected journey.
2. Determine whether the disruption invalidates the primary recommendation.
3. Check whether the backup remains feasible.
4. Retrieve additional alternatives if necessary.
5. Recalculate the recommended departure time.
6. Communicate any meaningful change to the student.

Only perform proactive rechecks when Cubbie's supported scheduling capabilities have been configured to do so.

Do not claim that a route is continuously monitored unless continuous monitoring is actually available.

## 10. Recommended Departure Time

Distinguish between:

- Vehicle departure time
- Time to leave the student's starting location

The recommended leave time must account for walking time to the boarding stop and an appropriate boarding buffer.

Example:

Bus departure: 8:15 AM

Walk to stop: 7 minutes

Boarding buffer: 3 minutes

Recommended leave-home time: 8:05 AM

Do not tell the student to leave home at the exact time their bus departs.

Treat each journey's leave_by as the backend-calculated door-to-door departure time. Use it directly when evaluating departure feasibility and scheduling reminders. Do not subtract walking time or boarding buffers again.

If the student's current time or location makes leave_by infeasible, request a fresh route plan.

## 11. Expected Decision Output

After evaluating journeys, provide:

### Event

- Event title
- Event start time
- Preferred arrival deadline

### Primary Journey

- Provider and route
- Recommended leave-home time
- Boarding stop
- Vehicle departure time
- Expected arrival time
- Transfers, if any
- Availability status
- Reason for recommendation

### Backup Journey

- Provider and route
- Recommended leave-home time
- Boarding stop
- Vehicle departure time
- Expected arrival time
- Conditions under which the backup remains feasible

### Warnings

Include relevant warnings about:

- Reduced arrival buffer
- High-risk transfers
- Unverified service
- Service disruptions
- No feasible backup
- Late arrival

Pass the selected journey and recommended leave-home time to `notifications.md`.

## 12. Student-Facing Response

Keep responses concise and suitable for iMessage or RCS.

Example:

🚌 Your 9 AM class

✅ Best route: Orbit
Leave home: 8:05 AM
Expected arrival: 8:45 AM

🔄 Backup: Valley Metro
Leave home: 8:12 AM
Expected arrival: 8:55 AM

⚠️ The backup gets you there before class, but misses your preferred 10-minute arrival buffer.

Want a reminder before you leave?

The example times are illustrative, not live transit information.

## 13. Handling Missing or Uncertain Data

If the route provider returns no journeys:

- Do not invent transportation options.
- Check whether the origin and destination are correct.
- Try another supported source when appropriate.
- Explain when transit information is unavailable.

If service availability is uncertain:

- Mark the affected journey as uncertain.
- Prefer a confirmed alternative when feasible.
- Do not claim the uncertain journey is guaranteed.

If no route meets the event deadline:

- Identify the earliest realistic arrival.
- Clearly state that the student may be late.
- Offer alternatives when available.

## 14. Integration With Other Files

### onboarding.md

Provides student preferences, starting location, and arrival buffer.

### destinations.md

Provides the resolved destination address or coordinates.

### directions.md

Provides candidate door-to-door journeys and their timing details.

### transit-sources.md

Verifies operating schedules, service availability, and relevant disruptions.

### notifications.md

Schedules reminders using the selected journey's recommended departure time.

## 15. Important Rules

- Never guarantee arrival times.
- Never invent transit schedules or live vehicle positions.
- Never recommend a route that has already departed.
- Never assume a backup remains feasible after the primary is missed.
- Never ignore walking time to the boarding stop.
- Never assume that all campus shuttle routes operate on the same schedule.
- Never select a journey that violates the student's accessibility requirements.
- Prefer confirmed, feasible journeys over uncertain alternatives.
- Always distinguish between preferred arrival time and actual class start time.
- Recalculate recommendations when the student's current location or departure time changes.