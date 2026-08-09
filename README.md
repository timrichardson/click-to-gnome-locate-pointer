# Click to GNOME Locate Pointer

Highlight mouse clicks on GNOME Wayland by triggering GNOME's built-in
**Locate Pointer** ripple after each raw Linux `BTN_LEFT` release.

Useful for screen recordings and demonstrations. The script watches Linux
input events and emits a brief synthetic Ctrl tap through `uinput`.

> [!WARNING]
> The focused application also receives the synthetic Ctrl tap. This can
> interfere with applications, games, virtual machines, or remote desktops.
> Use this as a temporary recording helper, not an always-on daemon.

## Install

Requires Python 3.10+, `python-evdev`, `uinput`, and GNOME on Wayland.

```bash
git clone https://github.com/timrichardson/click-to-gnome-locate-pointer.git
cd click-to-gnome-locate-pointer
```

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
python3 click-to-gnome-locate-pointer.py
```

The script enables GNOME's Locate Pointer feature, starts a privileged child
to access the input devices, and restores your previous GNOME settings when it
exits. Press <kbd>Ctrl</kbd>+<kbd>C</kbd> to stop.

By default, releases after more than 12 device units of movement are ignored,
preventing a ripple after most drag operations.

## Useful options

```bash
# List detected pointer devices
python3 click-to-gnome-locate-pointer.py --list

# Watch one device
python3 click-to-gnome-locate-pointer.py --device /dev/input/event5

# Adjust or disable drag filtering
python3 click-to-gnome-locate-pointer.py --ignore-drags 30
python3 click-to-gnome-locate-pointer.py --include-drags

# Emit right Ctrl instead of left Ctrl
python3 click-to-gnome-locate-pointer.py --key KEY_RIGHTCTRL
```

Run `python3 click-to-gnome-locate-pointer.py --help` for all options.

## Notes

- The script needs permission to read `/dev/input/event*` and write to
  `/dev/uinput`; review the code before granting elevated input access.
- Auto-detection may watch too many devices. Use `--list` and `--device` if
  clicks produce duplicate ripples.
- The script watches the raw Linux `BTN_LEFT` event, before GNOME applies its
  logical button mapping. This is normally the physical left button. With a
  left-handed mouse configuration, GNOME may treat it as right-click, so the
  ripple can appear on right-click rather than on the primary click.
- A hard crash or `SIGKILL` may prevent automatic restoration of GNOME settings.

To disable and reset Locate Pointer manually:

```bash
gsettings set org.gnome.desktop.interface locate-pointer false
gsettings reset org.gnome.mutter locate-pointer-key
```

## License

[MIT](LICENSE) © 2026 Tim Richardson
