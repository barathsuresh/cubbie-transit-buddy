#!/usr/bin/env python3
"""Cubbie-side client for the Never Late backend. Standard library only.

Vendored from https://never-late-api-966291054830.us-west1.run.app/client.py
Fetched 2026-10-24 (re-vendored for v2); backend /health version: never-late-api-00008-8nc.
Do not download this file at runtime: the Skill runs the copy in its own folder.

CHANGES (made for cubbie-transit-buddy; the backend team can merge them back):
  1. Built-in defaults DEFAULT_URL / DEFAULT_TOKEN; NEVER_LATE_URL / NEVER_LATE_TOKEN override them.
  2. HTTPS only: any other base URL is refused (fix_input, exit 2), except http://127.0.0.1 and
     http://localhost for local mock-server tests.
  3. --sample [ok|no_transit|error|short_trip]: reads assets/sample_<name>.json instead of calling the network,
     runs it through the same output code, saves nothing.
  4. Adds "live_check_needed" to the output: true unless data.data_quality is "live" or
     data.verification.live_vehicle_tracking is true.
  5. The token is scrubbed from anything printed.
  6. The request file is closed after reading.
  7. Guard for a backend bug found in never-late-api-00008-8nc and fixed in never-late-api-00011-njh: if a v2
     WALK/BICYCLE/DRIVE journey comes back with a leave_by earlier than the request time (data.generated_at),
     it is moved to "leave now": leave_by = request time, arrive_at and on_time recomputed,
     "leave_by_adjusted": true added. Transit journeys are never moved (leaving later would miss the bus).
     A no-op against the fixed backend; kept in case the bug returns.
  Everything else (retries, timeouts, message composition, actions, exit codes) is unchanged.

Usage:
  python3 never_late.py request.json
  echo '{...}' | python3 never_late.py -
  python3 never_late.py --sample [ok|no_transit|error|short_trip]

Input JSON is the request body. If it has "modes" it goes to POST /v2/plan (candidate journeys, YOU choose);
otherwise to POST /v1/plan (backend picks primary + backup).

Prints ONE JSON object to stdout:
  {"action": "send_alert" | "journeys" | "web_search_fallback" | "fix_input",
   "message":  short text Cubbie can send (present for send_alert, optional otherwise),
   "search_hint": what to search for (web_search_fallback only),
   "maps_link": url,
   "reason": error code from the backend, when it sent one,
   "live_check_needed": true unless the backend's times are live,
   "data": full backend response (when one was received)}

  v2 success gives action "journeys" with "options" (one short line per journey) and the full "data".
Exit code: 0 send_alert/journeys, 3 web_search_fallback, 2 fix_input.
The script never raises: any failure becomes web_search_fallback so Cubbie always has a next step.
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

DEFAULT_URL = "https://never-late-api-966291054830.us-west1.run.app"
DEFAULT_TOKEN = "54c95c1fe69bb2dc817900ba4e811fd2"
ASSETS = Path(__file__).resolve().parent.parent / "assets"
SAMPLES = ("ok", "no_transit", "error", "short_trip")
LOCAL_HTTP = ("http://127.0.0.1", "http://localhost")

TIMEOUT_S = 12  # backend caps a whole request at 10s
RETRIES = 1  # one retry on timeout / network / 5xx


def call(url: str, token: str, body: dict, path: str = "/v1/plan"):
    """Return (http_status, parsed_json_or_None). status 0 = network failure/timeout."""
    req = urllib.request.Request(
        url.rstrip("/") + path,
        data=json.dumps(body).encode(),
        headers={"content-type": "application/json", "x-skill-token": token},
        method="POST",
    )
    for attempt in range(RETRIES + 1):
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT_S) as r:
                return r.status, json.loads(r.read())
        except urllib.error.HTTPError as e:
            try:
                data = json.loads(e.read())
            except Exception:
                data = None
            if e.code == 429 and attempt < RETRIES:
                time.sleep(min(int(e.headers.get("Retry-After", "2")), 5))
                continue
            if e.code >= 500 and attempt < RETRIES:
                time.sleep(1)
                continue
            return e.code, data
        except Exception:  # timeout, DNS, TLS, bad JSON
            if attempt < RETRIES:
                time.sleep(1)
                continue
            return 0, None
    return 0, None


def compose_alert(d: dict) -> str:
    """Short iMessage-style text from a successful response."""
    trip, p = d.get("trip", {}), d["primary"]
    dest = trip.get("destination_label") or "class"
    lines = []
    if p["mode"] == "TRANSIT":
        bus = next((s for s in p["steps"] if s["type"] == "transit"), None)
        head = f"Leave by {p['leave_by']} for {dest}"
        if bus:
            head += f" - {bus['line']} from {bus['stop']} at {bus['depart_at']}"
        lines.append(head + f". Arrive ~{p['arrive_at']}.")
        if p.get("backup"):
            b = p["backup"]
            lines.append(f"Backup if you miss it: {b['text']}, arrive ~{b['arrive_at']}.")
    else:
        lines.append(f"Leave by {p['leave_by']} ({p['mode'].lower()}) for {dest}. Arrive ~{p['arrive_at']}.")
    if not p["on_time"]:
        lines.append("Heads up: you'll be late on this plan.")
    w = d.get("weather") or {}
    if w.get("impact"):
        lines.append(w["impact"] + ".")
    for a in w.get("alerts") or []:
        until = f" until {a['ends'][11:16]}" if a.get("ends") else ""
        lines.append(f"Weather alert: {a['event']}{until}.")
    for a in p.get("alerts", []):
        lines.append(a)
    if d.get("suggestion"):
        lines.append(d["suggestion"] + ".")
    return " ".join(lines)


def search_hint(d, body) -> str:
    if d and d.get("fallback_hint"):
        return d["fallback_hint"]
    dest = (body.get("destination") or {})
    place = dest.get("label") or dest.get("address") or "the destination"
    return f"Search for transit or walking directions and live status to {place} arriving by {body.get('arrive_by')}"


def option_lines(d: dict) -> list:
    """One short line per v2 journey: 'Orbit Mars: leave 08:20, arrive 08:43 (on time)'."""
    out = []
    for j in d.get("journeys") or []:
        name = j.get("route") or j["mode"].lower()
        out.append(f"{name}: leave {j['leave_by'][11:16]}, arrive {j['arrive_at'][11:16]} "
                   f"({'on time' if j['on_time'] else 'LATE'})")
    return out


def fix_past_leave_by(d: dict) -> None:
    """CHANGE 7: move non-transit journeys whose leave_by is already past to "leave now"."""
    try:
        now = datetime.fromisoformat(d["generated_at"])
        deadline = datetime.fromisoformat(d["trip"]["arrive_by"])
    except Exception:
        return
    if now.second or now.microsecond:  # round up: never tell the student a time that has passed
        now = now.replace(second=0, microsecond=0) + timedelta(minutes=1)
    for j in d.get("journeys") or []:
        if j.get("mode") == "TRANSIT":
            continue
        try:
            leave, arrive = datetime.fromisoformat(j["leave_by"]), datetime.fromisoformat(j["arrive_at"])
            minutes = int(j["total_min"])
        except Exception:
            continue
        if leave >= now:
            continue
        arrive = max(arrive, now + timedelta(minutes=minutes))
        j.update(leave_by=now.isoformat(), arrive_at=arrive.isoformat(), on_time=arrive <= deadline,
                 leave_by_adjusted=True)


def handle(url: str, token: str, body: dict, caller=call):
    v2 = "modes" in body
    status, d = caller(url, token, body, "/v2/plan" if v2 else "/v1/plan")
    if v2 and isinstance(d, dict):
        fix_past_leave_by(d)
    link = (d or {}).get("maps_link")

    if status in (400, 401):  # our bug or bad token: retrying/searching won't fix the call
        msg = ((d or {}).get("error") or {}).get("message", "request rejected")
        return {"action": "fix_input", "message": f"Never Late rejected the request ({status}): {msg}", "data": d}, 2

    if v2 and d and d.get("ok") and not d.get("fallback_needed") and d.get("journeys"):
        return {"action": "journeys", "options": option_lines(d), "maps_link": link, "data": d}, 0
    if d and d.get("ok") and not d.get("fallback_needed") and d.get("primary"):
        return {"action": "send_alert", "message": compose_alert(d), "maps_link": link, "data": d}, 0

    # fallback_needed, ok:false, 429 after retry, timeout, network failure, malformed reply
    out = {"action": "web_search_fallback", "search_hint": search_hint(d, body), "data": d}
    if link:
        out["maps_link"] = link
    if v2 and d and d.get("journeys"):
        out["message"] = "Backend had no transit data; options: " + "; ".join(option_lines(d))
    elif d and d.get("alternatives"):  # partial info is still useful context for the search
        out["message"] = "Backend had no transit data; alternatives: " + ", ".join(
            f"{a['mode'].lower()} {a['minutes']} min (leave by {a['leave_by']})" for a in d["alternatives"]
        )
    if d and d.get("error"):
        out["reason"] = d["error"].get("code")
        if out["reason"] == "ADDRESS_NOT_FOUND":  # searching won't help; the student must fix the address
            out["search_hint"] = f"Ask the student to confirm their {d['error'].get('field') or 'trip'} address; it could not be located"
    return out, 3


def add_live_flag(out: dict) -> dict:
    d = out.get("data") or {}
    live = d.get("data_quality") == "live" or (d.get("verification") or {}).get("live_vehicle_tracking") is True
    out["live_check_needed"] = not live
    return out


def emit(out: dict, token: str) -> None:
    text = json.dumps(out, ensure_ascii=False)
    if token and len(token) >= 8:
        text = text.replace(token, "***")
    print(text)


def run_sample(name: str) -> int:
    if name not in SAMPLES:
        emit({"action": "fix_input", "message": f"--sample takes one of: {', '.join(SAMPLES)}"}, "")
        return 2
    try:
        with open(ASSETS / f"sample_{name}.json") as f:
            response = json.load(f)
        with open(ASSETS / "sample_request.json") as f:
            body = json.load(f)
    except Exception as e:
        emit({"action": "fix_input", "message": f"sample file missing or unreadable: {e}"}, "")
        return 2
    out, code = handle("", "", body, caller=lambda *_: (200, response))
    emit(add_live_flag(out), "")
    return code


def main() -> int:
    if len(sys.argv) >= 2 and sys.argv[1] == "--sample":
        return run_sample(sys.argv[2] if len(sys.argv) > 2 else "ok")
    url = os.environ.get("NEVER_LATE_URL") or DEFAULT_URL
    token = os.environ.get("NEVER_LATE_TOKEN") or DEFAULT_TOKEN
    if len(sys.argv) < 2:
        emit({"action": "fix_input", "message": "usage: never_late.py <request.json|-> or --sample [ok|no_transit|error|short_trip]"}, token)
        return 2
    if not (url.startswith("https://") or any(url == h or url.startswith(h + ":") or url.startswith(h + "/") for h in LOCAL_HTTP)):
        emit({"action": "fix_input", "message": "refusing a backend URL that is not https://"}, token)
        return 2
    try:
        if sys.argv[1] == "-":
            body = json.load(sys.stdin)
        else:
            with open(sys.argv[1]) as f:
                body = json.load(f)
    except Exception as e:
        emit({"action": "fix_input", "message": f"bad request json: {e}"}, token)
        return 2
    if not isinstance(body, dict):
        emit({"action": "fix_input", "message": "bad request json: expected an object"}, token)
        return 2
    try:
        out, code = handle(url, token, body)
    except Exception:  # never crash Cubbie
        out, code = {"action": "web_search_fallback", "search_hint": search_hint(None, body)}, 3
    emit(add_live_flag(out), token)
    return code


if __name__ == "__main__":
    sys.exit(main())
