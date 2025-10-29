# onscreen_menu.py
# On-device menu for Pwnagotchi on Waveshare 1.3" LCD HAT (ST7789).
# Controls (per user request):
#   UP/DOWN .......... navigate
#   RIGHT or KEY1 .... Select / Confirm
#   LEFT  or KEY2 .... Back / Exit
#   KEY3 ............. Toggle menu open/close
#   Joystick press ... Unused (prevents accidental nav while pressing)
#
# Features:
#   - Status (uptime/service/IP)
#   - Restart pwnagotchi service
#   - Toggle deauth in /etc/pwnagotchi/config.toml (service auto-restarts)
#   - Reboot / Shutdown device
#   - View events (40)  [journalctl -u <pwnagotchi*> if available, fallback to generic journal/grep]
#   - Saved nets (10)   [pulls from common json/paths, fallback to journal/grep]
#   - Upload logs       [tar.gz; optional rclone upload to configured remote]
#
# Notes:
#   - Designed/tested against Jayofelony's "pwnagotchi-noai" build which ships the 'lcdhat' driver (ST7789 LCD_1inch3).
#   - Backlight is BCM 24 in that driver; we do NOT bind it here.

import time
import threading
import json
import urllib.request
import subprocess
import RPi.GPIO as GPIO
from PIL import Image, ImageDraw, ImageFont

__author__ = "you"
__version__ = "0.4.0"
__name__ = "onscreen_menu"
__description__ = "On-device menu for Pwnagotchi (service controls, logs, secured nets, tar+rclone, PiSugar3 battery)."

# --- GPIO (BCM) pins per Waveshare 1.3\" LCD HAT ---
PIN_UP    = 6
PIN_DOWN  = 19
PIN_LEFT  = 5     # Back / Exit (redundant with KEY2)
PIN_RIGHT = 26    # Select / Confirm (redundant with KEY1)
PIN_OK    = 13    # Joystick press (unused)
PIN_KEY1  = 21    # Select / Confirm
PIN_KEY2  = 20    # Back / Exit
PIN_KEY3  = 16    # Toggle menu open/close
# NOTE: Backlight is BCM 24; do NOT bind as a button here.

DEBOUNCE_S = 0.15

# Optional PiSugar3 API (if pisugar-server is installed)
PISUGAR_HOST = "127.0.0.1"
PISUGAR_PORT = 8421

class Plugin(object):
    def __init__(self):
        self.ready = False
        self.menu_open = False
        self.menu_items = [
            ("Status", self._act_status),
            ("Restart pwnagotchi", self._act_restart_service),
            ("Toggle deauth", self._act_toggle_deauth),
            ("Reboot device", self._act_reboot_pi),
            ("Shutdown device", self._act_shutdown_pi),
            ("—", None),
            ("View events (40)", self._act_show_events),
            ("Saved nets (10)", self._act_show_networks),
            ("Upload logs", self._act_upload_logs),
            ("PiSugar: battery", self._act_pisugar_status),
        ]
        self.menu_index = 0
        self.font = ImageFont.load_default()
        self.ui = None
        self._lock = threading.Lock()

        # config overridables (read from /etc/pwnagotchi/config.toml via _get_cfg)
        self.rclone_remote = None  # e.g., "gdrive:pwna-logs"

    # ---------- Pwnagotchi hooks ----------
    def on_loaded(self):
        GPIO.setmode(GPIO.BCM)
        for pin in (PIN_UP, PIN_DOWN, PIN_LEFT, PIN_RIGHT, PIN_OK, PIN_KEY1, PIN_KEY2, PIN_KEY3):
            try:
                GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            except Exception:
                pass
        # read config overrides if present
        self.rclone_remote = self._get_cfg("rclone_remote") or None
        self.ready = True

    def on_unloaded(self):
        try:
            GPIO.cleanup()
        except Exception:
            pass

    def on_ui_setup(self, ui):
        self.ui = ui

    def on_ready(self, agent):
        self.ui = agent.view

    def on_ui_update(self, ui):
        if not self.ready:
            return

        # Toggle menu with KEY3 (press & release)
        if self._edge(PIN_KEY3):
            with self._lock:
                self.menu_open = not self.menu_open

        if not self.menu_open:
            return

        # Navigation (UP/DOWN)
        if self._edge(PIN_UP):
            with self._lock:
                self.menu_index = (self.menu_index - 1) % len(self.menu_items)
        elif self._edge(PIN_DOWN):
            with self._lock:
                self.menu_index = (self.menu_index + 1) % len(self.menu_items)

        # Back/Exit: LEFT or KEY2
        elif self._edge(PIN_LEFT) or self._edge(PIN_KEY2):
            with self._lock:
                self.menu_open = False
                return

        # Select/Confirm: RIGHT or KEY1
        elif self._edge(PIN_RIGHT) or self._edge(PIN_KEY1):
            label, fn = self.menu_items[self.menu_index]
            if fn is not None:
                threading.Thread(target=self._run_action, args=(label, fn), daemon=True).start()

        # Draw overlay
        self._draw_menu(ui)

    # ---------- Input helpers ----------
    def _btn(self, pin):
        try:
            return GPIO.input(pin) == GPIO.LOW
        except Exception:
            return False

    def _edge(self, pin):
        if self._btn(pin):
            time.sleep(DEBOUNCE_S)
            while self._btn(pin):
                time.sleep(0.01)
            return True
        return False

    # ---------- Drawing ----------
    def _draw_menu(self, ui):
        w, h = ui.width(), ui.height()
        img = Image.new("RGB", (w, h), "black")
        d = ImageDraw.Draw(img)
        d.text((8, 8), "Pwnagotchi Menu", font=self.font, fill=(200, 255, 200))

        y = 32
        for i, (label, _) in enumerate(self.menu_items):
            prefix = "➤ " if i == self.menu_index else "  "
            d.text((8, y), prefix + label, font=self.font, fill=(255, 255, 255))
            y += 18

        hint = "UP/DN nav  RIGHT/KEY1 ok  LEFT/KEY2 back  KEY3 menu"
        d.text((8, h - 20), hint, font=self.font, fill=(160, 200, 160))
        ui.display_image(img)

    def _draw_msg(self, lines):
        w, h = self.ui.width(), self.ui.height()
        img = Image.new("RGB", (w, h), "black")
        d = ImageDraw.Draw(img)
        y = 8
        for line in lines:
            d.text((8, y), line, font=self.font, fill=(200, 255, 200))
            y += 18
        self.ui.display_image(img)

    # ---------- Shell helpers ----------
    def _sh(self, cmd):
        try:
            return subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, text=True)
        except subprocess.CalledProcessError as e:
            return e.output

    def _first_line(self, s):
        return (s or "").splitlines()[0] if s else ""

    def _detect_pwn_service(self):
        """
        Find the pwnagotchi systemd unit name dynamically.
        Returns (unit_name or None).
        """
        # typical unit includes 'pwnagotchi.service'
        out = self._sh("systemctl list-units --type=service --all | awk '{print $1}' | grep -i pwnagotchi | head -n1 || true").strip()
        return out if out else None

    def _journal_tail(self, n=200):
        """
        Pull ~n lines of relevant logs. Prefer unit-specific journal if we can detect it.
        Fall back to generic journal, then to /var/log/syslog if present.
        """
        unit = self._detect_pwn_service()
        if unit:
            raw = self._sh(f"journalctl -u {unit} -n {n} --no-pager 2>/dev/null || true")
            if raw.strip():
                return raw
        # generic journald tail
        raw = self._sh(f"journalctl -n {n} --no-pager 2>/dev/null || true")
        if raw.strip():
            return raw
        # rsyslog fallback (Raspberry Pi OS default sometimes)
        raw = self._sh("tail -n 300 /var/log/syslog 2>/dev/null || true")
        return raw or ""

    # ---------- Actions ----------
    def _run_action(self, label, fn):
        if not self.ui:
            return
        self._draw_msg([label + "..."])
        try:
            out = fn()
            if not out:
                out = "Done."
            lines = [label + ":", *out.splitlines()[:8], "", "RIGHT/KEY1=OK  LEFT/KEY2=Back"]
            self._draw_msg(lines)
            # Wait for either confirm or back to continue
            while True:
                if self._edge(PIN_RIGHT) or self._edge(PIN_KEY1) or self._edge(PIN_LEFT) or self._edge(PIN_KEY2):
                    break
                time.sleep(0.05)
        except Exception as e:
            self._draw_msg([label, "", f"Error: {e}", "", "RIGHT/KEY1=OK  LEFT/KEY2=Back"])
            while True:
                if self._edge(PIN_RIGHT) or self._edge(PIN_KEY1) or self._edge(PIN_LEFT) or self._edge(PIN_KEY2):
                    break
                time.sleep(0.05)

    def _act_status(self):
        up  = self._sh("uptime -p || true").strip()
        svc = self._first_line(self._sh("systemctl is-active pwnagotchi 2>/dev/null || true").strip())
        # if unit name is different, try detected name:
        if not svc or svc == "unknown":
            unit = self._detect_pwn_service()
            if unit:
                svc = self._first_line(self._sh(f"systemctl is-active {unit} || true").strip()) or "unknown"
        ip  = self._sh("hostname -I 2>/dev/null | awk '{print $1}' || true").strip()
        return f"uptime: {up}\nsvc: {svc}\nip: {ip}"

    def _act_restart_service(self):
        unit = self._detect_pwn_service() or "pwnagotchi"
        return self._sh(f"sudo systemctl restart {unit} && sleep 1 && systemctl is-active {unit} || true")

    def _act_reboot_pi(self):
        subprocess.Popen(["sudo", "reboot"])
        return "Rebooting…"

    def _act_shutdown_pi(self):
        subprocess.Popen(["sudo", "shutdown", "now"])
        return "Shutting down…"

    def _act_toggle_deauth(self):
        # Toggle personality.deauth true/false in /etc/pwnagotchi/config.toml
        path = "/etc/pwnagotchi/config.toml"
        cur = self._sh(f"grep -E '^ *personality\\.deauth' {path} || true").strip()
        if "true" in cur:
            self._sh(f"""sudo sed -i -E 's/^( *personality\\.deauth *= *).*/\\1false/' {path}""")
            new = "false"
        else:
            self._sh(f"""sudo sed -i -E 's/^( *personality\\.deauth *= *).*/\\1true/' {path} || echo 'personality.deauth = true' | sudo tee -a {path} >/dev/null""")
            new = "true"
        unit = self._detect_pwn_service() or "pwnagotchi"
        self._sh(f"sudo systemctl restart {unit} || true")
        return f"deauth -> {new}"

    # -------- logs & networks --------
    def _act_show_events(self):
        """Show last ~40 pwnagotchi-relevant lines, paginated."""
        raw = self._journal_tail(300)
        if not raw.strip():
            return "No logs found."
        # Prefer lines that mention pwnagotchi, handshake, WPA/WEP, errors, deauth, peers, etc.
        import re
        keep = []
        patterns = re.compile(r"(pwnagotchi|handshake|WPA|WEP|deauth|error|WARN|INFO|peer|epoch|session)", re.I)
        for line in raw.splitlines():
            if patterns.search(line):
                keep.append(line.strip())
        lines = keep if keep else [l.strip() for l in raw.splitlines() if l.strip()]
        last = lines[-40:] if len(lines) > 40 else lines

        # Page display (6 lines per page)
        chunks = [last[i:i+6] for i in range(0, len(last), 6)]
        for chunk in chunks:
            self._draw_msg(chunk + ["", "RIGHT/KEY1=next  LEFT/KEY2=back"])
            # wait for next or back
            while True:
                if self._edge(PIN_RIGHT) or self._edge(PIN_KEY1):
                    break
                if self._edge(PIN_LEFT) or self._edge(PIN_KEY2):
                    return ""
                time.sleep(0.05)
        return "End of events."

    def _act_show_networks(self):
        """Show last 10 unique 'secured' networks detected."""
        # heuristic paths used across community builds
        candidates = [
            "/root/.pwnagotchi/known_networks.json",
            "/root/.pwnagotchi/networks.json",
            "/root/.pwnagotchi/seen_networks.json",
            "/home/pi/.pwnagotchi/known_networks.json",
            "/root/handshakes",
            "/home/pi/handshakes",
        ]
        found = []
        import glob, os, re
        # JSON sources
        for c in candidates:
            for p in glob.glob(c):
                if os.path.isdir(p):
                    continue
                try:
                    txt = open(p, "r", errors="ignore").read()
                except Exception:
                    continue
                try:
                    obj = json.loads(txt)
                    # pull ssids recursively
                    def gather(o, out):
                        if isinstance(o, dict):
                            for k,v in o.items():
                                if isinstance(v, (dict,list)):
                                    gather(v, out)
                                else:
                                    if "ssid" in k.lower() and isinstance(v,str) and v.strip():
                                        out.append(v.strip())
                        elif isinstance(o, list):
                            for e in o:
                                gather(e, out)
                    tmp = []
                    gather(obj, tmp)
                    if tmp:
                        found.extend(tmp)
                except Exception:
                    pass
        # CAP/handshake file name hints
        for capdir in ["/root/handshakes", "/home/pi/handshakes"]:
            if not os.path.isdir(capdir):
                continue
            for f in sorted(glob.glob(os.path.join(capdir, "*")))[-50:]:
                # try to pull SSID-ish substrings from filenames
                base = os.path.basename(f)
                ssid = re.sub(r"\.(pcap|pcapng|cap|hccapx)$", "", base, flags=re.I)
                ssid = ssid.replace("_", " ").strip()
                if ssid:
                    found.append(ssid)

        # Fallback: grep journal/syslog for SSID markers
        if not found:
            raw = self._journal_tail(500)
            raw += "\n" + self._sh("grep -h -E 'SSID|WPA|WEP|handshake|secured|handshakes' /var/log/* 2>/dev/null || true")
            ss = re.findall(r"SSID[:= ]*\"?([^\"]{1,32})\"?", raw, flags=re.I)
            found += [s.strip() for s in ss if s.strip()]

        # Deduplicate preserving newest last-seen order
        seen = []
        for s in reversed(found):
            if s and s not in seen:
                seen.append(s)
        newest = list(reversed(seen))[:10]
        if not newest:
            return "No secured networks found."

        for ssid in newest:
            self._draw_msg([f"SSID: {ssid}", "", "RIGHT/KEY1=next  LEFT/KEY2=back"])
            while True:
                if self._edge(PIN_RIGHT) or self._edge(PIN_KEY1):
                    break
                if self._edge(PIN_LEFT) or self._edge(PIN_KEY2):
                    return ""
                time.sleep(0.05)
        return "End of networks."

    def _act_upload_logs(self):
        """Create tarball of pwnagotchi logs; upload via rclone if configured."""
        files = [
            "/etc/pwnagotchi/config.toml",
            "/root/.pwnagotchi/state.json",
            "/var/log/pwnagotchi.log",
            "/var/log/syslog",
        ]
        import glob, os
        existing = []
        for f in files:
            existing.extend(glob.glob(f))
        existing = [e for e in existing if os.path.exists(e)]

        if not existing:
            return "No known logs found."

        ts = int(time.time())
        tarball = f"/tmp/pwnalog-{ts}.tar.gz"
        cmd = "tar -czf {} {}".format(tarball, " ".join("'{}'".format(e) for e in existing))
        self._draw_msg(["Packaging logs...", "", tarball])
        _ = self._sh(cmd)

        if self.rclone_remote:
            r = self._sh("which rclone || true").strip()
            if not r:
                return f"rclone not installed. Tarball created: {tarball}"
            self._draw_msg([f"Uploading to {self.rclone_remote} ..."])
            upout = self._sh(f"rclone copy {tarball} {self.rclone_remote} --progress")
            return f"Uploaded: {self.rclone_remote}"
        return f"Tarball created: {tarball}"

    # ---------- PiSugar ----------
    def _act_pisugar_status(self):
        url = f"http://{PISUGAR_HOST}:{PISUGAR_PORT}/getBattery"
        try:
            with urllib.request.urlopen(url, timeout=0.8) as r:
                data = json.loads(r.read().decode("utf-8"))
            pct = data.get("percentage")
            volt = data.get("voltage")
            chg = data.get("isCharging")
            return f"PiSugar:\n{pct}%  {volt}V\ncharging: {chg}"
        except Exception:
            return "PiSugar server not found."

    # ---------- Config reader ----------
    def _get_cfg(self, key):
        """
        Very small INI-ish/TOML-ish getter for our plugin block in /etc/pwnagotchi/config.toml
        Only handles simple 'key = "value"' under [main.plugins.onscreen_menu]
        """
        path = "/etc/pwnagotchi/config.toml"
        try:
            txt = open(path, "r", errors="ignore").read()
        except Exception:
            return None
        # crude parse: find plugin block, then key =
        import re
        m = re.search(r"(?ms)^\s*\[main\.plugins\.onscreen_menu\]\s*(.*?)^\s*\[", txt + "\n[END]", re.M)
        block = m.group(1) if m else ""
        km = re.search(rf"^\s*{re.escape(key)}\s*=\s*\"([^\"]*)\"", block, re.M)
        if km:
            return km.group(1).strip()
        km2 = re.search(rf"^\s*{re.escape(key)}\s*=\s*([^\s#]+)", block, re.M)
        if km2:
            return km2.group(1).strip()
        return None
