# jellyrpc

Discord Rich Presence for Linux — window detection and idle state, with automatic handoff to [mprisence](https://github.com/lazykern/mprisence) when media is playing.

## How it works

Two daemons run side by side:

- **mprisence** — handles Jellyfin, music, and any MPRIS media player automatically. Install it separately.
- **jellyrpc** — handles everything else: shows what app you're in (terminal, browser, editor, Steam…) and goes idle after 5 minutes of inactivity. Steps back silently whenever mprisence has something to show.

```
Discord ← pypresence IPC ← jellyrpc.py
                               ├── is mprisence playing? → clear (stay silent)
                               ├── idle > 5 min?         → "Away from keyboard"
                               └── pgrep APP_MAP         → show app activity
```

App detection uses `pgrep` in priority order — terminal beats browser, editor beats terminal. Edit `APP_MAP` in `jellyrpc.py` to add or reorder apps.

## Install

```bash
git clone https://github.com/tiiow-fedora/jellyrpc
cd jellyrpc
bash install.sh
```

Then fill in your config:

```bash
nano ~/.config/jellyrpc/config.json
```
(dont forget to restart it with systemctl --user restart jellyrpc)
```json
{
  "discord_app_id":   "YOUR_DISCORD_APP_ID",
  "idle_detection":   true,
  "window_detection": true
}
```

### Getting a Discord App ID

1. Go to [discord.com/developers/applications](https://discord.com/developers/applications)
2. New Application → name it whatever you want shown in Discord (e.g. "Linux")
3. Copy the Application ID from the General Information page
   
### Uploading Rich Presence Art Assets

jellyrpc uses named image keys for each activity. You must upload the icons manually in your browser — this cannot be automated.

The icon files are in the `assets/` folder of this repo.

**Steps:**

1. Go to [discord.com/developers/applications](https://discord.com/developers/applications) and open your application
2. Click **Rich Presence** → **Art Assets** in the left sidebar
3. Upload each PNG from `assets/` with the exact key name listed below

| File | Key name (must match exactly) |
|------|-------------------------------|
| `firefox.png` | `firefox` |
| `terminal.png` | `terminal` |
| `coding.png` | `coding` |
| `steam.png` | `steam` |
| `jellyfin.png` | `jellyfin` |
| `idle.png` | `idle` |
| `music.png` | `music` |
| `watching.png` | `watching` |

The key names must match exactly — they map directly to the `large_image` values in `APP_MAP`.

### Dependencies

| Package | Purpose | Fedora |
|---------|---------|--------|
| `pypresence` | Discord IPC | `pip install pypresence --break-system-packages` |
| `playerctl` | Detect mprisence activity | `sudo dnf install playerctl` |
| `xssstate` | Idle detection (primary) | `sudo dnf install xscreensaver` |
| `xprintidle` | Idle detection (fallback) | `sudo dnf install xprintidle` |

`install.sh` installs `pypresence` automatically. The rest are optional — jellyrpc gracefully skips features it can't use.

## Config

`~/.config/jellyrpc/config.json`:

| Key | Default | Description |
|-----|---------|-------------|
| `discord_app_id` | `""` | **Required.** Your Discord application ID. |
| `idle_detection` | `true` | Show "Away from keyboard" after 5 min idle. |
| `window_detection` | `true` | Show current app activity. |

## Adding apps

Edit `APP_MAP` in `daemon/jellyrpc.py`:

```python
("zed",    "Coding",   "Zed",   "coding"),
("steam",  "On Steam", "Steam", "steam"),
```

Fields: `(pgrep name, details line, state line, large_image key)`. Priority order — put higher-priority entries first.

## Logs

```bash
journalctl --user -fu jellyrpc
```

## Update

```bash
git pull
bash install.sh
systemctl --user restart jellyrpc
```

## Uninstall

```bash
systemctl --user disable --now jellyrpc
rm ~/.local/bin/jellyrpc.py
rm ~/.config/systemd/user/jellyrpc.service
```
