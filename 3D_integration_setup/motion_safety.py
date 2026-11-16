"""Travel envelope for this laser setup; validate before opening hardware."""

import argparse
import math

# Software travel limit per BSC203 channel (1 = Y, 2 = X). Both are NRT100
# stages with 100 mm travel; X beyond 97.5 mm hits the laser. The controller's
# own software limits are set to "ignore", so only these checks and the
# hardware end switches stop an over-travel move.
TRAVEL_MAX_MM = {1: 200.0, 2: 97.5}
_AXIS = {1: "Y", 2: "X"}


def positive_timeout(value):
    timeout = float(value)
    if not math.isfinite(timeout) or timeout <= 0:
        raise argparse.ArgumentTypeError("Timeout must be finite and positive")
    return timeout


def check_position_mm(value, channel):
    """Return value as mm if 0 <= value < that channel's travel limit."""
    limit = TRAVEL_MAX_MM[channel]
    position = float(value)
    if not math.isfinite(position) or not 0 <= position < limit:
        raise argparse.ArgumentTypeError(
            f"{_AXIS[channel]} position {value} out of range: must be finite and "
            f"0 <= position < {limit:g} mm")
    return position


def safe_position_mm(value):
    """argparse type for a Y (channel 1) position."""
    return check_position_mm(value, 1)



# Keep-out corners in stage coordinates, closed boxes (x_min, x_max, y_min, y_max)
# in mm: the stages hit the setup here even though each axis alone is in range.
KEEP_OUT_XY_MM = (
    (50.0, 90.0, 90.0, math.inf),       # 50 <= X <= 90 and Y >= 90
    (90.0, math.inf, 75.0, math.inf),   # X >= 90 and Y >= 75
)


def _describe(box):
    x_min, x_max, y_min, _ = box
    x = f"{x_min:g} <= X <= {x_max:g}" if math.isfinite(x_max) else f"X >= {x_min:g}"
    return f"{x} mm and Y >= {y_min:g} mm"


def check_xy_move(channel, target, x, y):
    """Refuse a single-axis move whose straight path from the live (x, y) touches a keep-out corner.

    channel 1 moves Y and channel 2 moves X; the other coordinate stays fixed, so
    the path is an axis-aligned segment and box overlap is an exact test.
    """
    target = check_position_mm(target, channel)
    x, y = float(x), float(y)
    if not (math.isfinite(x) and math.isfinite(y)):
        raise ValueError(f"Stage position readback is not finite: X={x}, Y={y}")
    end_x, end_y = (x, target) if channel == 1 else (target, y)
    for box in KEEP_OUT_XY_MM:
        x_min, x_max, y_min, y_max = box
        if x_min <= x <= x_max and y_min <= y <= y_max:
            raise ValueError(f"Stage is inside a keep-out corner ({_describe(box)}) at "
                             f"X={x:.3f}, Y={y:.3f} mm; refusing all moves. Home the axis or "
                             f"move it out by hand.")
        if (min(x, end_x) <= x_max and max(x, end_x) >= x_min
                and min(y, end_y) <= y_max and max(y, end_y) >= y_min):
            raise ValueError(f"Refusing {_AXIS[channel]} move to {target:.3f} mm from X={x:.3f}, "
                             f"Y={y:.3f} mm: the path enters the keep-out corner ({_describe(box)}).")
    return target
