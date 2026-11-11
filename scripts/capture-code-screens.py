#!/usr/bin/env python3
"""Capture the RoomKit Code screenshots shown on /code/.

Drives the real roomkit-code binary in a pseudo-terminal against a demo project
with a failing test. The tools really run: the files, the diff and the test
output are real. Only the model is scripted, by a local Chat Completions server,
so no account, key or network is needed. HOME and the state directory are
throwaway, so no local profile or conversation can reach a capture.

    uv run --no-project --with pyte --with playwright python \
        scripts/capture-code-screens.py ../roomkit-code/target/release/roomkit-code code/screenshots

CAPTURE_DEBUG=<dir> also writes each screen as text and the first model request
there; CAPTURE_TMP=<dir> holds the throwaway project and state.

Screens are rendered from the emulator with DejaVu Sans Mono, as roomkit-tui's
own scripts/screenshot.py does, then photographed with the system Chrome. Block
characters are drawn as solid cells, as a terminal draws them.
"""

import errno
import fcntl
import html
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import pty
import re
import select
import shutil
import struct
import subprocess
import sys
import tempfile
import termios
import threading
import time

import pyte
from playwright.sync_api import sync_playwright

COLS, ROWS = 132, 34
CHROME = "/usr/bin/google-chrome"
MODEL = "scripted-demo"
SESSION = "invoice-rounding"
# The project really lives in a throwaway directory. The header shows what a
# person would see for their own project instead of that long temporary path.
SHOWN_WORKSPACE = f"~/invoices-app · {SESSION}"

TOTALS = '''\"\"\"Invoice totals.\"\"\"

from decimal import ROUND_HALF_UP, Decimal


def to_cents(amount):
    return round(amount, 2)


def invoice_total(lines, tax_rate):
    subtotal = sum(line["quantity"] * line["unit_price"] for line in lines)
    return to_cents(subtotal * (1 + tax_rate))
'''

TEST = '''import unittest

from invoices.totals import invoice_total


class InvoiceTotal(unittest.TestCase):
    def test_rounds_half_cents_up(self):
        lines = [{"quantity": 1, "unit_price": 1.005}]
        self.assertEqual(invoice_total(lines, 0), 1.01)


if __name__ == "__main__":
    unittest.main()
'''

PLAN_STEPS = [
    {"step_id": "rounding", "description": "Round half cents up with Decimal", "status": "pending"},
    {"step_id": "tests", "description": "Run the test suite", "status": "pending"},
]
TEST_COMMAND = "python3 -m unittest discover -s tests -t . 2>&1"


def call(name, intent=None, **arguments):
    # Only some tools ask the model for a public intent (shell, processes,
    # delegation, MCP); the others are described from their arguments.
    if intent is not None:
        arguments = {"_roomkit_intent": intent, **arguments}
    return {"name": name, "arguments": arguments}


def complete_plan(body):
    # The plan's identifier and revision come from the plan tool's own result.
    results = "\n".join(
        str(message.get("content")) for message in body["messages"] if message["role"] == "tool"
    )
    plan_id = re.findall(r'"plan_id"\s*:\s*"([^"]+)"', results)[-1]
    revision = int(re.findall(r'"revision"\s*:\s*(\d+)', results)[-1])
    steps = [{**step, "status": "completed"} for step in PLAN_STEPS]
    return call("plan_update", plan_id=plan_id, expected_revision=revision, steps=steps)


REVIEW_TASK = ("Review the change to to_cents in invoices/totals.py: does it round half "
               "cents up for every amount, refunds included?")

# One entry per model request of the Code agent, in order: text to stream,
# then tool calls.
SCRIPT = [
    ("I'll start with the failing test and the code it covers.",
     [call("read", path="tests/test_totals.py"),
      call("read", path="invoices/totals.py")]),
    ("`round()` works on binary floats, so 1.005 is stored just below the half "
     "cent and rounds down. I'll save a plan for the fix.",
     [call("plan_create",
           title="Fix invoice rounding",
           objective="Invoice totals round half cents up, as the test expects.",
           steps=PLAN_STEPS)]),
    ("The plan is saved. Nothing has changed yet: switch to Ask and I'll apply it.", []),
    ("Applying the plan.",
     [call("edit", path="invoices/totals.py",
           old_text="    return round(amount, 2)",
           new_text='    return float(Decimal(str(amount)).quantize(Decimal("0.01"), ROUND_HALF_UP))')]),
    ("Now the test suite.",
     [call("shell", "Run the test suite", command=TEST_COMMAND)]),
    ("All green. I'll close the plan.", [complete_plan]),
    ("The test passes. `to_cents` now rounds half up with `Decimal`, so 1.005 gives "
     "1.01. Only `invoices/totals.py` changed.", []),
    ("I'll hand the review to the Review agent.",
     [call("delegate_task", "Ask Review to check the rounding change", agent="review",
           task=REVIEW_TASK, context={"files": ["invoices/totals.py", "tests/test_totals.py"]})]),
    ("Review is reading the change. I'll pass on what it finds.", []),
    ("Review agrees with the fix: 1.005 and 2.675 now round up. It notes that a "
     "refund of -1.005 gives -1.01, away from zero. Should I add a test for refunds?", []),
]

# The Review agent's requests, in its own conversation.
REVIEW_SCRIPT = [
    ("Reading the change and where it is used.",
     [call("read", path="invoices/totals.py"),
      call("grep", pattern="to_cents", path=".")]),
    ("The change is right. `Decimal(str(amount))` keeps 1.005 and 2.675 exact, and "
     "`ROUND_HALF_UP` rounds them up. A refund of -1.005 gives -1.01: half cents "
     "round away from zero. No test covers refunds yet.", []),
]

REVIEW_AGENT = {
    "id": "review", "label": "Review",
    "instructions": "Review changes. Read, never edit.",
    "tools": ["code_outline", "list", "glob", "grep", "read", "diff"],
}


class Model(BaseHTTPRequestHandler):
    """Streams the script as OpenAI-compatible chat completion chunks."""

    requests = []
    review_requests = []
    lock = threading.Lock()

    def log_message(self, *args):
        pass

    @classmethod
    def next_reply(cls, body):
        # The Review agent works in a conversation of its own, opened by the task.
        first_user = next(
            (str(m.get("content")) for m in body["messages"] if m["role"] == "user"), "")
        with cls.lock:
            if REVIEW_TASK in first_user:
                cls.review_requests.append(body)
                tag, index, script = "review", len(cls.review_requests) - 1, REVIEW_SCRIPT
            else:
                cls.requests.append(body)
                tag, index, script = "code", len(cls.requests) - 1, SCRIPT
        return f"{tag}-{index}", index, script[min(index, len(script) - 1)]

    def send_chunk(self, payload):
        self.wfile.write(b"data: " + json.dumps(payload).encode() + b"\n\n")
        self.wfile.flush()

    def delta(self, delta, finish=None):
        self.send_chunk({"choices": [{"index": 0, "delta": delta, "finish_reason": finish}]})

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        call_id, index, (text, calls) = Model.next_reply(body)
        calls = [tool(body) if callable(tool) else tool for tool in calls]
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.end_headers()
        for word in text.split(" "):
            self.delta({"content": word + " "})
            time.sleep(0.05)
        for position, tool in enumerate(calls):
            self.delta({"tool_calls": [{
                "index": position, "id": f"call-{call_id}-{position}", "type": "function",
                "function": {"name": tool["name"], "arguments": json.dumps(tool["arguments"])},
            }]})
        self.delta({}, "tool_calls" if calls else "stop")
        self.send_chunk({"choices": [], "usage": {
            "prompt_tokens": 15412 + 1317 * index, "completion_tokens": 96 + 43 * index,
        }})
        self.wfile.write(b"data: [DONE]\n\n")
        self.wfile.flush()


def make_project(root):
    project = root / "invoices-app"
    (project / "invoices").mkdir(parents=True)
    (project / "tests").mkdir()
    (project / "invoices" / "__init__.py").write_text("")
    (project / "tests" / "__init__.py").write_text("")
    (project / "invoices" / "totals.py").write_text(TOTALS)
    (project / "tests" / "test_totals.py").write_text(TEST)
    (project / ".gitignore").write_text("__pycache__/\n")
    return project


class Terminal:
    """The application in a pseudo-terminal, read through a terminal emulator."""

    def __init__(self, command, env):
        self.screen = pyte.Screen(COLS, ROWS)
        self.stream = pyte.ByteStream(self.screen)
        self.master, slave = pty.openpty()
        fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack("HHHH", ROWS, COLS, 0, 0))
        self.process = subprocess.Popen(
            command, stdin=slave, stdout=slave, stderr=slave, env=env, start_new_session=True,
        )
        os.close(slave)

    def pump(self, seconds):
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            ready, _, _ = select.select([self.master], [], [], 0.05)
            if not ready:
                continue
            try:
                self.stream.feed(os.read(self.master, 65536))
            except OSError as error:
                if error.errno == errno.EIO:
                    return
                raise

    def text(self):
        return "\n".join(self.screen.display)

    def wait_for(self, marker, timeout=20):
        deadline = time.monotonic() + timeout
        while marker not in self.text():
            if time.monotonic() >= deadline:
                raise RuntimeError(f"missing {marker!r} on screen:\n{self.text()}")
            self.pump(0.1)
        self.pump(0.6)

    def send(self, data, settle=0.4):
        os.write(self.master, data)
        self.pump(settle)

    def say(self, message):
        self.send(message.encode(), 0.3)
        self.send(b"\r", 0.2)

    def close(self):
        self.send(b"\x04", 0.3)
        self.send(b"\x04", 0.3)
        try:
            self.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.process.kill()


COLORS = {
    "black": "000000", "red": "cd3131", "green": "0dbc79", "brown": "e5e510",
    "blue": "2472c8", "magenta": "bc3fbc", "cyan": "11a8cd", "white": "e5e5e5",
    "brightblack": "666666", "brightred": "f14c4c", "brightgreen": "23d18b",
    "brightbrown": "f5f543", "brightblue": "3b8eea", "brightmagenta": "d670d6",
    "brightcyan": "29b8db", "brightwhite": "ffffff",
}
DEFAULT_FG, DEFAULT_BG = "d4d4d8", "16161e"


def color(value, fallback):
    if value == "default":
        return fallback
    return COLORS.get(value) or (value if len(value) == 6 else fallback)


# Block characters by the quarters of the cell they fill: upper left, upper
# right, lower left, lower right. A terminal draws them to fill the whole cell;
# a font's glyphs leave gaps between rows, so they are drawn here as shapes.
QUADRANTS = {
    "█": "1111", "▀": "1100", "▄": "0011", "▌": "1010", "▐": "0101",
    "▖": "0010", "▗": "0001", "▘": "1000", "▝": "0100", "▙": "1011",
    "▚": "1001", "▛": "1110", "▜": "1101", "▞": "0110", "▟": "0111",
}
QUADRANT_PLACES = ((0, 0), (1, 0), (0, 1), (1, 1))  # (column, line) halves
# A whole number of pixels per cell, and the font size whose advance matches
# it, so that cell edges and half cells fall on device pixels.
CELL, ROW_HEIGHT = 9, 18


def quadrant_html(x, char, fg, bg):
    # Solid rectangles, one per filled quarter, on the cell's background.
    half_width, half_height = CELL / 2, ROW_HEIGHT / 2
    parts = [f'<span style="left:{x * CELL}px;width:{CELL}px;background:#{bg}"></span>']
    for (column, line), filled in zip(QUADRANT_PLACES, QUADRANTS[char]):
        if filled == "1":
            parts.append(
                f'<span style="left:{x * CELL + column * half_width}px;top:{line * half_height}px;'
                f'width:{half_width}px;height:{half_height}px;background:#{fg}"></span>')
    return "".join(parts)


def row_html(screen, y):
    # Each run of same-styled cells sits at its own column, CELL pixels wide
    # per cell, so a glyph advance a fraction off never shifts what follows.
    line = screen.buffer[y]
    parts, run = [], None  # run: [first column, cells, style, characters]

    def flush():
        if run is None:
            return
        first, cells, (fg, bg, bold, underline), chars = run
        css = f"left:{first * CELL}px;width:{cells * CELL}px;color:#{fg};background:#{bg}"
        if bold:
            css += ";font-weight:700"
        if underline:
            css += ";text-decoration:underline"
        parts.append(f'<span style="{css}">{html.escape("".join(chars))}</span>')

    for x in range(COLS):
        cell = line[x]
        if cell.data == "":
            if run is not None:
                run[1] += 1  # Second cell of a wide character.
            continue
        fg, bg = color(cell.fg, DEFAULT_FG), color(cell.bg, DEFAULT_BG)
        if cell.reverse:
            fg, bg = bg, fg
        if cell.data in QUADRANTS:
            flush()
            run = None
            parts.append(quadrant_html(x, cell.data, fg, bg))
            continue
        style = (fg, bg, cell.bold, cell.underscore)
        if run is None or style != run[2]:
            flush()
            run = [x, 0, style, []]
        run[1] += 1
        run[3].append(cell.data)
    flush()
    return f'<div class="row">{"".join(parts)}</div>'


def show_clean_workspace(screen, project):
    prefix = str(project)[:16]
    for y in range(ROWS):
        text = "".join(screen.buffer[y][x].data for x in range(COLS))
        start = text.find(prefix)
        if start < 0:
            continue
        end = text.index("│", start) if "│" in text[start:] else COLS
        style = screen.buffer[y][start]
        for x in range(start, end):
            position = x - start
            data = SHOWN_WORKSPACE[position] if position < len(SHOWN_WORKSPACE) else " "
            screen.buffer[y][x] = style._replace(data=data)


def screen_html(screen):
    rows = "".join(row_html(screen, y) for y in range(ROWS))
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
html,body{{margin:0;background:#0f172a}}
.window{{display:inline-block;background:#{DEFAULT_BG}}}
.bar{{height:30px;background:#20202a;display:flex;align-items:center;padding:0 12px;gap:8px}}
.dot{{width:12px;height:12px;border-radius:50%}}
.screen{{padding:10px 14px 14px;font:14.949px/18px 'DejaVu Sans Mono',monospace;white-space:pre}}
.row{{position:relative;width:{COLS * CELL}px;height:18px}}
.row span{{position:absolute;top:0;height:18px}}
</style></head><body><div class="window">
<div class="bar"><span class="dot" style="background:#ff5f57"></span>
<span class="dot" style="background:#febc2e"></span>
<span class="dot" style="background:#28c840"></span></div>
<div class="screen">{rows}</div></div></body></html>"""


def scenario(terminal, shoot):
    terminal.wait_for("Plan", 20)
    terminal.pump(1)
    shoot("welcome")

    terminal.say("/tools")
    terminal.wait_for("code_outline", 10)
    shoot("tools")
    terminal.send(b"\x1b", 0.8)

    terminal.say("The invoice test fails. Find out why and plan the fix.")
    terminal.wait_for("switch to Ask", 30)
    shoot("plan")

    # Shift+Tab goes from Plan to Yolo, then to Ask.
    terminal.send(b"\x1b[Z", 0.6)
    terminal.send(b"\x1b[Z", 0.6)
    terminal.wait_for("[Ask]", 5)
    terminal.say("Apply the plan.")
    terminal.wait_for("Ctrl+Y", 30)
    shoot("approval")

    terminal.send(b"\x19", 0.5)
    terminal.wait_for("Ctrl+Y", 30)
    terminal.send(b"\x19", 0.5)
    terminal.wait_for("Execution Completed", 30)
    shoot("done")

    terminal.say("Ask Review to look over the change.")
    terminal.wait_for("add a test for refunds", 60)
    shoot("delegate")


def add_review_agent(state):
    # A project's agents live in its own file; the Review agent copies the
    # connection and model of the Code agent the first launch created.
    (path,) = state.glob("projects/*/agents.json")
    profiles = json.loads(path.read_text())
    code = profiles["agents"]["code"]
    profiles["agents"]["review"] = {**code, **REVIEW_AGENT, "skills": [], "mcp": {}}
    path.write_text(json.dumps(profiles, indent=2))


def main():
    binary, out_dir = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    # The screens as text and the first model request, to check a capture,
    # go elsewhere than the published images, and only when asked.
    debug_dir = os.environ.get("CAPTURE_DEBUG")
    if debug_dir:
        debug_dir = Path(debug_dir).resolve()
        debug_dir.mkdir(parents=True, exist_ok=True)
    root = Path(tempfile.mkdtemp(prefix="roomkit-code-capture-", dir=os.environ.get("CAPTURE_TMP")))
    server = ThreadingHTTPServer(("127.0.0.1", 0), Model)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    home = root / "home"
    home.mkdir()
    project = make_project(home)
    env = {
        "HOME": str(home), "PATH": os.environ["PATH"], "LANG": "C.UTF-8",
        "TERM": "xterm-256color", "COLORTERM": "truecolor",
        "ROOMKIT_NO_UPDATE_CHECK": "true",
    }
    command = [
        str(binary), str(project), "--state-dir", str(root / "state"),
        "--base-url", f"http://127.0.0.1:{server.server_port}/v1", "--model", MODEL,
        "--mode", "plan", "--session", SESSION, "--context-window", "200000",
        "--no-animations", "--no-terminal-status", "--no-herdr",
        "--color", "always", "--theme", "dark",
    ]
    first = Terminal(command, env)
    first.wait_for("Plan", 20)
    first.close()
    add_review_agent(root / "state")
    terminal = Terminal(command, env)
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(executable_path=CHROME)
            page = browser.new_context(
                viewport={"width": 1300, "height": 800}, device_scale_factor=2,
            ).new_page()

            def shoot(name):
                show_clean_workspace(terminal.screen, project)
                if debug_dir:
                    (debug_dir / f"{name}.txt").write_text(terminal.text())
                page.set_content(screen_html(terminal.screen))
                page.locator(".window").screenshot(path=str(out_dir / f"{name}.png"))
                print("captured", name)

            scenario(terminal, shoot)
            browser.close()
        print("model requests:", len(Model.requests), "+ review:", len(Model.review_requests))
    finally:
        if debug_dir and Model.requests:
            (debug_dir / "first-request.json").write_text(json.dumps(Model.requests[0], indent=1))
        terminal.close()
        server.shutdown()
        shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    main()
