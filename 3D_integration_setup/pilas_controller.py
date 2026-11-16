#!/usr/bin/env python3
"""PILAS controller: inspect TUNE, set TUNE, or select auto/manual mode.

Confirm compatibility with the manual supplied with YOUR controller before use.
See pilas_tune.md for protocol sources, prerequisites, and examples.

SAFETY: software must never switch laser emission on or off. Turning the laser
on is a deliberate physical action by a person (key switch, then the front-panel
ON button), because emission with the enclosure open is dangerous. The manual's
`ld=` and `cw=` commands are therefore refused by `exchange()`; do not add a
bypass. Software may only read the emission state and refuse to take data.
"""

import argparse
from decimal import Decimal, InvalidOperation
import os
import re
import sys
import time


# AEe: setting/readback tested; AEb: identity and readback tested only.
KNOWN_FIRMWARE = ("SW.PiLas.V1.1.AEe", "SW.PiLas.V1.1.AEb")
KNOWN_ADAPTER_SERIALS = {"A505ZP7D", "BG01VUC3"}
LASER_OFF_MESSAGE = "The laser is turned off. Please turn it on before trying to take data."
EMISSION_OFF_MESSAGE = ("Laser emission is off: the PILAS front-panel emission button is not on "
                        "(mState? field 2 = 0). Turn it on before trying to take data.")
# Manual commands that set pulsed (ld=) or CW (cw=) emission. Never sent: see
# the module docstring and docs/pilas_tune.md ("Laser emission is manual only").
FORBIDDEN_EMISSION_COMMANDS = ("ld", "cw")


def require_laser_port(port="auto"):
    """Require a visible PILAS port before acquisition; opens no hardware.

    Missing USB connectivity is treated as laser-off for the acquisition UI.
    A visible port does not establish that the laser is emitting.
    """
    from serial.tools import list_ports

    ports = list(list_ports.comports())
    if port in (None, "auto"):
        candidates = [p.device for p in ports
                      if getattr(p, "serial_number", None) in KNOWN_ADAPTER_SERIALS
                      or "pilas" in (getattr(p, "description", "") or "").lower()]
        if not candidates:
            raise RuntimeError(LASER_OFF_MESSAGE + " No PILAS serial port is visible.")
        if len(candidates) != 1:
            raise RuntimeError("Multiple PILAS ports are visible; select one with --pilas-port.")
        port = candidates[0]
    matches = [p for p in ports if os.path.realpath(p.device).casefold() ==
               os.path.realpath(str(port)).casefold()]
    if not matches:
        raise RuntimeError(LASER_OFF_MESSAGE + f" PILAS port {port!r} is not visible.")
    selected = matches[0]
    if ((getattr(selected, "vid", None), getattr(selected, "pid", None)) == (0x0403, 0xFAF0)
            or re.search(r"\bAPT\b", getattr(selected, "description", "") or "", re.I)):
        raise RuntimeError(f"Configured PILAS port {port!r} belongs to a Thorlabs APT controller. "
                           "Select the laser port with --pilas-port.")
    return str(port)


def percent(text):
    """Reject rounding, nonfinite values, and values outside the protocol range."""
    try:
        value = Decimal(text)
        if not value.is_finite() or not 0 <= value <= 100:
            raise ValueError
        if value * 10 != (value * 10).to_integral_value():
            raise ValueError
        return value
    except (InvalidOperation, ValueError):
        raise argparse.ArgumentTypeError("Use 0..100 percent in steps of 0.1") from None


def exchange(port, command):
    """One request, one bounded CRLF reply; unexpected formats fail closed."""
    name, setter, _ = command.partition("=")
    if setter and name.strip().lower() in FORBIDDEN_EMISSION_COMMANDS:
        raise PermissionError(f"Refusing {command!r}: laser emission is switched on or off only by a "
                              "person at the controller (key and ON button), never by software.")
    if port.in_waiting:
        raise RuntimeError("Unsolicited/pending serial input; refusing next command")
    payload = (command + "\r").encode("ascii")
    print(f"TX: {command}", flush=True)
    if port.write(payload) != len(payload):
        raise RuntimeError("Incomplete write; controller state is uncertain")
    reply = port.read_until(b"\n", size=512)
    if not reply.endswith(b"\r\n"):
        raise RuntimeError(f"Missing or incomplete CRLF response: {reply!r}")
    text = reply[:-2].decode("ascii")
    print(f"RX: {text}", flush=True)
    return text


def state(port):
    # Section 6 specifies 15 integer fields. Field 14 uses 0.01%, whereas
    # tune= uses 0.1%. Do not assume these two scales are interchangeable.
    response = exchange(port, "mState?")
    if not re.fullmatch(r"-?\d+(?: +-?\d+){14}", response):
        raise RuntimeError("Unrecognized mState reply; check firmware/manual offline")
    values = tuple(map(int, response.split()))
    if values[1] not in (0, 1):
        raise RuntimeError("Invalid emission state readback")
    if values[5] not in (0, 1):
        raise RuntimeError("Invalid TUNE mode readback")
    if not 0 <= values[13] <= 10000:
        raise RuntimeError("Invalid TUNE readback")
    return values


def require_emission(port):
    """Field 2 follows the front-panel emission button (1 = on).

    Verified on the AEb controller on 2026-10-28 by toggling the button: only
    field 2 changed. With it off, the 40 kHz trigger still runs but no light
    reaches the sensor, so acquisitions silently record no signal.
    """
    values = state(port)
    if values[1] != 1:
        raise RuntimeError(EMISSION_OFF_MESSAGE)
    return values


def open_port(name, baudrate=19200):
    import serial

    # Configure before opening. Drivers may still briefly toggle control lines;
    # first commissioning must be done with the sensitive optical path isolated.
    port = serial.Serial(port=None, baudrate=baudrate, bytesize=serial.EIGHTBITS,
                         parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE,
                         timeout=2, write_timeout=2, xonxoff=False,
                         rtscts=False, dsrdtr=False,
                         **({"exclusive": True} if os.name == "posix" else {}))
    port.dtr = False
    port.rts = False
    port.port = name
    port.open()
    return port


def check_emission(name="auto"):
    """Open the laser port, verify protocol and emission, and close it again."""
    port = open_port(require_laser_port(name))
    try:
        verify_protocol(read_identity(port))
        require_emission(port)
    finally:
        port.close()


def set_mode(port, mode):
    """Select a TUNE mode and verify it before returning the new state."""
    wanted = {"manual": 0, "auto": 1}[mode]
    before = state(port)
    if before[5] == wanted:
        print(f"TUNE mode already {mode}")
        return before
    if exchange(port, f"tm={wanted}") != "done":
        raise RuntimeError("Mode change not acknowledged; controller state is uncertain")
    after = state(port)
    if after[5] != wanted:
        raise RuntimeError("TUNE mode readback mismatch")
    check_settings(before, after)
    print(f"Verified TUNE mode: {mode}")
    return after


def check_settings(before, after):
    # TUNE and its mode may change intentionally; measured values may fluctuate.
    if any(before[i] != after[i] for i in (1, 2, 3, 4, 6, 12, 14)):
        raise RuntimeError("Other controller settings changed during the operation")


def apply_tune(port, target):
    """Set TUNE (manual mode) and return the verified mState? fields afterwards."""
    target = percent(str(target))
    before = set_mode(port, "manual")
    if target == Decimal(before[13]) / 100:
        print("Already at requested TUNE; no TUNE write sent")
        return before
    # Never retry a write: a missing reply does not mean it was not applied.
    if exchange(port, f"tune={int(target * 10):04d}") != "done":
        raise RuntimeError("TUNE not acknowledged; controller state is uncertain")
    after = state(port)
    if after[13] != int(target * 100) or after[5] != 0:
        raise RuntimeError("TUNE value/mode readback mismatch; controller state is uncertain")
    check_settings(before, after)
    print(f"Verified TUNE: {target:.1f}% (manual)")
    return after


def read_identity(port):
    """Read a bounded version reply without assuming a model or firmware."""
    if port.in_waiting:
        raise RuntimeError("Pending serial input; refusing identity query")
    print("TX: version?", flush=True)
    if port.write(b"version?\r") != 9:
        raise RuntimeError("Incomplete identity query")
    # version? is multiline; this controller prefixes its reply with two NULs.
    response = bytearray()
    old_timeout = port.timeout
    port.timeout = 0.1
    deadline = time.monotonic() + 3
    try:
        while time.monotonic() < deadline and len(response) < 4096:
            response.extend(port.read(min(port.in_waiting or 1, 4096 - len(response))))
    finally:
        port.timeout = old_timeout
    identity = bytes(response).lstrip(b"\x00").decode("ascii")
    if len(response) >= 4096 or not identity.strip() or not identity.endswith("\r\n"):
        raise RuntimeError(f"Missing, incomplete or oversized identity reply: {bytes(response)!r}")
    print("RX:", flush=True)
    fields = [line.partition(":") for line in identity.splitlines()]
    width = max((len(label) for label, separator, _ in fields if separator), default=0)
    for label, separator, value in fields:
        if separator:
            print(f"  {label + ':':<{width + 1}} {value.strip()}", flush=True)
        else:
            print(f"  {label}", flush=True)
    return identity


def verify_protocol(identity):
    if not any(f"software version: {version}\r\n" in identity for version in KNOWN_FIRMWARE):
        raise RuntimeError("Unrecognized firmware; no further commands sent")


def inspect_tune(port):
    """Read TUNE after the caller has verified the protocol."""
    values = state(port)
    mode = "manual" if values[5] == 0 else "automatic"
    print(f"TUNE: {Decimal(values[13]) / 100:.2f}% ({mode})")
    print("Inspection complete; no setting commands sent")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--tune", type=percent, help="Target percent")
    action.add_argument("--inspect", action="store_true", help="Read identity and TUNE only")
    action.add_argument("--identity", action="store_true", help="Read version? only, including unknown firmware")
    action.add_argument("--list-ports", action="store_true", help="List serial metadata without opening ports")
    action.add_argument("--mode", choices=("auto", "manual"), help="Set TUNE mode")
    action.add_argument("--check-emission", action="store_true",
                        help="Exit 1 unless the front-panel emission button is on")
    parser.add_argument("--port", default=os.environ.get("PILAS_PORT"),
                        help="Laser serial device (or PILAS_PORT); e.g. /dev/ttyUSB1, COM3")
    parser.add_argument("--baudrate", type=int, default=19200,
                        help="Serial baud rate from controller manual (default: 19200)")
    args = parser.parse_args(argv)
    if args.baudrate <= 0:
        parser.error("--baudrate must be positive")
    if args.list_ports:
        from serial.tools import list_ports

        ports = sorted(list_ports.comports(), key=lambda item: item.device)
        for item in ports:
            print(f"{item.device}: {item.description}\n  {item.hwid}")
        if not ports:
            print("No serial ports found")
        return 0
    if not args.port:
        parser.error("Hardware access requires --port or PILAS_PORT; use --list-ports")
    import serial

    port = None
    try:
        port = open_port(args.port, args.baudrate)
        identity = read_identity(port)
        if args.identity:
            print("Identity inspection complete; no setting commands sent")
            return 0
        verify_protocol(identity)
        if args.inspect:
            inspect_tune(port)
        elif args.check_emission:
            require_emission(port)
            print("Laser emission is on")
        elif args.mode:
            set_mode(port, args.mode)
        else:
            apply_tune(port, args.tune)
    except (OSError, RuntimeError, UnicodeError, serial.SerialException) as exc:
        print(f"Stopped: {exc}. No retry or rollback attempted; inspect controller "
              "before any further operation.", file=sys.stderr)
        return 1
    finally:
        if port is not None:
            port.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
