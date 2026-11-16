"""Homing history and calibration validity; importing this opens no hardware."""

from datetime import datetime, timezone
import json
from pathlib import Path
import os
import tempfile


HOMING_FILE = Path(__file__).resolve().parent / "laser_homing.json"
# BSC203 stage channels by axis; Y keeps its historical channel 1.
AXIS_CHANNELS = {"y": 1, "x": 2}
AXIS_NAMES = {channel: axis.upper() for axis, channel in AXIS_CHANNELS.items()}
# Power loss reverts the controller to ~6e-5 mm/s, so homing sets this again.
MAX_VELOCITY_MM_S = 5.0
# NRT100/BSC20x APT velocity units per mm/s at 409600 steps/mm; raw units keep
# the check independent of each caller's pylablib scale.
VELOCITY_UNITS_PER_MM_S = 21987328
MAX_VELOCITY_RAW = round(MAX_VELOCITY_MM_S * VELOCITY_UNITS_PER_MM_S)


def require_enabled(stage, channel=1, status=None):
    # Status bit 31 follows the controller's front-panel channel enable button.
    # A disabled stepper drive still counts steps and reports moves complete.
    status = stage.get_status(channel=channel) if status is None else status
    if "enabled" not in status:
        axis = AXIS_NAMES.get(channel, "?")
        raise RuntimeError(f"Laser {axis} stage (channel {channel}) is not enabled. Press its enable "
                           f"button on the APT controller (light green), then re-home with "
                           f"dy_motion_v1.py --home --channel {channel}.")


def require_homed(stage, channel=1):
    status = stage.get_status(channel=channel)
    require_enabled(stage, channel, status)
    if "homed" not in status or "homing" in status:
        axis = AXIS_NAMES.get(channel, "?")
        raise RuntimeError(f"Laser {axis} stage (channel {channel}) is not currently homed. "
                           f"Run dy_motion_v1.py --home --channel {channel}.")


def configure_velocity(stage, channel):
    """Set the move speed lost on power loss; acceleration is left unchanged."""
    stage.setup_velocity(max_velocity=MAX_VELOCITY_RAW, channel=channel, scale=False)
    require_velocity(stage, channel)


def require_velocity(stage, channel):
    raw = stage.get_velocity_parameters(channel=channel, scale=False).max_velocity
    if abs(raw - MAX_VELOCITY_RAW) > 0.01 * MAX_VELOCITY_RAW:
        axis = AXIS_NAMES.get(channel, "?")
        raise RuntimeError(f"Laser {axis} stage (channel {channel}) max velocity is "
                           f"{raw / VELOCITY_UNITS_PER_MM_S:.3g} mm/s, not {MAX_VELOCITY_MM_S:g} mm/s "
                           f"(likely power loss). Run dy_motion_v1.py --home --channel {channel}.")


def require_motion_ready(stage, channel=1):
    require_homed(stage, channel)
    require_velocity(stage, channel)


def read_history():
    try:
        return json.loads(HOMING_FILE.read_text())
    except (OSError, ValueError) as exc:
        raise ValueError(f"Cannot read homing history {HOMING_FILE}; "
                         "saved pixel positions cannot be used.") from exc


def record_home(channel, homed_at, source="dy_motion_v1.py --home"):
    """Atomically update one channel; None invalidates it before homing starts."""
    data = read_history() if HOMING_FILE.exists() else {"schema_version": 1, "channels": {}}
    data["channels"][str(channel)] = {"homed_at": homed_at, "source": source}
    fd, name = tempfile.mkstemp(prefix=".laser_homing-", dir=HOMING_FILE.parent)
    try:
        with os.fdopen(fd, "w") as output:
            json.dump(data, output, indent=2)
            output.write("\n")
        os.replace(name, HOMING_FILE)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def timestamp(value):
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        raise ValueError("Timestamp must include a timezone")
    return parsed


def load_pixel_positions(path, channel=1):
    """Reject stale/undated calibrations using measurement time, never file mtime."""
    data = json.loads(Path(path).read_text())
    try:
        homed_at = timestamp(read_history()["channels"][str(channel)]["homed_at"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("No valid homing date for this channel; saved pixel positions "
                         "cannot be used. Run dy_motion_v1.py --home.") from exc
    valid = {}
    for key, pixel in data["pixels"].items():
        try:
            measured_at = timestamp(pixel.get("measured_at", data.get("measured_at")))
            current = homed_at <= measured_at <= datetime.now(timezone.utc)
        except (TypeError, ValueError):
            current = False
        if current and not pixel.get("deprecated", False):
            valid[key] = pixel
    if len(valid) != len(data["pixels"]):
        stale = sorted(set(data["pixels"]) - set(valid))
        raise ValueError(f"Deprecated pixel locations in {path}: {', '.join(stale)}. "
                         f"Locations must have a timezone-qualified measured_at on or after "
                         f"the latest homing ({homed_at.isoformat()}). Repeat the position scan.")
    return data
