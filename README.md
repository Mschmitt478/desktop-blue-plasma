# Desktop Blue for KDE Plasma

Desktop Blue recreates this XP-era desktop setup on a clean Bazzite KDE install. It uses a raised cobalt taskbar with a lighter notification area, the original green Start artwork with Plasma’s cascading Kicker menu, a blue window decoration with period-style caption buttons, and Microsoft’s Tahoma fonts and Windows XP SP3 shell icons.

## Install

Open a terminal in your logged-in Plasma session and run the installer.

```sh
./install.py
```

The installer runs as your desktop user. It needs internet access on the first run and restarts the Plasma shell near the end to load the new panel. Your session and running applications remain open. Reopen any apps that cache their previous fonts or styles.

The first run downloads the 316 MiB Microsoft XP SP3 redistributable to extract two font files. It verifies the installer and font checksums, caches only the extracted fonts, and never runs the Windows executable. The shell icons, Start artwork, and XP-tan wallpaper also come from documented upstream sources.

## Compatibility

The reference system is **Bazzite KDE, Plasma 6.8.3 on Wayland**, with Dolphin and Konsole 26.08.3. The installer uses user-level KDE and XDG settings, so it is distro-portable in principle. Other distributions need the same tools and plugins, including a systemd-managed Plasma shell, Plasma 6.8 or newer within Plasma 6, the Aurorae v2 KWin decoration backend, the Oxygen Qt 6 widget style and icons, Dolphin, and Konsole. Plasma 5 and older Plasma 6 installations are outside the supported range.

Run `./install.py --check` to check the installed tools and plugins. Typical additional dependencies are curl, 7-Zip, cabextract, icoutils, ImageMagick 7, Pillow, and PyGObject with GTK 3. On a different distribution, use its normal package mechanism to get missing dependencies. Use `./install.py --stage /path/to/new-directory` to assemble the files without touching the desktop.

## What it sets up

- A full-width bottom taskbar with a beveled blue surface, lighter tray, separately labeled open windows, and a right-aligned 12-hour clock in 10 pt Tahoma. The tray boundary is proportioned for the original 1920×1080 display.
- The green Start button and Kicker, with Control Panel pinned to the launcher and a small set of available application shortcuts.
- Blue Aurorae title bars, blue Minimize and Maximize/Restore buttons, and a red Close button.
- The warm KDE color scheme, Oxygen application style, original XP shell icons, and a desktop Recycle Bin with its 32-bit empty and full artwork.
- Original Tahoma at 10 pt for standard Plasma, KDE, and GTK UI text, with bold window titles. Applications that set their own font or require monospace keep that behavior.
- The XP-tan Bliss desktop wallpaper and a blue, banded lock-screen backdrop. Plasma handles unlocking.
- A classic Dolphin menu, address field, and navigation toolbar, a Control Panel with links to real KDE settings, and an opaque black Konsole profile with light gray text and the classic color palette.

The installer replaces the contents of the primary panel and preserves other panels. It uses the default browser when Zen is absent. The repository contains no account activity identifiers, monitor identifiers, private desktop files, or application data.

## Restore

Run the installer with `--restore` to recover the configuration captured by the first installation.

```sh
./install.py --restore
```

The restore point is stored in `$XDG_STATE_HOME/desktop-blue-plasma`, normally `~/.local/state/desktop-blue-plasma`. Restoring also rolls back later changes to the configuration files and theme paths tracked by the installer.

## Artwork and sources

Desktop Blue’s panel SVGs and Plasma colors build on the KDE Visual Design Group’s Breeze assets, and the application colors build on KDE’s Oxygen Cold scheme. The upstream Breeze theme identifies its license as LGPL. The installer derives Dolphin’s toolbar from the corresponding upstream Dolphin release. [KDE LibPlasma](https://github.com/KDE/libplasma/tree/v6.8.3/src/desktoptheme) · [Oxygen](https://github.com/KDE/oxygen) · [Dolphin](https://github.com/KDE/dolphin)

Microsoft artwork, fonts, and the XP-tan wallpaper are downloaded at install time. The icon theme maps original Windows XP SP3 shell resources to Linux names. The Start image is a pixel crop from the original Windows XP screenshot. [Windows XP shell resources](https://github.com/bartekl1/windows-ui-assets/tree/21970f48b8f66b4d44742cb30388c1454512d681/Icons/Windows%20XP) · [Start button screenshot](https://bootstrike.com/WindowsXP/review.php) · [XP-tan wallpaper](https://knowyourmeme.com/photos/1334837-windows-xp-bliss-wallpaper) · [Microsoft Tahoma](https://learn.microsoft.com/en-us/typography/font-list/tahoma)
