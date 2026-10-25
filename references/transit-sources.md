# Transit Sources and Service Availability

## Purpose

This document instructs Cubbie how to verify transportation availability for students using Cubbie Transit Buddy.

Cubbie already supports web search, browsing, and reading websites. Use these built-in capabilities to retrieve public transit information.

Do not assume that a transportation service is operating solely because it appears in a route-planning result.

The goal is to determine whether a candidate journey is available on the student's travel date and whether any known disruption affects it.

## 1. Supported Transportation Services

Initially support transportation around Arizona State University's Tempe campus.

### A. Valley Metro

Official transit information:
https://www.valleymetro.org

Transportation:
- Public buses
- Light rail
- Streetcar

Check:
- Route-specific operating schedules
- Boarding and destination stops
- Service frequency
- Weekend and holiday schedules
- Relevant service alerts
- Live arrival information, when available

### B. Tempe Orbit

Official source:
https://www.tempe.gov/government/transportation-and-sustainability/transportation/bus-light-rail-paratransit-streetcar/orbit

Transportation:
- Mercury
- Venus
- Earth
- Mars
- Jupiter
- Saturn

Check:
- Whether the requested Orbit route serves the journey
- Operating hours for the specific route
- Service frequency for the requested day
- Route detours and temporary changes
- Whether the selected journey uses a shortened route
- Boarding restrictions or designated stops

Do not assume every Orbit vehicle travels the entire route.

### C. ASU Intercampus Shuttles

Official source:
https://cfo.asu.edu/shuttles

Transportation:
- ASU-operated intercampus shuttle services

Check:
- Which campuses the route connects
- Route-specific schedules
- Weekend availability
- University-observed holidays
- Service changes during academic breaks
- Boarding locations
- Live shuttle tracking, when accessible

Do not assume that all ASU shuttle routes share the same operating schedule.

### D. Tempe FLASH

Official source:
https://cfo.asu.edu/transit

Transportation:
- FLASH routes serving the Tempe campus

Check:
- Weekday operating hours
- Limited service during university holidays and class breaks
- Current route and stop information
- Whether FLASH serves the student's origin and destination

Do not confuse FLASH with ASU intercampus shuttle routes.

## 2. When to Verify Transit Availability

Verify transportation information when:

1. A student requests a commute plan.
2. A class or event is approaching.
3. A journey includes a university shuttle.
4. A journey occurs on a weekend or holiday.
5. A journey occurs during an academic break.
6. A student reports missing a bus or shuttle.
7. A scheduled commute check-in requires updated route information.

Only check services relevant to the student's requested journey.

## 3. Verification Workflow

Receive the Never Late API response through `directions.md` and read its `journeys[]` array. Treat each entry as a candidate journey, not a verified or recommended route.

For each journey, inspect its `steps[]` array and verify every step where `type` is `"transit"`. For journeys containing multiple transit legs, verify each leg independently.

Walking-only journeys do not require transit service verification. Pass them to `commute-intelligence.md` for feasibility evaluation.

Preserve each journey's `id` so verification results can be matched to the correct journey, even when multiple journeys use the same route at different departure times.

For each candidate journey:

### Step 1: Identify the transportation provider

Determine whether the journey uses:
- Valley Metro
- Tempe Orbit
- ASU intercampus shuttle
- FLASH
- A combination of transportation services

For each transit leg in each candidate journey's `steps[]` within `journeys[]`, use the combination of `provider`, `route`, `direction`, `boarding_stop`, `destination_stop`, and other available transit-leg information to identify the appropriate official transit source listed in Section 1. Never rely solely on the `provider` field.

Google Routes API may group Tempe Orbit, light rail, streetcar, and regular bus routes under `Valley Metro`. When `route` identifies an Orbit service, such as `Orbit Mars` or `Orbit Mercury`, consult the official Tempe Orbit source even if `provider` is `Valley Metro`.

Preserve the original `provider` and `route` values returned by the backend without overwriting them. Identify the official source using existing journey information; do not introduce a new `service` field or require changes to the Never Late API response.

If the appropriate official source cannot be confidently identified, mark the verification as `UNCERTAIN` rather than guessing.

### Step 2: Verify the route

Confirm that the route serves the required boarding and destination stops.

For multi-leg journeys, verify each transit leg separately.

### Step 3: Verify the operating schedule

Check the service schedule for the exact travel date.

Consider:
- Weekdays
- Saturdays
- Sundays
- Public holidays
- University holidays
- Academic breaks
- Route-specific exceptions

Never infer availability solely from the day of the week.

### Step 4: Check service disruptions

Search for relevant:
- Cancellations
- Detours
- Stop closures
- Temporary schedule changes
- Service suspensions

Only apply alerts that affect the requested route, direction, stop, and travel time.

### Step 5: Check live information

When available, retrieve current arrival predictions or vehicle tracking information.

Distinguish between:
- Scheduled arrival
- Real-time prediction
- Vehicle position
- Unverified estimate

A vehicle position alone does not establish an exact arrival time.

### Interpret backend routing information

Interpret these fields in the Never Late API's `journeys[]` response as follows:

- `on_time: true` means routing data predicts arrival by the requested `arrive_by` deadline. It does not confirm that the transit service is operating.
- `availability: "UNCERTAIN"` is the initial transit availability status returned by the backend, not the final verification result.
- `realtime: false` means transit departure information is scheduled rather than a live prediction.
- `service_alerts_checked: false` means relevant official service alerts have not yet been checked.

Treat the backend's `availability` as an initial status, not an authoritative confirmation. Independently verify transit schedules, operating hours, and relevant service alerts using the official sources listed in this document, then assign a final status of `AVAILABLE`, `UNAVAILABLE`, or `UNCERTAIN` using Step 6.

`AVAILABLE` means the published schedule supports the journey and no known applicable disruption prevents it. It does not guarantee that a vehicle is currently running or will arrive on time. If official information cannot confirm the relevant service, retain `UNCERTAIN` rather than assuming availability.

Keep the backend's original routing information intact. Store Cubbie's verification result separately so `commute-intelligence.md` can distinguish routing feasibility from verified transit availability, without changing the Never Late API response schema.

### Step 6: Determine availability

Assign one of the following statuses:

**AVAILABLE**

The published schedule supports the journey and no known applicable disruption prevents it.

**UNAVAILABLE**

An authoritative source confirms the service does not operate or the relevant journey is canceled.

**UNCERTAIN**

The service cannot be verified, relevant information is outdated, or conflicting sources prevent a reliable conclusion.

Absence of a service alert is not proof that a vehicle is running on time.

## 4. Source Priority

Prefer information in this order:

1. Current official service alerts and live information from the transportation operator.
2. Official route-specific schedules for the travel date.
3. Official transportation announcements and notices.
4. Google Maps route-planning information.
5. Other credible public sources when official information is unavailable.

A newer, route-specific notice may override a general timetable.

When sources conflict, explain the uncertainty rather than silently choosing one.

## 5. Expected Output

Provide the following information for each transit leg or journey:

- Provider
- Route name or number
- Travel date
- Boarding stop
- Destination stop
- Scheduled departure time, if available
- Scheduled arrival time, if available
- Live prediction, if available
- Availability status
- Applicable service alerts
- Information source
- Time the information was checked
- Relevant uncertainty or limitations

Pass this information to the commute-intelligence workflow.

## 6. Handling Missing Information

If a source is unavailable:

1. Attempt another reliable source.
2. Do not invent schedules or vehicle locations.
3. Mark the affected information as uncertain.
4. Continue evaluating other available transportation options.
5. Inform the student when uncertainty affects the recommendation.

If no route can be verified, do not present a journey as guaranteed.

## 7. Integration With Other Skill Files

### directions.md

Provides candidate journeys, including route names, stops, departure times, and arrival times.

### transit-sources.md

Verifies operating schedules, service exceptions, and current availability.

### commute-intelligence.md

Uses verified information to rank journeys and select primary and backup routes.

### notifications.md

Uses the selected journey to schedule reminders and communicates relevant service changes when a supported check detects them.

## 8. Important Rules

- Never confuse Tempe Orbit with ASU-operated shuttle services.
- Never assume all university shuttles operate on weekends.
- Never assume university holidays affect every transportation provider equally.
- Never describe scheduled arrival times as live predictions.
- Never promise that a student will arrive on time.
- Always account for service uncertainty when recommending a route.
- Keep student-facing messages concise.