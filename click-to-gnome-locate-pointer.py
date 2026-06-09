#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Tim Richardson
"""
Emit a quick Ctrl tap after each left mouse-button release so GNOME's
"Locate Pointer" ripple can be used as a mouse-click highlight under Wayland.

Usage
-----
Install dependencies on Ubuntu/Debian:
    sudo apt install python3-evdev
    sudo modprobe uinput

Run this script as your normal desktop user, not with sudo:
    python3 ~/click-to-gnome-locate-pointer.py --ignore-drags 12

Before asking for sudo, the script enables GNOME's locate-pointer ripple and
sets GNOME's locate-pointer key to match --key. By default this is:
    gsettings set org.gnome.desktop.interface locate-pointer true
    gsettings set org.gnome.mutter locate-pointer-key Control_L

It then re-runs itself with sudo so it can read /dev/input/event* and write
/dev/uinput. sudo will prompt for your password if needed.

Optional:
    python3 ~/click-to-gnome-locate-pointer.py --list
    python3 ~/click-to-gnome-locate-pointer.py --key KEY_RIGHTCTRL --ignore-drags 12
    python3 ~/click-to-gnome-locate-pointer.py --no-gnome-setup --ignore-drags 12

Turn it off:
    # Stop the running script with Ctrl-C, or kill/stop its service if you made one.
    gsettings set org.gnome.desktop.interface locate-pointer false
    gsettings reset org.gnome.mutter locate-pointer-key

Main risks
----------
- It needs elevated input privileges: read access to /dev/input/event* and
  write access to /dev/uinput.
- The focused application also sees the fake Ctrl tap. Usually harmless, but
  it can interfere with apps, VMs, remote desktops, games, terminals, or if
  another key is physically held at the same time.
- It is best used as a temporary recording helper, not an always-on daemon.
- Auto-detection may watch more pointer devices than intended. Use --list and
  --device /dev/input/eventX if it double-fires or reacts to the wrong device.
- Use --ignore-drags, for example --ignore-drags 12, if you do not want drag
  releases to trigger the ripple.
"""

from __future__ import annotations

import argparse
import os
import select
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

try:
    from evdev import InputDevice, UInput, ecodes, list_devices
except ImportError:  # pragma: no cover - friendly runtime error
    print(
        "Missing Python module 'evdev'. Install it with:\n"
        "  sudo apt install python3-evdev\n"
        "or:\n"
        "  python3 -m pip install --user evdev",
        file=sys.stderr,
    )
    sys.exit(2)


@dataclass
class DeviceState:
    down: bool = False
    rel_motion: int = 0
    abs_x: int | None = None
    abs_y: int | None = None
    start_abs_x: int | None = None
    start_abs_y: int | None = None


def key_code(name: str) -> int:
    code = ecodes.ecodes.get(name)
    if code is None:
        raise SystemExit(f"Unknown key code {name!r}; try KEY_LEFTCTRL")
    return code


def open_device(path: str) -> InputDevice | None:
    try:
        return InputDevice(path)
    except PermissionError:
        print(f"Permission denied opening {path}; try running with sudo", file=sys.stderr)
    except OSError as exc:
        print(f"Could not open {path}: {exc}", file=sys.stderr)
    return None


def is_pointer(dev: InputDevice) -> bool:
    try:
        caps = dev.capabilities(absinfo=False)
    except OSError:
        return False

    keys = set(caps.get(ecodes.EV_KEY, []))
    rels = set(caps.get(ecodes.EV_REL, []))
    abss = set(caps.get(ecodes.EV_ABS, []))

    has_left_click = ecodes.BTN_LEFT in keys
    has_pointer_axis = (
        ecodes.REL_X in rels
        or ecodes.REL_Y in rels
        or ecodes.ABS_X in abss
        or ecodes.ABS_Y in abss
    )
    return has_left_click and has_pointer_axis


def pointer_devices() -> list[InputDevice]:
    devices: list[InputDevice] = []
    for path in list_devices():
        dev = open_device(path)
        if dev and is_pointer(dev):
            devices.append(dev)
        elif dev:
            dev.close()
    return devices


def describe(dev: InputDevice) -> str:
    return f"{dev.path:18} {dev.name} ({dev.phys or 'no-phys'})"


def drag_distance(state: DeviceState) -> int:
    rel = state.rel_motion
    abs_dist = 0
    if None not in (state.abs_x, state.abs_y, state.start_abs_x, state.start_abs_y):
        abs_dist = abs(state.abs_x - state.start_abs_x) + abs(state.abs_y - state.start_abs_y)  # type: ignore[operator]
    return max(rel, abs_dist)


def tap(ui: UInput, code: int, tap_ms: int) -> None:
    ui.write(ecodes.EV_KEY, code, 1)
    ui.syn()
    time.sleep(tap_ms / 1000)
    ui.write(ecodes.EV_KEY, code, 0)
    ui.syn()


GNOME_KEYSYMS = {
    "KEY_LEFTCTRL": "Control_L",
    "KEY_RIGHTCTRL": "Control_R",
    "KEY_LEFTSHIFT": "Shift_L",
    "KEY_RIGHTSHIFT": "Shift_R",
    "KEY_LEFTALT": "Alt_L",
    "KEY_RIGHTALT": "Alt_R",
}


def gnome_keysym_for_evdev(evdev_key_name: str) -> str:
    if evdev_key_name in GNOME_KEYSYMS:
        return GNOME_KEYSYMS[evdev_key_name]
    if evdev_key_name.startswith("KEY_F") and evdev_key_name[5:].isdigit():
        return evdev_key_name[4:]
    raise SystemExit(
        f"Don't know the GNOME keysym for {evdev_key_name!r}. "
        "Use KEY_LEFTCTRL or KEY_RIGHTCTRL, or add a mapping in GNOME_KEYSYMS."
    )


def run_gsettings(args: list[str]) -> bool:
    if shutil.which("gsettings") is None:
        print("gsettings not found; skipping GNOME locate-pointer setup.", file=sys.stderr)
        return False

    proc = subprocess.run(
        ["gsettings", *args],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        print(
            "Could not configure GNOME with gsettings; skipping GNOME setup.\n"
            f"gsettings {' '.join(args)}\n"
            f"{proc.stderr.strip()}",
            file=sys.stderr,
        )
        return False
    return True


def configure_gnome_locate_pointer(evdev_key_name: str) -> None:
    if os.geteuid() == 0:
        print(
            "Skipping GNOME setup while running as root. For automatic GNOME setup, "
            "run this script as your normal desktop user and let it ask for sudo.",
            file=sys.stderr,
        )
        return

    gnome_key = gnome_keysym_for_evdev(evdev_key_name)
    ok = True
    ok &= run_gsettings(["set", "org.gnome.desktop.interface", "locate-pointer", "true"])
    ok &= run_gsettings(["set", "org.gnome.mutter", "locate-pointer-key", gnome_key])
    if ok:
        print(f"GNOME locate-pointer enabled; trigger key set to {gnome_key}.")


def reexec_with_sudo() -> None:
    if os.geteuid() == 0:
        return

    sudo = shutil.which("sudo")
    if sudo is None:
        print("sudo not found; run this script as root or install sudo.", file=sys.stderr)
        raise SystemExit(1)

    script = str(Path(__file__).resolve())
    forwarded_args = [arg for arg in sys.argv[1:] if arg != "--no-gnome-setup"]
    cmd = [sudo, sys.executable or "python3", script, "--no-gnome-setup", *forwarded_args]
    print("Requesting sudo so the script can read /dev/input/event* and write /dev/uinput...")
    os.execvp(sudo, cmd)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Convert left mouse-button release into a brief Ctrl tap for GNOME locate-pointer."
    )
    parser.add_argument(
        "-d",
        "--device",
        action="append",
        help="/dev/input/eventX device to watch; repeatable. Default: all detected pointer devices.",
    )
    parser.add_argument("--list", action="store_true", help="List detected pointer devices and exit.")
    parser.add_argument("--key", default="KEY_LEFTCTRL", help="uinput key to emit; default KEY_LEFTCTRL.")
    parser.add_argument("--tap-ms", type=int, default=25, help="Ctrl tap length in milliseconds; default 25.")
    parser.add_argument(
        "--no-gnome-setup",
        action="store_true",
        help="Do not enable GNOME locate-pointer or set org.gnome.mutter locate-pointer-key before sudo.",
    )
    parser.add_argument(
        "--no-auto-sudo",
        action="store_true",
        help="Do not re-run through sudo automatically; useful if permissions are handled another way.",
    )
    parser.add_argument(
        "--ignore-drags",
        type=int,
        default=None,
        metavar="PIXELS",
        help="Do not emit Ctrl if movement while held exceeds PIXELS; disabled by default.",
    )
    args = parser.parse_args()

    key_code(args.key)  # Validate early, before changing GNOME settings or asking for sudo.

    if not args.list and not args.no_gnome_setup:
        configure_gnome_locate_pointer(args.key)

    if not args.no_auto_sudo:
        reexec_with_sudo()

    if args.list:
        devs = pointer_devices()
        if not devs:
            print("No pointer devices found, or no permission to read them.")
            return 1
        for dev in devs:
            print(describe(dev))
            dev.close()
        return 0

    if args.device:
        devs = [dev for p in args.device if (dev := open_device(p))]
    else:
        devs = pointer_devices()

    if not devs:
        print(
            "No input devices to watch. Try --list, check /dev/input permissions, or run: sudo modprobe uinput",
            file=sys.stderr,
        )
        return 1

    code = key_code(args.key)

    try:
        ui = UInput({ecodes.EV_KEY: [code]}, name="click-to-gnome-locate-pointer")
    except PermissionError:
        print("Permission denied opening /dev/uinput; try sudo or adjust uinput permissions.", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"Could not create uinput device: {exc}\nTry: sudo modprobe uinput", file=sys.stderr)
        return 1

    states = {dev.fd: DeviceState() for dev in devs}

    print("Watching pointer devices:")
    for dev in devs:
        print("  " + describe(dev))
    print(f"Emitting {args.key} for {args.tap_ms} ms after BTN_LEFT release. Ctrl-C to stop.")

    try:
        while True:
            readable, _, _ = select.select(devs, [], [])
            for dev in readable:
                state = states[dev.fd]
                for ev in dev.read():
                    if ev.type == ecodes.EV_ABS:
                        if ev.code == ecodes.ABS_X:
                            state.abs_x = ev.value
                        elif ev.code == ecodes.ABS_Y:
                            state.abs_y = ev.value
                    elif ev.type == ecodes.EV_REL and state.down:
                        if ev.code in (ecodes.REL_X, ecodes.REL_Y):
                            state.rel_motion += abs(ev.value)
                    elif ev.type == ecodes.EV_KEY and ev.code == ecodes.BTN_LEFT:
                        if ev.value == 1:  # down
                            state.down = True
                            state.rel_motion = 0
                            state.start_abs_x = state.abs_x
                            state.start_abs_y = state.abs_y
                        elif ev.value == 0 and state.down:  # up
                            state.down = False
                            if args.ignore_drags is not None and drag_distance(state) > args.ignore_drags:
                                continue
                            tap(ui, code, args.tap_ms)
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        for dev in devs:
            dev.close()
        ui.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
