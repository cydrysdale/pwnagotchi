# Onscreen Menu (Waveshare 1.3" LCD HAT) for Pwnagotchi

On-device menu for the ST7789 LCD HAT with buttons.

**Controls**
- **UP/DOWN** navigate
- **RIGHT / KEY1** select / confirm
- **LEFT / KEY2** back / exit
- **KEY3** toggle menu open/close
- Joystick press is ignored (prevents accidental nav)

**Features**
- Status (uptime, service state, IP)
- Restart Pwnagotchi service (unit auto-detected)
- Toggle `personality.deauth` in `/etc/pwnagotchi/config.toml` (service auto-restarts)
- Reboot / Shutdown
- View events (last ~40 from journal/syslog)
- Saved nets (last ~10 from JSON/handshake dirs or logs)
- Upload logs (tar.gz; optional `rclone` upload)
- PiSugar3 battery via `pisugar-server` (optional)

> Designed/tested with Jayofelony’s **pwnagotchi-noai** build (`lcdhat` driver for the Waveshare 1.3" ST7789). Backlight is BCM 24; not bound here.

---

## Install — Git clone
```bash
# On the Pi
sudo mkdir -p /usr/local/share/pwnagotchi/custom-plugins # If it doesn't exist already
cd /usr/local/share/pwnagotchi/custom-plugins
sudo git clone https://github.com/cydrysdale/pwnagotchi.git pwnagotchi-repo
sudo cp -r pwnagotchi-repo/plugins/onscreen_menu ./onscreen_menu
sudo bash ./onscreen_menu/install.sh
