# FM4 Settings menu map

Open the source carousel with the encoder, select **Settings**, then turn to choose a section. Click opens/selects; hold goes back. Each submenu also has a Back entry. Saved preferences and learned remote keys survive updates.

```text
Settings
├── Now Playing
├── Display
│   ├── Display Mode
│   │   ├── Modern: Panel
│   │   ├── Modern: Panel Performance
│   │   ├── Modern: Cinema
│   │   ├── Panel / Needle VU
│   │   ├── Panel / Spectrum
│   │   └── Panel / Twin Needle VU
│   ├── HDMI Now Playing (Beta) — On / Off
│   ├── Brightness → Low / Medium / High
│   ├── Screen Rotation → Normal / Upside-down
│   └── Display Timeouts
│       ├── Pause to clock
│       ├── Clock dim after
│       └── Display off after
├── Audio
│   ├── Audio Output → detected audio devices
│   ├── Power-on Volume
│   ├── AirPlay → On / Off
│   ├── Bluetooth → Pair device (3 minutes) / Stop discovery
│   └── Playback
│       ├── Play Single
│       ├── Play All
│       ├── Repeat Single
│       ├── Repeat All
│       └── Shuffle
├── Remote
│   ├── Pair Apple Remote
│   └── Learn Remote
│       ├── Learn Up / Down / Left / Right
│       ├── Learn Select / Menu
│       ├── Learn Back / previous (context-sensitive)
│       ├── Learn Play / pause
│       ├── Learn Volume up / Volume down / Mute
│       ├── Learn Next track / Previous track
│       ├── Learn Stop
│       ├── Learn Repeat / shuffle mode
│       ├── Learn Save track
│       ├── Learn Now Playing
│       ├── Learn Back (navigation)
│       ├── Cancel learning
│       └── Restore Apple defaults
├── Streaming Services
│   ├── BBC Sounds
│   ├── TIDAL
│   ├── Beta Spotify
│   └── Beta Qobuz
│       Each service → Show in carousel / Hide from carousel / Account URL
├── Network & Services
│   ├── Network
│   │   ├── IP Address
│   │   ├── Wi-Fi Networks → choose network → enter password → join
│   │   └── Wi-Fi status / IP
│   └── Service URLs
│       ├── Sable configuration
│       ├── Web player
│       ├── FM4 Favorites page
│       ├── BBC Sounds
│       ├── TIDAL
│       └── Server settings
├── Library & Shortcuts
│   ├── Music Library
│   │   ├── Refresh now
│   │   └── Auto refresh → Off / Every 15 minutes / Every hour
│   ├── Shortcuts → Reset 5–7 Defaults
│   └── Add G's Mini Tidal List
├── System
│   ├── Storage
│   ├── Check / Apply Updates
│   │   └── Apply latest patches? → Cancel / Yes, apply patches
│   │       └── When complete → Later / Reboot now
│   └── Shutdown → Confirm Shutdown / Cancel
└── Back
```

Back entries inside submenus are omitted from the diagram for clarity.

## Streaming services and configuration page

Open `http://YOUR-IP/sable-config.html` for account links, the web player,
Favorites, Lyrion settings and piCorePlayer settings. Links follow the address
used to open the page. The OLED URL is under Network & Services → Service URLs.

Streaming Services controls carousel visibility without deleting accounts or
changing playback. BBC Sounds/TIDAL default to shown; Beta Spotify/Qobuz to hidden.
Spotify uses SpotOn and requires Premium; Qobuz needs a streaming subscription.
Both new services have loaded successfully but authenticated playback remains
untested. Spotify's shared-client profile request returned HTTP 429 in our test.
For remote Spotify sign-in, paste the full loopback redirect URL into SpotOn's
Manual authorisation field. Wait before retrying rate-limit errors.

## Numeric controls

Click **Power-on Volume** or a **Display Timeouts** entry to open its editor. Turn the knob to adjust, click to save, or hold to cancel. Cancelling leaves the saved value unchanged.

| Setting | Range | Step | Behaviour |
| --- | --- | --- | --- |
| Power-on Volume | Off, 0–100% | 1% | Applies at startup and on playback resume after an hour paused or stopped. Off is below 0%; 0% is silent. AirPlay/Bluetooth remain controlled by the sending device. |
| Pause to clock | Off, up to 2 hours | 30 seconds | Switches paused playback to the clock. Stopped playback already returns to the clock. |
| Clock dim after | Off, up to 2 hours | 30 seconds | Dims the idle display after the chosen delay. |
| Display off after | Off, up to 2 hours | 30 seconds | Turns the idle OLED off after the chosen delay. An interaction wakes it. |

Timeout zero means Off. Normal active playback stays awake. Display timeout editing stays open until saved or cancelled; ordinary menu navigation retains its inactivity return timer.

## Remote learning

Choose a Learn action, then press the desired key within 30 seconds. Relearning an action replaces its old key; assigning an already-used key gives it the new action. Dedicated Next/Previous work as track controls in any view. Arrows retain their context-sensitive navigation. Repeat/shuffle mode cycles the available playback modes. Restore Apple defaults clears custom learned mappings.

## Updates

The 10 October AirPlay handover update restores the local Squeezelite player
after receiver release, with stale PID detection, bounded startup retries and
Lyrion connection confirmation. Tested with AirPlay followed by TIDAL/BBC.
This fixes the local audio handover; HDMI AirPlay metadata is still separate work.

Use **Settings → System → Check / Apply Updates**. Older builds have Check / Apply Updates directly under Settings. Keep power and internet connected, and choose Reboot now or reboot later after completion. See [installation and update instructions](INSTALL.md) and [button controls](CONTROLS.md).

HDMI startup and the On action automatically select Jivelite’s actual graphics console. Verified after a full reboot; receiver-specific HDMI metadata remains unfinished.

Screen Rotation and Brightness apply immediately. Wait for DISPLAY SAVED — Safe to reboot while the native backup runs; both are restored at startup and used by the early boot screen. HDMI orientation is unaffected.

## Browser configuration pages

`http://YOUR-IP/sable-config.html`

```text
Sable configuration
├── Streaming accounts → BBC Sounds / TIDAL / Beta Spotify / Beta Qobuz
├── Web player
├── FM4 Favorites
├── Lyrion settings
├── System status → CPU / memory / temperature / uptime / drive activity / storage
├── Hardware Setup — Alpha
│   ├── OLED connected / chip select / DC / reset
│   ├── Encoder connected / CLK / DT / switch / reverse direction
│   ├── Button/LED board connected / address / button and LED orientation
│   ├── IR receiver / Shutdown button → GPIO or Not connected
│   ├── Reserved GPIOs → user-entered DAC HAT restrictions
│   ├── Review → validate → Alpha acknowledgement → Save and restart panel
│   └── Restore previous mapping → review and acknowledge
└── piCorePlayer settings
```

**Hardware Setup: Alpha — Not Supported — Use at own risk. Encoder switch GPIO4 / IR GPIO27 is user confirmed after reboot; other mappings and alternative hardware remain unverified.** Browser save/restart was exercised with unchanged wiring. It is a browser page, not an OLED menu item. See [hardware details](HARDWARE.md) and the [testing status list](README.md#features-awaiting-testing-or-completion).
