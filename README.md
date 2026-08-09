# Click to GNOME Locate Pointer

Highlight mouse clicks on GNOME Wayland by triggering GNOME's built-in
**Locate Pointer** ripple after each primary mouse-button release.

Useful for screen recordings and demonstrations. While running, the script
temporarily enables Locate Pointer and emits a brief synthetic Ctrl tap through
`uinput` after each primary-button release.

> [!WARNING]
> The focused application also receives the synthetic Ctrl tap. This can
> interfere with applications, games, virtual machines, or remote desktops.
> Use this as a temporary recording helper, not an always-on daemon.

## Install

Requires Python 3.10+, `python-evdev`, `uinput`, and GNOME on Wayland.

```bash
git clone https://github.com/timrichardson/click-to-gnome-locate-pointer.git
cd click-to-gnome-locate-pointer
make install
```

This installs `click-to-gnome-locate-pointer` in `~/.local/bin`. Ensure that
directory is on your `PATH`. Remove it later with `make uninstall`.

Install `python-evdev`:

```bash
# Ubuntu/Debian
sudo apt install python3-evdev

# Arch Linux
sudo pacman -S python-evdev

# Fedora
sudo dnf install python3-evdev
```

Load `uinput` now and on future boots:

```bash
sudo modprobe uinput
echo uinput | sudo tee /etc/modules-load.d/uinput.conf
```

## Run

Run as your normal desktop user, **not** directly with `sudo`:

```bash
click-to-gnome-locate-pointer
```

The script enables GNOME's Locate Pointer feature, starts a privileged child
to access the input devices, and restores your previous GNOME settings when it
exits. Press <kbd>Ctrl</kbd>+<kbd>C</kbd> to stop.

It automatically reads GNOME's mouse handedness setting, watching raw
`BTN_LEFT` for a right-handed mouse or raw `BTN_RIGHT` for a left-handed mouse.

By default, releases after more than 12 device units of movement are ignored,
preventing a ripple after most drag operations.

## Useful options

```bash
# List detected pointer devices
click-to-gnome-locate-pointer --list

# Watch one device
click-to-gnome-locate-pointer --device /dev/input/event5

# Override automatic handedness detection with a raw button
click-to-gnome-locate-pointer --button right

# Adjust or disable drag filtering
click-to-gnome-locate-pointer --ignore-drags 30
click-to-gnome-locate-pointer --include-drags

# Emit right Ctrl instead of left Ctrl
click-to-gnome-locate-pointer --key KEY_RIGHTCTRL
```

Run `click-to-gnome-locate-pointer --help` for all options. The script can also
be run directly from a checkout with `python3 click-to-gnome-locate-pointer.py`.

## Versions and releases

```bash
click-to-gnome-locate-pointer --version
```

Published versions are available from
[GitHub Releases](https://github.com/timrichardson/click-to-gnome-locate-pointer/releases)
and use matching Git tags such as `v0.8`.

## Notes

- The input-monitoring child normally runs through `sudo` because reading
  `/dev/input/event*` and writing `/dev/uinput` require elevated privileges.
  The script does not make permanent permission changes.
- Auto-detection may watch too many devices. Use `--list` and `--device` if
  clicks produce duplicate ripples.
- `--button auto` follows GNOME's mouse handedness setting. Use `--button left`
  or `--button right` for unusual mappings. Touchpads configured independently
  of the mouse may require an explicit override.
- A hard crash or `SIGKILL` may prevent automatic restoration of GNOME settings.

To disable and reset Locate Pointer manually:

```bash
gsettings set org.gnome.desktop.interface locate-pointer false
gsettings reset org.gnome.mutter locate-pointer-key
```

## License

[MIT](LICENSE) © 2026 Tim Richardson
