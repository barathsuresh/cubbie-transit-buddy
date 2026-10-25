"""Tests for scripts/never_late.py. Standard library only.

  python3 -m unittest discover -s tests -v                      # offline: samples + mock server
  LIVE=1 NEVER_LATE_TOKEN=<token> python3 -m unittest ...     # also one live call to the backend

Every run of the client uses a fresh temporary HOME and checks nothing was written to it.
"""
import json
import os
import socket
import subprocess
import sys
import tempfile
import threading
import unittest
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
SCRIPT = SKILL / "scripts" / "never_late.py"
ASSETS = SKILL / "assets"
FAKE_TOKEN = "fake-test-token-7f3a9c21d4"


def sample(name):
    return json.loads((ASSETS / f"sample_{name}.json").read_text())


def run(args, env_extra=None, stdin=None):
    """Run the client like Cubbie does, from the Skill folder, with an empty temporary HOME."""
    with tempfile.TemporaryDirectory() as home:
        # PYTHONDONTWRITEBYTECODE: some interpreters (macOS's built-in Python) cache bytecode under HOME
        env = {"PATH": os.environ.get("PATH", ""), "HOME": home, "PYTHONDONTWRITEBYTECODE": "1"}
        env.update(env_extra or {})
        p = subprocess.run([sys.executable, str(SCRIPT), *args], cwd=SKILL, env=env, input=stdin,
                           capture_output=True, text=True, timeout=60)
        leftovers = list(Path(home).rglob("*"))
    assert not leftovers, f"client wrote under HOME: {leftovers}"
    assert len(p.stdout) < 8000, "stdout over 8,000 characters"
    return p.returncode, json.loads(p.stdout), p.stdout + p.stderr


class Mock(BaseHTTPRequestHandler):
    """Replies according to the class attribute `mode`; counts requests in `hits`."""
    mode, hits, seen_token, path = "ok", 0, None, None

    def log_message(self, *a):
        pass

    def reply(self, status, body, headers=None):
        raw = body if isinstance(body, bytes) else json.dumps(body).encode()
        self.send_response(status)
        self.send_header("content-type", "application/json")
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        self.send_header("content-length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_POST(self):
        type(self).hits += 1
        type(self).seen_token = self.headers.get("x-skill-token")
        type(self).path = self.path
        self.rfile.read(int(self.headers.get("content-length", 0)))
        m = type(self).mode
        if m in ("ok", "no_transit", "error", "short_trip"):
            return self.reply(200, sample(m))
        if m == "400":
            return self.reply(400, {"ok": False, "error": {"code": "BAD_REQUEST", "message": "arrive_by needs a UTC offset", "field": "arrive_by"}})
        if m == "401":
            return self.reply(401, {"ok": False, "error": {"code": "UNAUTHORIZED", "message": "bad token"}})
        if m == "429":
            return self.reply(429, {"ok": False, "error": {"code": "RATE_LIMITED", "message": "slow down"}}, {"Retry-After": "1"})
        if m == "500":
            return self.reply(500, b"internal error")
        if m == "malformed":
            return self.reply(200, b"{not json")
        if m == "no_journeys":
            d = sample("ok")
            d["journeys"] = []
            return self.reply(200, d)
        if m == "all_late":
            d = sample("ok")
            for j in d["journeys"]:
                j["on_time"] = False
            return self.reply(200, d)
        if m == "past_leave_by":  # request made at 8:40:30, after the walk's and bike's natural leave times
            d = sample("ok")
            d["generated_at"] = "2026-10-26T08:40:30-07:00"
            return self.reply(200, d)
        if m == "v1_ok":
            return self.reply(200, V1_OK)


# minimal v1 /v1/plan answer, to check the client still handles requests without "modes"
V1_OK = {"ok": True, "data_quality": "scheduled", "fallback_needed": False,
         "trip": {"destination_label": "HLMK 120"},
         "primary": {"mode": "TRANSIT", "leave_by": "8:40 AM", "arrive_at": "8:54 AM", "on_time": True,
                     "steps": [{"type": "transit", "line": "Orbit Mars", "stop": "Terrace Rd", "depart_at": "8:46 AM"}]},
         "maps_link": "https://www.google.com/maps/dir/?api=1", "degraded": []}


class SampleMode(unittest.TestCase):
    def test_ok(self):
        code, out, _ = run(["--sample", "ok"])
        self.assertEqual((code, out["action"]), (0, "journeys"))
        self.assertEqual(len(out["options"]), len(out["data"]["journeys"]))
        self.assertIs(out["live_check_needed"], True)
        self.assertEqual(out["data"]["data_quality"], "scheduled")
        self.assertIs(out["data"]["verification"]["live_vehicle_tracking"], False)
        self.assertFalse(any("leave_by_adjusted" in j for j in out["data"]["journeys"]), "no-op when nothing is past")

    def test_no_transit(self):
        code, out, _ = run(["--sample", "no_transit"])
        self.assertEqual((code, out["action"]), (3, "web_search_fallback"))
        self.assertNotIn("reason", out)
        self.assertIn("search_hint", out)

    def test_short_trip_keeps_walk_journey(self):
        code, out, _ = run(["--sample", "short_trip"])
        self.assertEqual((code, out["action"]), (3, "web_search_fallback"))
        walk = [j for j in out["data"]["journeys"] if j["mode"] == "WALK"]
        self.assertTrue(walk and walk[0]["on_time"])
        self.assertIn("walk", out["message"])

    def test_error(self):
        code, out, _ = run(["--sample", "error"])
        self.assertEqual((code, out["action"], out["reason"]), (3, "web_search_fallback", "ADDRESS_NOT_FOUND"))

    def test_default_is_ok(self):
        self.assertEqual(run(["--sample"])[0], 0)

    def test_unknown_sample(self):
        code, out, _ = run(["--sample", "nope"])
        self.assertEqual((code, out["action"]), (2, "fix_input"))

    def test_sample_needs_no_network_or_token(self):
        code, _, _ = run(["--sample", "ok"], {"NEVER_LATE_URL": "https://127.0.0.1:1"})
        self.assertEqual(code, 0)


class MockServer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), Mock)
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
        cls.env = {"NEVER_LATE_URL": f"http://127.0.0.1:{cls.server.server_port}", "NEVER_LATE_TOKEN": FAKE_TOKEN}
        cls.request = (ASSETS / "sample_request.json").read_text()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()

    def call(self, mode, args=("-",)):
        Mock.mode, Mock.hits = mode, 0
        code, out, raw = run(list(args), self.env, self.request)
        self.assertNotIn(FAKE_TOKEN, raw, "token leaked into output")
        return code, out

    def test_ok(self):
        code, out = self.call("ok")
        self.assertEqual((code, out["action"]), (0, "journeys"))
        self.assertEqual(Mock.path, "/v2/plan")
        self.assertEqual(Mock.seen_token, FAKE_TOKEN)
        self.assertIs(out["live_check_needed"], True)

    def test_request_from_file(self):
        code, _ = self.call("ok", args=[str(ASSETS / "sample_request.json")])
        self.assertEqual(code, 0)

    def test_no_transit(self):
        self.assertEqual(self.call("no_transit")[1]["action"], "web_search_fallback")

    def test_address_not_found(self):
        self.assertEqual(self.call("error")[1]["reason"], "ADDRESS_NOT_FOUND")

    def test_400(self):
        code, out = self.call("400")
        self.assertEqual((code, out["action"]), (2, "fix_input"))
        self.assertEqual(Mock.hits, 1, "400 must not be retried")

    def test_401(self):
        code, out = self.call("401")
        self.assertEqual((code, out["action"]), (2, "fix_input"))
        self.assertEqual(Mock.hits, 1)

    def test_429_retries_once_then_falls_back(self):
        code, out = self.call("429")
        self.assertEqual((code, out["action"], out.get("reason")), (3, "web_search_fallback", "RATE_LIMITED"))
        self.assertEqual(Mock.hits, 2)

    def test_500(self):
        code, out = self.call("500")
        self.assertEqual((code, out["action"]), (3, "web_search_fallback"))
        self.assertEqual(Mock.hits, 2)
        self.assertIs(out["live_check_needed"], True)

    def test_malformed_json(self):
        self.assertEqual(self.call("malformed")[0], 3)

    def test_short_trip(self):
        code, out = self.call("short_trip")
        self.assertEqual((code, out["action"]), (3, "web_search_fallback"))
        self.assertIn("options", out["message"])

    def test_ok_without_journeys(self):
        code, out = self.call("no_journeys")
        self.assertEqual((code, out["action"]), (3, "web_search_fallback"))

    def test_all_late_is_passed_through(self):
        code, out = self.call("all_late")
        self.assertEqual(code, 0)
        self.assertTrue(all("LATE" in line for line in out["options"]))
        self.assertFalse(any(j["on_time"] for j in out["data"]["journeys"]))

    def test_past_leave_by_moved_to_leave_now(self):
        code, out = self.call("past_leave_by")
        self.assertEqual(code, 0)
        by_mode = {j["mode"]: j for j in out["data"]["journeys"]}
        walk, bike = by_mode["WALK"], by_mode["BICYCLE"]
        self.assertEqual(walk["leave_by"], "2026-10-26T08:41:00-07:00")  # rounded up from 8:40:30
        self.assertEqual(walk["arrive_at"], "2026-10-26T09:35:00-07:00")  # 54 min walk from now
        self.assertIs(walk["on_time"], False)
        self.assertEqual((bike["leave_by"], bike["arrive_at"], bike["on_time"]),
                         ("2026-10-26T08:41:00-07:00", "2026-10-26T08:54:00-07:00", True))
        self.assertTrue(walk["leave_by_adjusted"] and bike["leave_by_adjusted"])
        for j in out["data"]["journeys"]:
            if j["mode"] == "TRANSIT":  # a bus is never moved: leaving later would miss it
                self.assertNotIn("leave_by_adjusted", j)
        self.assertIn("walk: leave 08:41, arrive 09:35 (LATE)", out["options"])

    def test_v1_request_still_works(self):
        Mock.mode, Mock.hits = "v1_ok", 0
        body = json.loads(self.request)
        body.pop("modes")
        code, out, raw = run(["-"], self.env, json.dumps(body))
        self.assertEqual((code, out["action"], Mock.path), (0, "send_alert", "/v1/plan"))
        self.assertNotIn(FAKE_TOKEN, raw)

    def test_bad_json_input(self):
        Mock.hits = 0
        code, out, _ = run(["-"], self.env, "{oops")
        self.assertEqual((code, out["action"], Mock.hits), (2, "fix_input", 0))

    def test_non_object_input(self):
        code, out, _ = run(["-"], self.env, "[1, 2]")
        self.assertEqual((code, out["action"]), (2, "fix_input"))


class Transport(unittest.TestCase):
    def test_connection_refused(self):
        s = socket.socket()
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
        s.close()
        code, out, raw = run(["-"], {"NEVER_LATE_URL": f"http://127.0.0.1:{port}", "NEVER_LATE_TOKEN": FAKE_TOKEN},
                             (ASSETS / "sample_request.json").read_text())
        self.assertEqual((code, out["action"]), (3, "web_search_fallback"))
        self.assertNotIn(FAKE_TOKEN, raw)

    def test_plain_http_refused(self):
        for url in ("http://example.com", "http://localhost.evil.com", "ftp://x"):
            code, out, _ = run(["-"], {"NEVER_LATE_URL": url, "NEVER_LATE_TOKEN": FAKE_TOKEN}, "{}")
            self.assertEqual((code, out["action"]), (2, "fix_input"), url)

    def test_usage(self):
        code, out, _ = run([])
        self.assertEqual((code, out["action"]), (2, "fix_input"))


@unittest.skipUnless(os.environ.get("LIVE") == "1" and os.environ.get("NEVER_LATE_TOKEN"), "set LIVE=1 and NEVER_LATE_TOKEN")
class Live(unittest.TestCase):
    def test_live_end_to_end(self):
        token = os.environ["NEVER_LATE_TOKEN"]
        body = json.loads((ASSETS / "sample_request.json").read_text())
        today = datetime.now(timezone(timedelta(hours=-7))).date()  # Phoenix, no daylight saving time
        monday = today + timedelta(days=(0 - today.weekday()) % 7 or 7)  # within the backend's 7-day window
        body["arrive_by"] = f"{monday.isoformat()}T09:00:00-07:00"
        code, out, raw = run(["-"], {"NEVER_LATE_TOKEN": token}, json.dumps(body))
        self.assertNotIn(token, raw)
        self.assertIn(out["action"], ("journeys", "web_search_fallback"))
        self.assertIsNotNone(out.get("data"), "no backend response")
        self.assertIn("live_check_needed", out)


if __name__ == "__main__":
    unittest.main()
