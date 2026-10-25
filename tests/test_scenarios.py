"""Automated parts of the Transit Buddy test cases (tests/test-cases.md). Standard library only.

  python3 -m unittest discover -s tests -v                      # offline parts
  LIVE=1 NEVER_LATE_TOKEN=<token> python3 -m unittest ...     # plus live backend calls

What runs here: building resolution against data/asu-buildings.json (TC02, TC12), the client's handling of the
fictional TC04 journeys, and live backend calls for TC01, TC03, TC05, TC10 and TC11 using the sample calendar's
buildings on the next matching weekday. Everything that needs Cubbie itself (calendar, reminders, web checks,
the wording of replies) is a manual test in tests/test-cases.md.
"""
import json
import math
import os
import threading
import time
import unittest
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from test_never_late import ASSETS, FAKE_TOKEN, SKILL, run

PHOENIX = timezone(timedelta(hours=-7))  # Arizona: no daylight saving time
BUILDINGS = json.loads((SKILL / "data" / "asu-buildings.json").read_text())["buildings"]
BY_CODE = {b["code"]: b for b in BUILDINGS}
FIXTURES = Path(__file__).resolve().parent / "fixtures"

# Test student (fictional). The start is a public apartment complex; address from ASU's off-campus housing
# listing, https://offcampushousing.asu.edu/city/tempe-az/listing/villas-on-apache-12196
YUGO = {"label": "Yugo Tempe Villas", "address": "1111 E Apache Blvd, Tempe, AZ 85281"}
BUFFER = 10


def km(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (*a, *b))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 6371 * 2 * math.asin(math.sqrt(h))


def iso(t):
    return datetime.fromisoformat(t)


def place(code, room=""):
    b = BY_CODE[code]
    return {"label": f"{b['name']} ({code}) {room}".strip(), "address": b["address"], "lat": b["lat"], "lng": b["lng"]}


def next_weekday(weekday):
    """Next date (1-7 days ahead, Phoenix time) falling on weekday (Mon=0), so it is a class day in the future."""
    today = datetime.now(PHOENIX).date()
    return today + timedelta(days=(weekday - today.weekday()) % 7 or 7)


def at(day, hh, mm):
    return datetime(day.year, day.month, day.day, hh, mm, tzinfo=PHOENIX).isoformat()


def transit_steps(j):
    return [s for s in j["steps"] if s["type"] == "transit"]


# ---------------------------------------------------------------------------------------------------------
# TC02 / TC12: building resolution data


class BuildingData(unittest.TestCase):
    def test_sample_calendar_buildings_resolve(self):
        # ISTB4 101 / ISTB4 130 (CSE 110), Lattie F. Coor 4403 (ENG 102), Memorial Union, Hayden Library
        for code, name_part in [("ISTB4", "Interdisciplinary Science and Technology IV"), ("COOR", "Coor"),
                                ("MU", "Memorial Union"), ("LIB", "Hayden Library")]:
            b = BY_CODE.get(code)
            self.assertIsNotNone(b, f"{code} missing from the building list")
            self.assertIn(name_part, b["name"])
            self.assertEqual(b["campus"], "Tempe")

    def test_names_match_for_name_only_locations(self):
        # "Memorial Union" and "Hayden Library" appear by name, not code, in the sample calendar
        names = {b["name"] for b in BUILDINGS}
        self.assertIn("Memorial Union", names)
        self.assertIn("Hayden Library", names)

    def test_psf_is_not_guessed(self):
        # TC02: ASU's pages give no street address for the Bateman F wing (PSF), so it is deliberately absent;
        # destinations.md must use the web and ask the student to confirm, never invent an address.
        self.assertNotIn("PSF", BY_CODE)

    def test_unknown_code_is_absent(self):
        # TC12: an unrecognized code must not resolve to anything
        for code in ("XYZQ", "HLMKX", ""):
            self.assertNotIn(code, BY_CODE)

    def test_every_entry_is_verifiable(self):
        self.assertEqual(len(BY_CODE), len(BUILDINGS), "duplicate building codes")
        for b in BUILDINGS:
            with self.subTest(code=b["code"]):
                for field in ("code", "name", "campus", "address", "lat", "lng", "source_url", "coords_source"):
                    self.assertTrue(b.get(field) not in (None, ""), field)
                self.assertTrue(b["source_url"].startswith("https://") and ".asu.edu/" in b["source_url"])
                self.assertRegex(b["address"], r"^\d+ .*\b8528\d\b")
                self.assertTrue(33.40 < b["lat"] < 33.45 and -111.95 < b["lng"] < -111.91, "outside ASU Tempe area")

    def test_no_two_buildings_share_a_pin(self):
        pins = [(b["lat"], b["lng"]) for b in BUILDINGS]
        self.assertEqual(len(pins), len(set(pins)))


# ---------------------------------------------------------------------------------------------------------
# TC04: fictional journeys A/B/C through the client


class FixtureServer(BaseHTTPRequestHandler):
    body = b"{}"

    def log_message(self, *a):
        pass

    def do_POST(self):
        self.rfile.read(int(self.headers.get("content-length", 0)))
        self.send_response(200)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(self.body)))
        self.end_headers()
        self.wfile.write(self.body)


class TC04PrimaryAndBackup(unittest.TestCase):
    """The client must pass the journeys through unchanged; the facts commute-intelligence.md must see hold."""

    @classmethod
    def setUpClass(cls):
        FixtureServer.body = (FIXTURES / "tc04_journeys.json").read_bytes()
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), FixtureServer)
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
        env = {"NEVER_LATE_URL": f"http://127.0.0.1:{cls.server.server_port}", "NEVER_LATE_TOKEN": FAKE_TOKEN}
        cls.code, cls.out, _ = run(["-"], env, (ASSETS / "sample_request.json").read_text())
        cls.journeys = {j["id"][-1]: j for j in cls.out["data"]["journeys"]}

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()

    def test_passed_through_unchanged(self):
        self.assertEqual((self.code, self.out["action"]), (0, "journeys"))
        self.assertEqual(self.out["data"], json.loads((FIXTURES / "tc04_journeys.json").read_text()))
        self.assertEqual(len(self.out["options"]), 3)
        self.assertIn("LATE", self.out["options"][2])

    def test_b_is_the_justified_primary(self):
        class_start = iso(self.out["data"]["trip"]["arrive_by"])
        preferred = class_start - timedelta(minutes=BUFFER)  # 8:50
        meets = [k for k, j in self.journeys.items() if iso(j["arrive_at"]) <= preferred]
        self.assertEqual(sorted(meets), ["A", "B"])
        fewest = min(len(transit_steps(self.journeys[k])) - 1 for k in meets)
        best = max((k for k in meets if len(transit_steps(self.journeys[k])) - 1 == fewest),
                   key=lambda k: iso(self.journeys[k]["leave_by"]))
        self.assertEqual(best, "B")  # meets 8:50, no transfers, latest departure

    def test_no_post_miss_backup(self):
        b = self.journeys["B"]
        later = [k for k, j in self.journeys.items() if iso(j["leave_by"]) > iso(b["leave_by"])]
        self.assertEqual(later, ["C"])  # A leaves earlier, so it can't help after missing B
        self.assertFalse(self.journeys["C"]["on_time"])  # C is late: there is no feasible backup


# ---------------------------------------------------------------------------------------------------------
# Live: TC01, TC03, TC05, TC10, TC11


def live_plan(origin, destination, arrive_by, now, modes=("TRANSIT", "WALK")):
    body = {"origin": origin, "destination": destination, "arrive_by": arrive_by, "modes": list(modes),
            "buffer_min": BUFFER, "now": now}
    for attempt in range(2):  # the backend allows 10 requests/min; wait out one rate-limit window
        code, out, raw = run(["-"], {"NEVER_LATE_TOKEN": os.environ["NEVER_LATE_TOKEN"]}, json.dumps(body))
        assert os.environ["NEVER_LATE_TOKEN"] not in raw
        if out.get("reason") != "RATE_LIMITED":
            break
        time.sleep(61)
    return code, out


@unittest.skipUnless(os.environ.get("LIVE") == "1" and os.environ.get("NEVER_LATE_TOKEN"), "set LIVE=1 and NEVER_LATE_TOKEN")
class LiveScenarios(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.monday = next_weekday(0)
        cls.class_start = at(cls.monday, 9, 0)  # CSE 110, ISTB4 101, Mon/Wed/Fri 9:00
        cls.code, cls.out = live_plan(YUGO, place("ISTB4", "101"), cls.class_start, at(cls.monday, 6, 0))
        cls.data = cls.out.get("data") or {}
        cls.journeys = cls.data.get("journeys") or []

    def assert_consistent(self, journeys, arrive_by, now):
        for j in journeys:
            with self.subTest(journey=j["id"]):
                self.assertEqual(j["on_time"], iso(j["arrive_at"]) <= iso(arrive_by), "on_time disagrees with times")
                self.assertGreaterEqual(iso(j["leave_by"]), iso(now) - timedelta(minutes=1), "leaves before now")
                self.assertLessEqual(iso(j["leave_by"]), iso(j["arrive_at"]))
                for s in transit_steps(j):
                    self.assertLessEqual(iso(j["leave_by"]), iso(s["depart_at"]))

    def test_tc01_first_class_commute(self):
        self.assertEqual((self.code, self.out["action"]), (0, "journeys"), self.out.get("search_hint"))
        dest = self.data["resolved"]["destination"]
        self.assertLess(km((dest["lat"], dest["lng"]), (BY_CODE["ISTB4"]["lat"], BY_CODE["ISTB4"]["lng"])), 0.3)
        transit = [j for j in self.journeys if j["mode"] == "TRANSIT"]
        self.assertTrue(transit, "no transit journey to ISTB4")
        for j in transit:
            self.assertTrue(any(s["type"] == "walk" for s in j["steps"]), "walking time missing")
            for s in transit_steps(j):
                self.assertEqual(s["source"], "google_routes")  # identifiable source, not invented
        on_time = [j for j in transit if j["on_time"]]
        if on_time:
            preferred = iso(self.class_start) - timedelta(minutes=BUFFER)
            self.assertTrue(any(iso(j["arrive_at"]) <= preferred for j in on_time), "nothing arrives by 8:50")
        self.assert_consistent(self.journeys, self.class_start, at(self.monday, 6, 0))

    def test_tc03_providers_and_timing_are_consistent(self):
        ids = [j["id"] for j in self.journeys]
        self.assertEqual(len(ids), len(set(ids)))
        for j in self.journeys:
            if j["mode"] != "TRANSIT":
                continue
            with self.subTest(journey=j["id"]):
                steps = transit_steps(j)
                self.assertTrue(all(s.get("provider") and s.get("route") for s in steps))
                self.assertEqual(j["provider"], steps[0]["provider"])
                for a, b in zip(steps, steps[1:]):
                    self.assertLessEqual(iso(a["arrive_at"]), iso(b["depart_at"]), "transfer leaves before arrival")
        self.assertIs(self.data["verification"]["live_vehicle_tracking"], False)
        self.assertIs(self.out["live_check_needed"], True)

    def test_tc05_missed_bus_excludes_expired_journeys(self):
        transit = [j for j in self.journeys if j["mode"] == "TRANSIT" and j["on_time"]]
        if not transit:
            self.skipTest("no on-time transit journey to miss")
        plan = max(transit, key=lambda j: iso(j["leave_by"]))
        missed = transit_steps(plan)[0]
        now = (iso(missed["depart_at"]) + timedelta(minutes=1)).isoformat()
        code, out = live_plan(YUGO, place("ISTB4", "101"), self.class_start, now)
        journeys = (out.get("data") or {}).get("journeys") or []
        for j in journeys:
            for s in transit_steps(j):
                self.assertGreater(iso(s["depart_at"]), iso(now) - timedelta(minutes=1), "expired bus offered")
        self.assert_consistent(journeys, self.class_start, now)

    def test_tc10_no_feasible_route(self):
        now = at(self.monday, 8, 58)  # two minutes before class, from home
        code, out = live_plan(YUGO, place("ISTB4", "101"), self.class_start, now)
        journeys = (out.get("data") or {}).get("journeys") or []
        self.assertFalse(any(j["on_time"] for j in journeys), "claims an on-time arrival that is impossible")
        self.assert_consistent(journeys, self.class_start, now)
        if journeys:  # the earliest realistic arrival can be reported
            self.assertTrue(min(iso(j["arrive_at"]) for j in journeys) > iso(self.class_start))

    def test_backend_walk_leave_by_respects_now(self):
        # Regression check: backend never-late-api-00008-8nc returned WALK/BICYCLE/DRIVE leave_by values already
        # past `now` (now 8:58 -> walk "leave 8:36, arrive 9:12"); fixed in never-late-api-00011-njh. If this
        # fails again, the backend regressed; scripts/never_late.py (CHANGE 7) still corrects it for students.
        now = at(self.monday, 8, 58)
        code, out = live_plan(YUGO, place("ISTB4", "101"), self.class_start, now)
        walk = [j for j in (out.get("data") or {}).get("journeys") or [] if j["mode"] == "WALK"]
        self.assertTrue(walk)
        self.assertNotIn("leave_by_adjusted", walk[0], "backend still returns a past leave_by")

    def test_tc11_between_classes(self):
        # Tue/Thu: ENG 102 at COOR ends 10:50, next is ISTB4 at 12:00. (The Mon/Wed/Fri ISTB4 -> PSF pair needs
        # the student to confirm PSF first; see test-cases.md.) The origin is the previous class, not home.
        tuesday = next_weekday(1)
        now, start = at(tuesday, 10, 50), at(tuesday, 12, 0)
        code, out = live_plan(place("COOR", "4403"), place("ISTB4", "130"), start, now)
        data = out.get("data") or {}
        orig = data["resolved"]["origin"]
        self.assertLess(km((orig["lat"], orig["lng"]), (BY_CODE["COOR"]["lat"], BY_CODE["COOR"]["lng"])), 0.3)
        walk = [j for j in data.get("journeys") or [] if j["mode"] == "WALK"]
        self.assertTrue(walk, "walking not considered between classes")
        self.assertTrue(walk[0]["on_time"], "a 70-minute window should be walkable")
        self.assert_consistent(data["journeys"], start, now)


if __name__ == "__main__":
    unittest.main()
