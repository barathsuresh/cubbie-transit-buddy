# Proactive Commute Notifications

## Purpose

This document defines how Cubbie Transit Buddy schedules and manages commute reminders for students.

The objective is to notify students when they should prepare for and begin their journeys, using their class schedules, selected transportation routes, and personal preferences.

Use Cubbie's built-in reminders and scheduled check-ins to deliver notifications through the student's supported messaging channel.

Do not implement a separate notification service unless Cubbie's existing capabilities cannot support a required feature.

## 1. When to Use This Workflow

Use this workflow when:

- A student requests a reminder for an upcoming commute.
- A student enables recurring commute assistance.
- Cubbie creates a commute plan for a calendar event.
- A student's class or event schedule changes.
- A previously selected route becomes unavailable during a scheduled check.
- A student requests an updated departure reminder.

Do not schedule recurring commute notifications without the student's consent.

## 2. Required Inputs

Before scheduling a notification, obtain:

### Event Information

- Event title
- Event date
- Event start time
- Event location
- Local time zone
- Calendar event identifier, when available

### Student Preferences

Retrieve from `onboarding.md` or Cubbie's memory:

- Whether commute reminders are enabled
- Preferred preparation reminder lead time
- Preferred notification frequency
- Transportation preferences
- Starting location

### Journey Information

Retrieve from `commute-intelligence.md`:

- Primary journey
- Backup journey, if available
- Recommended leave-home time
- Boarding stop
- Vehicle departure time
- Expected arrival time
- Availability status
- Relevant service warnings

Never calculate reminder times from the vehicle departure time alone.

Use the selected primary journey's leave_by value as the recommended leave-home time. This value already accounts for door-to-door travel. Do not subtract walking time or boarding buffers again.

## 3. Notification Types

### A. Commute Preview

Purpose:

Give students an overview of an upcoming journey before they need to travel.

Example:

"🚌 Tomorrow's first class starts at 9 AM. I'll check your commute and remind you when it's time to leave."

Trigger:

- The evening before an upcoming class, if the student enables evening previews.
- At another time explicitly chosen by the student.

Behavior:

1. Read the relevant upcoming calendar event.
2. Confirm the starting location.
3. Retrieve a commute plan when appropriate.
4. Present the planned journey or indicate when it will be checked again.
5. Avoid presenting tomorrow's scheduled transit times as live vehicle predictions.

### B. Preparation Reminder

Purpose:

Give the student time to get ready before leaving.

Example:

"🎒 Your 9 AM class is coming up. Start getting ready! Your current plan is to leave at 8:05 AM."

Trigger:

Preparation reminder time = Recommended leave-home time - Student's preparation lead time

Example:

Recommended leave-home time: 8:05 AM

Preparation lead time: 20 minutes

Preparation reminder: 7:45 AM

Allow the student to configure the preparation lead time.

Do not assume every student needs the same preparation time.

### C. Departure Reminder

Purpose:

Tell the student when they should leave their starting location.

Example:

"🚌 Time to leave! Head to your boarding stop now. Your bus is scheduled to depart at 8:15 AM."

Trigger:

At the recommended leave-home time.

Include:

- Route name or number
- Boarding stop
- Scheduled vehicle departure time
- Any relevant service warning

Avoid unnecessary details when the student needs to leave immediately.

For walking-only journeys, remind the student to begin walking at leave_by. Do not include a boarding stop, transit route, or vehicle departure time.

### D. Backup Route Notification

Purpose:

Help students recover when their primary journey becomes unavailable or is missed.

Example:

"⚠️ Your original route may no longer work. I found another option that could get you to class before 9 AM."

Trigger:

- The student reports missing the primary vehicle.
- A scheduled check detects a relevant disruption.
- A newly calculated route invalidates the previous recommendation.

Behavior:

1. Retrieve the current time.
2. Confirm the student's current location if necessary.
3. Recalculate candidate journeys using `directions.md`.
4. Verify relevant service information using `transit-sources.md`.
5. Select a feasible alternative using `commute-intelligence.md`.
6. Inform the student of the updated recommended leave time.

Do not automatically send a missed-bus alert merely because the scheduled departure time has passed.

Unless the student reports missing the vehicle or a supported source confirms the situation, Cubbie does not know whether the student boarded.

## 4. Notification Preferences

During onboarding, ask students whether they want commute reminders.

Suggested options:

- Departure reminders only
- Preparation and departure reminders
- Evening commute previews
- Daily commute check-ins
- No automatic reminders

Ask for the student's preferred preparation lead time.

Example:

"Would you like a reminder 15 or 20 minutes before you need to leave, or would you prefer another time?"

Respect the student's selected preferences.

Allow students to modify or disable notifications at any time.

## 5. Scheduling Workflow

When a student enables commute reminders:

### Step 1: Identify the Event

Read the relevant upcoming event from the student's connected Google Calendar.

Confirm:

- Event date
- Start time
- Destination
- Whether travel is required

### Step 2: Retrieve the Commute Plan

Use the destination and route-planning workflows to determine:

- Recommended primary journey
- Backup journey
- Recommended leave-home time

### Step 3: Calculate Reminder Times

Calculate the preparation reminder relative to the recommended leave-home time.
Schedule the departure reminder at the selected primary journey's leave_by time.

When a supported scheduled check runs, verify that the selected journey is still feasible using the current time and available transit information. If the journey is no longer feasible, replan before sending an outdated departure instruction.

When an event is rescheduled, canceled, or its destination changes, update or cancel the associated commute reminders. Do not leave reminders active for obsolete journeys.

Use the event's applicable IANA time zone, normally America/Phoenix for ASU and Tempe commutes. Preserve the time-zone offset when interpreting leave_by timestamps from the Never Late API.

### Step 4: Create Cubbie Reminders

Use Cubbie's built-in reminder or scheduled-task capability.

Associate each scheduled reminder with the calendar event identifier and reminder type. Before creating a reminder, check whether an equivalent reminder already exists. Update or replace it instead of creating a duplicate. Cancel obsolete reminders when an event is canceled or its commute plan changes.

If a calendar event identifier is unavailable, use a stable combination of event date, start time, destination, and reminder type to identify equivalent reminders.

Do not create a custom SMS or RCS delivery system.

### Step 5: Confirm Scheduling

Tell the student which reminders were successfully scheduled.

Example:

"Done! I'll remind you at 7:45 AM to get ready and at 8:05 AM to leave."

Only confirm reminders that Cubbie's scheduling capability has successfully created or updated. If scheduling fails or is unavailable, explain the limitation instead of promising a reminder.