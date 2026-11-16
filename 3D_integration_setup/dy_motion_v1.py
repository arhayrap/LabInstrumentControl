#!/usr/bin/env python3
import sys
import argparse
from datetime import datetime, timezone
from laser_homing import (AXIS_CHANNELS, HOMING_FILE, MAX_VELOCITY_MM_S, configure_velocity,
                          record_home, require_enabled, require_homed, require_motion_ready)
from motion_safety import positive_timeout, safe_position_mm

def resolve_motion_port(port):
    if port != "auto":
        return port
    from serial.tools import list_ports

    ports = list(list_ports.comports())
    candidates = [p.device for p in ports if p.vid == 0x0403 and p.pid == 0xFAF0
                  and "labjack" not in p.description.lower().replace(" ", "")
                  and not (getattr(p, "serial_number", None) or "").startswith("49")]
    if len(candidates) != 1:
        available = ", ".join(f"{p.device} ({p.description})" for p in ports) or "none"
        raise RuntimeError(
            f"Expected one APT controller, found {len(candidates)}. "
            f"Specify --port explicitly (v12: --motion-port). Available ports: {available}"
        )
    return candidates[0]


def main():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(line_buffering=True)
    parser = argparse.ArgumentParser(description="Thorlabs BSC20x Stage Control CLI")
    parser.add_argument("--port", default="auto", help="Serial port (default: detect the single USB APT controller)")
    parser.add_argument("--home", action="store_true", help="Home the stage before moving")
    parser.add_argument("--inspect", action="store_true", help="Read identity, position, status and velocity without moving")
    parser.add_argument("--move", type=safe_position_mm, help="Absolute target in mm (0 <= position < 60)")
    axis = parser.add_mutually_exclusive_group()
    axis.add_argument("--channel", type=int, choices=(1, 2), help="Channel number (1=Y, 2=X; default 1)")
    axis.add_argument("--axis", choices=sorted(AXIS_CHANNELS), help="Axis name instead of --channel")
    parser.add_argument("--timeout", type=positive_timeout, default=60.0,
                        help="Maximum seconds to wait for each home or move (default: 60)")
    args = parser.parse_args()
    args.channel = AXIS_CHANNELS[args.axis] if args.axis else (args.channel or 1)

    if args.inspect and (args.home or args.move is not None):
        parser.error("--inspect cannot be combined with --home or --move")
    if not args.inspect and not args.home and args.move is None:
        print("Error: Specify --inspect, --home or --move <position>")
        sys.exit(1)

    args.port = resolve_motion_port(args.port)

    from pylablib.devices import Thorlabs

    print(f"Connecting to motion controller on {args.port}...")
    
    stage = Thorlabs.KinesisMotor(
        args.port,
        scale=409600,  # steps/mm; derive velocity/acceleration units from controller model
        is_rack_system=True
        )

    try:
        if args.inspect:
            print(f"Controller: {stage.get_device_info()}")
        print(f"Connected. Channel {args.channel} position: "
              f"{stage.get_position(channel=args.channel):.3f} mm; "
              f"status: {stage.get_status(channel=args.channel)}")
        if args.inspect:
            print(f"Velocity parameters (mm/s, mm/s^2): {stage.get_velocity_parameters(channel=args.channel)}")
            print(f"Raw position (steps): {stage.get_position(channel=args.channel, scale=False)}")
            print(f"Raw status: 0x{stage.get_status_n(channel=args.channel):08x}")
            print(f"Raw velocity parameters: {stage.get_velocity_parameters(channel=args.channel, scale=False)}")
            print(f"Homing parameters (mm, mm/s): {stage.get_homing_parameters(channel=args.channel)}")
            print(f"Limit switch parameters (mm): {stage.get_limit_switch_parameters(channel=args.channel)}")
            print(f"General move parameters (mm): {stage.get_gen_move_parameters(channel=args.channel)}")
            print(f"Jog parameters (mm, mm/s, mm/s^2): {stage.get_jog_parameters(channel=args.channel)}")
            print("Inspection complete; no motion or motor-setting commands sent.")
            return
        if args.home:
            try:
                require_enabled(stage, args.channel)  # before invalidating the saved home
            except RuntimeError as exc:
                print(str(exc), file=sys.stderr)
                raise SystemExit(1)
            record_home(args.channel, None)
            print(f"Homing Channel {args.channel}...")
            stage.setup_homing(velocity=1.0, channel=args.channel)
            stage.home(channel=args.channel, timeout=args.timeout, force=True)
            require_homed(stage, args.channel)
            configure_velocity(stage, args.channel)
            record_home(args.channel, datetime.now(timezone.utc).isoformat())
            print(f"Homing complete; max velocity set to {MAX_VELOCITY_MM_S:g} mm/s. "
                  f"Homing date saved to {HOMING_FILE}.")

        if args.move is not None:
            try:
                require_motion_ready(stage, args.channel)
            except RuntimeError as exc:
                print(str(exc), file=sys.stderr)
                raise SystemExit(1)
            pos = args.move
            print(f"Moving Channel {args.channel} to {pos:.3f} mm...")
    
            stage.move_to(pos, channel=args.channel)
    
            try:
                stage.wait_move(channel=args.channel, timeout=args.timeout)
            except Exception:
                try:
                    print(f"Move did not complete: target={pos:.6f} mm, "
                          f"position={stage.get_position(channel=args.channel):.6f} mm, "
                          f"status={stage.get_status(channel=args.channel)}", file=sys.stderr)
                except Exception as diagnostic_error:
                    print(f"Could not read motion diagnostics: {diagnostic_error}", file=sys.stderr)
                raise
    
            current_pos = stage.get_position(channel=args.channel)
            print(f"Movement complete. Current Position: {current_pos:.3f} mm")

    except (Exception, KeyboardInterrupt):
        if args.inspect:
            raise
        print("Motion failed or was interrupted; requesting a stage stop.", file=sys.stderr)
        try:
            stage.stop(channel=args.channel, sync=False)
        except Exception as exc:
            print(f"Could not send stop command: {exc}", file=sys.stderr)
        raise
    finally:
        stage.close()

if __name__ == "__main__":
    main()
