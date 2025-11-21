# Pwnagotchi Custom Plugins

Custom plugins for [Pwnagotchi](https://github.com/evilsocket/pwnagotchi).

## Plugins

### Onscreen Menu (Waveshare 1.3" LCD HAT)

On-device menu for the ST7789 LCD HAT with button controls.

**Features:**
- Status display (uptime, service state, IP)
- Restart Pwnagotchi service
- Toggle deauth in config (with audit logging)
- Reboot / Shutdown
- View events (last ~40 from journal/syslog)
- List saved networks/handshakes
- Upload logs (tar.gz with optional rclone)
- PiSugar3 battery status (optional)

**Controls:** UP/DOWN navigate, RIGHT/KEY1 select, LEFT/KEY2 back, KEY3 toggle menu

See [plugins/onscreen_menu/README.md](plugins/onscreen_menu/README.md) for installation and configuration.

## Requirements

- Raspberry Pi with Pwnagotchi installed
- Waveshare 1.3" LCD HAT (ST7789)
- Tested with Jayofelony's pwnagotchi-noai build

## License

MIT
