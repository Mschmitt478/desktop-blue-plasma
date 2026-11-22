#!/usr/bin/python3
import subprocess
import sys

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gio, Gtk

MODULES = (
    ("Display", "preferences-desktop-display", "kcm_kscreen"),
    ("Appearance", "preferences-desktop-theme", "kcm_lookandfeel"),
    ("Sound", "preferences-desktop-sound", "kcm_pulseaudio"),
    ("Network", "preferences-system-network", "kcm_networkmanagement"),
    ("Mouse", "input-mouse", "kcm_mouse"),
    ("Keyboard", "input-keyboard", "kcm_keyboard"),
    ("Printers", "printer", "kcm_printer_manager"),
    ("Bluetooth", "preferences-system-bluetooth", "kcm_bluetooth"),
    ("Date & Time", "preferences-system-time", "kcm_clock"),
    ("User Accounts", "system-users", "kcm_users"),
    ("Power", "preferences-system-power-management", "kcm_powerdevilprofilesconfig"),
    ("Default Apps", "preferences-desktop-default-applications", "kcm_componentchooser"),
)

def open_settings(button, module):
    subprocess.Popen(["/usr/bin/kcmshell6", module])

def activate(app):
    window = app.get_active_window()
    if window:
        window.present()
        return

    window = Gtk.ApplicationWindow(application=app, title="Control Panel")
    window.set_default_size(640, 365)
    window.set_icon_name("preferences-system")
    content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16, margin=20)
    window.add(content)

    grid = Gtk.Grid(column_spacing=10, row_spacing=10, column_homogeneous=True)
    content.pack_start(grid, True, True, 0)
    colors = Gtk.IconTheme.new()
    colors.set_custom_theme("WindowsXPOriginal")
    for index, (label, icon, module) in enumerate(MODULES):
        item = Gtk.Button()
        item.set_tooltip_text(f"Open {label} settings")
        tile = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6, margin=10)
        icon_info = colors.lookup_icon(icon, 32, Gtk.IconLookupFlags.FORCE_SIZE)
        if icon_info:
            image = Gtk.Image.new_from_pixbuf(icon_info.load_icon())
        else:
            image = Gtk.Image.new_from_icon_name(icon, Gtk.IconSize.DIALOG)
        tile.pack_start(image, False, False, 0)
        tile.pack_start(Gtk.Label(label=label), False, False, 0)
        item.add(tile)
        item.connect("clicked", open_settings, module)
        grid.attach(item, index % 4, index // 4, 1, 1)

    all_settings = Gtk.Button(label="All KDE Settings", halign=Gtk.Align.END)
    all_settings.connect("clicked", lambda button: subprocess.Popen(["/usr/bin/systemsettings"]))
    content.pack_end(all_settings, False, False, 0)
    window.show_all()
    window.present()

if __name__ == "__main__":
    app = Gtk.Application(application_id="local.desktopblue.ControlPanel",
                          flags=Gio.ApplicationFlags.FLAGS_NONE)
    app.connect("activate", activate)
    raise SystemExit(app.run(sys.argv))
