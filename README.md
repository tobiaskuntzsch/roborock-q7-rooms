# Roborock Q7 Room Cleaning for Home Assistant

Custom [HACS](https://hacs.xyz/) integration that adds **room/segment cleaning** for Roborock Q7 series vacuums in Home Assistant.

The official Roborock integration (as of 2026.4) does not yet support room cleaning for Q7 devices because they use a different protocol (B01). This integration bridges that gap by using [python-roborock](https://github.com/Python-roborock/python-roborock) v5 which has full Q7 segment cleaning support.

## Features

- Room/segment cleaning via `roborock_q7_rooms.clean_segments` service
- Stop and dock services
- **No duplicate vacuum entity** - works alongside the official Roborock integration
- **No separate login** - reuses credentials from the official Roborock integration

## Installation

### HACS (recommended)

1. Open HACS in Home Assistant
2. Click the three dots in the top right corner and select "Custom repositories"
3. Add this repository URL: `https://github.com/tobiaskuntzsch/roborock-q7-rooms`
4. Category: Integration
5. Click "Add"
6. Search for "Roborock Q7 Room Cleaning" and install it
7. Restart Home Assistant

Or click this button to add the repository directly:

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=tobiaskuntzsch&repository=roborock-q7-rooms&category=integration)

### Setup

1. Make sure the official **Roborock integration** is already set up in Home Assistant
2. Go to **Settings** > **Devices & Services** > **Add Integration**
3. Search for "Roborock Q7 Room Cleaning"
4. Confirm - no login needed, credentials are reused from the official Roborock integration

## Usage

### Services

#### `roborock_q7_rooms.clean_segments`

Start room cleaning for specific room IDs.

```yaml
action: roborock_q7_rooms.clean_segments
data:
  segments:
    - 12
```

Multiple rooms:

```yaml
action: roborock_q7_rooms.clean_segments
data:
  segments:
    - 10
    - 12
    - 13
  repeat: 2
```

#### `roborock_q7_rooms.stop`

Stop the vacuum.

#### `roborock_q7_rooms.dock`

Send the vacuum back to its dock.

### Example HA Script

```yaml
alias: Flur saugen (OG)
sequence:
  - action: roborock_q7_rooms.clean_segments
    data:
      segments:
        - 12
mode: single
icon: mdi:robot-vacuum
```

## Finding Your Room IDs

Room IDs are device-specific and not exposed by the Q7 API directly. Use the included tool to discover them:

```bash
pip install python-roborock
python tools/find_room_ids.py
```

1. The tool will log in to your Roborock account (email + verification code, cached after first use)
2. It connects to your Q7 and watches the `recommend.room_ids` property
3. **Open the Roborock app** and start a room clean for a specific room
4. The tool will print the room ID(s) being cleaned
5. Repeat for each room to build your mapping
6. Press `Ctrl+C` to stop

Example output:

```
--- Staubsauger Obergeschoss ---
Status: charging, Battery: 100%
Map: Obergeschoss (ID: 1770036133)

Watching for room IDs...
Start a room clean from the Roborock app now!

  Status: charging
  Status: sweep_moping_2
  >>> Room IDs: [12, 11, 10, 15, 13]
```

Tip: Select **all rooms** in the Roborock app at once to get all IDs in a single run. Then select individual rooms to identify which ID belongs to which room.

## How It Works

The Q7 uses the B01 protocol (different from V1 used by S/Qrevo series). This integration:

1. Reads credentials from the official Roborock integration's config entry
2. Connects to the Q7 via MQTT using `python-roborock` v5
3. Sends `service.set_room_clean` commands with the B01 protocol
4. Registers HA services (no extra entities created)

## Requirements

- Home Assistant 2026.3+
- Official Roborock integration set up
- A Roborock Q7 series vacuum (model `roborock.vacuum.sc05`)
- [HACS](https://hacs.xyz/) installed

## Credits

- [python-roborock](https://github.com/Python-roborock/python-roborock) - the library that makes this possible
- PR [#778](https://github.com/Python-roborock/python-roborock/pull/778) which added Q7 segment cleaning support
