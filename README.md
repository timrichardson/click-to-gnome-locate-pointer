# Click to GNOME Locate Pointer

Highlight mouse clicks on GNOME Wayland by triggering GNOME's built-in
**Locate Pointer** ripple after each left-button release.

This is a small Python helper for screen recordings, demonstrations, and other
short sessions where visible click feedback is useful. It watches Linux input
events and emits a brief synthetic Ctrl tap through `uinput`; GNOME interprets
that tap as the Locate Pointer shortcut and displays its ripple animation.

> [!WARNING]
> The focused application also receives the synthetic Ctrl tap. This is usually
> harmless, but it can interfere with applications, games, virtual machines,
> remote desktops, terminals, or other keys held at the same time. This tool is
> best used as a temporary recording helper, not as an always-on daemon.

## Requirements

- Linux running GNOME on Wayland
- Python 3.10 or newer
- [`python-evdev`](https://python-evdev.readthedocs.io/)
- The Linux `uinput` kernel module
- `sudo`, unless input-device permissions are configured separately

## Installation

Clone the repository:

```bash
git clone https://github.com/timrichardson/click-to-gnome-locate-pointer.git
cd click-to-gnome-locate-pointer
```

Install `python-evdev` using your distribution's package manager. A distro
package is preferable to `pip` because the child process run by `sudo` must be
able to import the module too.

### Ubuntu or Debian

```bash
sudo apt install python3-evdev
```

### Arch Linux

```bash
sudo pacman -S python-evdev
```

### Fedora

```bash
sudo dnf install python3-evdev
```

Load `uinput` now and automatically on future boots:

```bash
sudo modprobe uinput
echo uinput | sudo tee /etc/modules-load.d/uinput.conf
```

## Usage

Run the script as your normal desktop user, **not** directly with `sudo`:

```bash
python3 click-to-gnome-locate-pointer.py
```

The script will:

1. Save your current GNOME Locate Pointer settings.
2. Enable Locate Pointer and configure its trigger key.
3. Start a child process with `sudo` so it can read `/dev/input/event*` and
   write to `/dev/uinput`.
4. Emit a short Ctrl tap after each qualifying left-button release.
5. Restore your previous GNOME settings when the process exits normally.

Press <kbd>Ctrl</kbd>+<kbd>C</kbd> to stop.

> [!NOTE]
> A `SIGKILL`, hard crash, or abruptly terminated desktop session can prevent
> the previous GNOME settings from being restored.

## Drag filtering

By default, a release is ignored when the pointer moves more than 12 device
units while the left button is held. This avoids displaying a ripple after
dragging windows, selecting text, or resizing.

Change the threshold:

```bash
python3 click-to-gnome-locate-pointer.py --ignore-drags 30
```

Highlight drag releases as well:

```bash
python3 click-to-gnome-locate-pointer.py --include-drags
```

The units are reported by the input device and may not correspond exactly to
screen pixels. Adjust the threshold if your mouse or touchpad reports unusually
large or small movement values.

## Selecting devices

List detected pointer devices:

```bash
python3 click-to-gnome-locate-pointer.py --list
```

Watch a specific device instead of every detected pointer device:

```bash
python3 click-to-gnome-locate-pointer.py --device /dev/input/event5
```

Repeat `--device` to watch more than one device. Selecting devices explicitly
can help if auto-detection produces duplicate ripples or watches an unintended
device.

## Using right Ctrl

To trigger the ripple with right Ctrl instead of left Ctrl:

```bash
python3 click-to-gnome-locate-pointer.py --key KEY_RIGHTCTRL
```

This may reduce interference with common left-Ctrl shortcuts. However, right
Ctrl is often a host or special key in virtual-machine and remote-desktop
software, so choose the key appropriate for your setup.

## Other options

```text
-d, --device PATH       Input device to watch; may be repeated
--list                  List detected pointer devices and exit
--key KEY               uinput key to emit (default: KEY_LEFTCTRL)
--tap-ms MILLISECONDS   Length of the synthetic key tap (default: 25)
--ignore-drags UNITS    Ignore releases after movement exceeds this value
--include-drags         Emit the key after drag releases too
--no-gnome-setup        Do not modify GNOME Locate Pointer settings
--no-auto-sudo          Do not automatically start a privileged child
```

Run the built-in help for the authoritative list:

```bash
python3 click-to-gnome-locate-pointer.py --help
```

## Turning the ripple off manually

Normally the script restores the previous settings on exit. If cleanup was
skipped, reset them manually:

```bash
gsettings set org.gnome.desktop.interface locate-pointer false
gsettings reset org.gnome.mutter locate-pointer-key
```

## Security and limitations

- The script needs permission to read `/dev/input/event*` and write to
  `/dev/uinput`. Those are elevated input privileges; review the code before
  granting them.
- Physical Ctrl presses are not captured or consumed. The script only adds a
  short synthetic Ctrl tap after a mouse-button release.
- The synthetic Ctrl event is delivered system-wide and is also visible to the
  focused application.
- Auto-detection may select more pointer devices than intended. Use `--list`
  and `--device` when necessary.
- The script listens for Linux `BTN_LEFT` events. Mouse-button remapping,
  including some left-handed configurations, may require selecting a different
  device or adapting the button handling.
- This implementation is Linux-, GNOME-, and Wayland-specific.

## License

[MIT](LICENSE) © 2026 Tim Richardson
