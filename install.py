#!/usr/bin/env python3
"""Install or restore the Desktop Blue Plasma setup for the current user."""

import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time
from xml.etree import ElementTree as ET

REPO = Path(__file__).resolve().parent
HOME = Path.home()
CONFIG = Path(os.environ.get("XDG_CONFIG_HOME") or HOME / ".config")
DATA = Path(os.environ.get("XDG_DATA_HOME") or HOME / ".local/share")
STATE = Path(os.environ.get("XDG_STATE_HOME") or HOME / ".local/state") / "desktop-blue-plasma"
CACHE = Path(os.environ.get("XDG_CACHE_HOME") or HOME / ".cache") / "desktop-blue-plasma"
SHELL = "org.kde.plasmashell"
FAVORITE = "applications:desktop-blue-control-panel.desktop"
FAVORITES_AGENT = "org.kde.plasma.favorites.applications"
FAVORITES_PATH = "/ActivityManager/Resources/Linking"
START = "plasma/desktoptheme/desktop-blue/windows-xp-luna-start.png"
WALLPAPER = "wallpapers/XP-tan-in-the-Bliss.png"
LOCKSCREEN = "wallpapers/Desktop-Blue-Lock-Screen.png"
SHELL32_URL = (
    "https://raw.githubusercontent.com/bartekl1/windows-ui-assets/"
    "21970f48b8f66b4d44742cb30388c1454512d681/Icons/Windows%20XP/dll/shell32.dll"
)
SP3_URL = (
    "https://catalog.s.download.windowsupdate.com/msdownload/update/software/svpk/2008/04/"
    "windowsxp-kb936929-sp3-x86-enu_c81472f7eeea2eca421e116cd4c03e2300ebfde4.exe"
)
FONT_HASHES = {
    "tahoma.ttf": "08f45bf539954d3252df97a2ae563362ed2ad5ebe05f2d1f2bc54b931e4d0550",
    "tahomabd.ttf": "4ba89e145ff39f208151ce269841899fc4e4a360189a4a31dc2359168dae27d0",
}

ASSETS = (
    "plasma/desktoptheme/desktop-blue",
    "aurorae/themes/DesktopBlue",
    "color-schemes/DesktopBlue.colors",
    "konsole/ClassicCmd.profile",
    "konsole/ClassicCmd.colorscheme",
    "icons/WindowsXPOriginal",
    "fonts/WindowsXP",
    "kxmlgui5/dolphin/dolphinui.rc",
    "desktop-blue/control-panel.py",
    "applications/desktop-blue-control-panel.desktop",
    WALLPAPER,
    LOCKSCREEN,
)
CONFIG_FILES = (
    "kdeglobals", "kwinrc", "plasmarc", "plasmashellrc",
    "plasma-org.kde.plasma.desktop-appletsrc", "kscreenlockerrc",
    "dolphinrc", "konsolerc", "gtk-3.0/settings.ini", "gtk-4.0/settings.ini",
)
TRAY_HIDDEN = (
    "org.kde.kdeconnect", "org.kde.plasma.vault", "org.kde.kscreen",
    "org.kde.plasma.battery", "org.kde.plasma.bluetooth", "org.kde.plasma.brightness",
    "org.kde.plasma.cameraindicator", "org.kde.plasma.clipboard",
    "org.kde.plasma.devicenotifier", "org.kde.plasma.keyboardindicator",
    "org.kde.plasma.keyboardlayout", "org.kde.plasma.manage-inputmethod",
    "org.kde.plasma.mediacontroller", "org.kde.plasma.networkmanagement",
    "org.kde.plasma.notifications", "org.kde.plasma.printmanager",
    "org.kde.plasma.volume", "org.kde.plasma.weather",
)


def run(*arguments, capture=False):
    return subprocess.run(
        [str(argument) for argument in arguments],
        check=True,
        text=True,
        stdout=subprocess.PIPE if capture else None,
    ).stdout


def digest(path, algorithm="sha256"):
    with path.open("rb") as file:
        return hashlib.file_digest(file, algorithm).hexdigest()


def download(url, destination, checksum=None, algorithm="sha256"):
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=destination.parent) as work:
        temporary = Path(work) / destination.name
        run("curl", "-fLsS", "--retry", "2", "--connect-timeout", "20", "-o", temporary, url)
        if checksum and digest(temporary, algorithm) != checksum:
            raise ValueError(f"Checksum mismatch for {url}")
        temporary.replace(destination)


def setup_fonts(target):
    cache = CACHE / "fonts"
    if not all((cache / name).is_file() and digest(cache / name) == signature
               for name, signature in FONT_HASHES.items()):
        print("Fetching Microsoft Windows XP SP3 for the original Tahoma fonts.", flush=True)
        with tempfile.TemporaryDirectory() as intermediate:
            work = Path(intermediate)
            installer = work / "xpsp3.exe"
            download(SP3_URL, installer, "c81472f7eeea2eca421e116cd4c03e2300ebfde4", "sha1")
            run("7z", "e", "-y", "-bd", f"-o{work}", installer,
                "i386/tahoma.tt_", "i386/tahomabd.tt_", capture=True)
            run("cabextract", "-q", "-d", work, work / "tahoma.tt_", work / "tahomabd.tt_")
            cache.mkdir(parents=True, exist_ok=True)
            for name, signature in FONT_HASHES.items():
                if digest(work / name) != signature:
                    raise ValueError(f"Unexpected font contents for {name}")
                shutil.copy2(work / name, cache / name)
    target.mkdir(parents=True)
    for name in FONT_HASHES:
        shutil.copy2(cache / name, target / name)


def setup_icons(target, work):
    from PIL import Image

    library = work / "shell32.dll"
    download(SHELL32_URL, library, "7c201e812138e2b9cbc2aa94e41d5573775d893b8104833a997acc79486d9a3a")
    originals = target / "original-shell32-ico"
    originals.mkdir(parents=True)
    run("wrestool", "-x", "-t", "14", "-o", originals, library)
    shutil.copy2(REPO / "data/icons.index", target / "index.theme")
    shutil.copy2(REPO / "data/icons.source", target / "SOURCE.txt")
    manifest = json.loads((REPO / "data/icons.json").read_text())
    true_color = work / "true-color"
    true_color.mkdir()
    for resource in (32, 33):
        run("icotool", "-x", "-b", "32", "-o", true_color, originals / f"shell32.dll_14_{resource}.ico")
    for name, entry in manifest.items():
        destination = target / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        if "alias" in entry:
            destination.symlink_to(entry["alias"])
            continue
        size = int(Path(name).parts[0].split("x")[0])
        resource = entry["id"]
        if entry.get("true_color"):
            source = next(true_color.glob(f"shell32.dll_14_{resource}_*_{size}x{size}x32.png"))
            shutil.copy2(source, destination)
        else:
            with Image.open(originals / f"shell32.dll_14_{resource}.ico") as icon:
                icon.ico.getimage((size, size)).convert("RGBA").save(destination)


def dolphin_version():
    result = run("dolphin", "--version", capture=True)
    version = re.search(r"\d+\.\d+\.\d+", result)
    if not version:
        raise ValueError(f"Could not identify the Dolphin version from {result!r}")
    return version.group()


def setup_dolphin(target, work):
    stock = work / "dolphinui.rc"
    url = f"https://raw.githubusercontent.com/KDE/dolphin/v{dolphin_version()}/src/dolphinui.rc"
    download(url, stock)
    gui = ET.parse(stock).getroot()
    toolbar = gui.find("ToolBar[@name='mainToolBar']")
    for child in list(toolbar):
        if child.tag != "text":
            toolbar.remove(child)
    actions = ("go_back", "go_forward", "go_up", "go_home", None, "show_folders_panel",
               "view_mode", "toggle_search", None, "url_navigators")
    properties = gui.find("ActionProperties[@scheme='Default']")
    for name in actions:
        if name is None:
            ET.SubElement(toolbar, "Separator")
            continue
        ET.SubElement(toolbar, "Action", name=name)
        if name != "url_navigators":
            action = properties.find(f"Action[@name='{name}']")
            if action is None:
                action = ET.SubElement(properties, "Action", name=name)
            action.set("priority", "128")
    ET.indent(gui)
    target.parent.mkdir(parents=True)
    target.write_text('<!DOCTYPE gui SYSTEM "kpartgui.dtd">\n' + ET.tostring(gui, encoding="unicode") + "\n")


def stage(target):
    target.mkdir()
    shutil.copytree(REPO / "payload", target, dirs_exist_ok=True)
    with tempfile.TemporaryDirectory() as intermediate:
        work = Path(intermediate)
        reference = work / "xp-desktop.jpg"
        download("https://bootstrike.com/WindowsXP/images/xpshot1.jpg", reference,
                 "88d2b76fc80f8497503f586d4fc318bd3ed05e60308bb0a3510248d23b281be2")
        run("magick", reference, "-gravity", "southwest", "-crop", "115x40+0+0", "+repage",
            "-gravity", "northwest", "-crop", "97x30+0+10", "+repage", target / START)
        download("https://i.kym-cdn.com/photos/images/original/001/334/837/429.png",
                 target / WALLPAPER, "429754afd4199330db87746e96e66d74bb8230c7e92c4476da27a926df0d732c")
        setup_fonts(target / "fonts/WindowsXP")
        setup_icons(target / "icons/WindowsXPOriginal", work)
        setup_dolphin(target / "kxmlgui5/dolphin/dolphinui.rc", work)
    control = target / "desktop-blue/control-panel.py"
    control.parent.mkdir(parents=True)
    shutil.copy2(REPO / "data/control-panel.py", control)
    control.chmod(0o755)
    desktop_entry = target / "applications/desktop-blue-control-panel.desktop"
    desktop_entry.parent.mkdir(parents=True)
    executable = str(DATA / "desktop-blue/control-panel.py")
    desktop_entry.write_text(
        "[Desktop Entry]\nType=Application\nName=Control Panel\n"
        "Comment=Open display, hardware, and system settings\n"
        f'Exec="{executable}"\nIcon=preferences-system\nTerminal=false\n'
        "Categories=Settings;DesktopSettings;\nStartupNotify=true\n"
    )


def dbus(service, path, interface, method, *args, capture=False):
    return run("gdbus", "call", "--session", "--dest", service, "--object-path", path,
               "--method", f"{interface}.{method}", *args, capture=capture)


def evaluate(script, capture=False):
    return dbus(SHELL, "/PlasmaShell", "org.kde.PlasmaShell", "evaluateScript", script, capture=capture)


def favorite(method):
    return dbus("org.kde.ActivityManager", FAVORITES_PATH, "org.kde.ActivityManager.ResourcesLinking",
                method, FAVORITES_AGENT, FAVORITE, ":global", capture=True)


def icon_command():
    candidates = [shutil.which("plasma-changeicons"),
                  "/usr/libexec/plasma-changeicons", "/usr/lib/libexec/plasma-changeicons",
                  "/usr/lib/plasma-changeicons"]
    for candidate in candidates:
        if candidate and os.access(candidate, os.X_OK):
            return candidate
    raise ValueError("Cannot find Plasma's plasma-changeicons helper.")


def active_plasma():
    if run("systemctl", "--user", "show", "-p", "ActiveState", "--value",
           "plasma-plasmashell.service", capture=True).strip() != "active":
        raise ValueError("An active systemd-managed Plasma session is required.")
    evaluate("print(panels().length);", capture=True)


def check():
    commands = ("curl", "7z", "cabextract", "wrestool", "icotool", "magick",
                "dolphin", "konsole", "kwriteconfig6", "kbuildsycoca6", "fc-cache", "qtpaths6",
                "xdg-user-dir", "plasma-apply-desktoptheme", "plasma-apply-colorscheme",
                "plasma-apply-wallpaperimage", "gdbus", "kcmshell6", "plasmashell")
    missing = [command for command in commands if not shutil.which(command)]
    if missing:
        raise ValueError("Missing commands: " + ", ".join(missing))
    import PIL  # noqa: F401
    import gi
    gi.require_version("Gtk", "3.0")
    from gi.repository import Gtk  # noqa: F401
    version = run("plasmashell", "--version", capture=True).strip()
    match = re.search(r"(\d+)\.(\d+)\.(\d+)", version)
    if not match or not (tuple(map(int, match.groups())) >= (6, 8, 0) and match[1] == "6"):
        raise ValueError(f"Plasma 6.8 or newer in the Plasma 6 series is required. Detected {version}.")
    icon_command()
    plugin_dir = Path(run("qtpaths6", "--plugin-dir", capture=True).strip())
    for plugin in ("org.kde.kdecoration3/org.kde.kwin.aurorae.v2.so", "styles/oxygen6.so"):
        if not (plugin_dir / plugin).is_file():
            raise ValueError(f"Required KDE plugin is unavailable: {plugin}")
    print(f"{version}, Dolphin {dolphin_version()}. Required commands and Python libraries found.")


def config(file, groups, key, value):
    file.parent.mkdir(parents=True, exist_ok=True)
    arguments = ["kwriteconfig6", "--file", file]
    for group in groups:
        arguments.extend(("--group", group))
    run(*arguments, "--key", key, value)


def apply_configuration(shortcut):
    run("fc-cache", "-f", DATA / "fonts/WindowsXP")
    run("plasma-apply-colorscheme", "DesktopBlue")
    run("plasma-apply-desktoptheme", "desktop-blue")
    run(icon_command(), "WindowsXPOriginal")
    regular = "Tahoma,10,-1,5,50,0,0,0,0,0"
    for role in ("font", "menuFont", "toolBarFont"):
        config(CONFIG / "kdeglobals", ("General",), role, regular)
    config(CONFIG / "kdeglobals", ("General",), "smallestReadableFont", "Tahoma,9,-1,5,50,0,0,0,0,0")
    config(CONFIG / "kdeglobals", ("WM",), "activeFont", "Tahoma,10,-1,5,75,0,0,0,0,0")
    config(CONFIG / "kdeglobals", ("KDE",), "widgetStyle", "Oxygen")
    for version in (3, 4):
        config(CONFIG / f"gtk-{version}.0/settings.ini", ("Settings",), "gtk-font-name", "Tahoma 10")
    gtk2 = HOME / ".gtkrc-2.0"
    current = gtk2.read_text() if gtk2.exists() else ""
    cleaned = re.sub(r'^gtk-font-name\s*=.*\n?', '', current, flags=re.M)
    gtk2.write_text(cleaned + '\ngtk-font-name="Tahoma 10"\n')
    configure_kwin()
    wallpaper = (DATA / LOCKSCREEN).as_uri()
    config(CONFIG / "kscreenlockerrc", ("Greeter",), "WallpaperPlugin", "org.kde.image")
    for key in ("Image", "PreviewImage"):
        config(CONFIG / "kscreenlockerrc", ("Greeter", "Wallpaper", "org.kde.image", "General"), key, wallpaper)

    config(CONFIG / "konsolerc", ("Desktop Entry",), "DefaultProfile", "ClassicCmd.profile")
    config(CONFIG / "dolphinrc", ("MainWindow",), "MenuBar", "Enabled")
    config(CONFIG / "dolphinrc", ("MainWindow", "Toolbar mainToolBar"), "ToolButtonStyle", "TextUnderIcon")
    config(CONFIG / "dolphinrc", ("General",), "EditableUrl", "true")
    config(CONFIG / "dolphinrc", ("General",), "ShowStatusBar", "1")
    shutil.copy2(REPO / "data/recycle-bin.desktop", shortcut)
    run("kbuildsycoca6")
    favorite("LinkResourceToActivity")

    xdg_app_dirs = os.environ.get("XDG_DATA_DIRS", "/usr/local/share:/usr/share").split(":")
    zen = "app.zen_browser.zen.desktop"
    browser = next((f"applications:{zen}" for directory in (DATA, *map(Path, xdg_app_dirs))
                    if (directory / "applications" / zen).is_file()), "preferred://browser")
    assets = {"startButton": str(DATA / START),
              "launchers": f"{browser},preferred://filemanager,applications:systemsettings.desktop"}
    response = evaluate(
        "const assets = " + json.dumps(assets) + ";\n" + (REPO / "data/panel.js").read_text(),
        capture=True,
    )
    layout = json.loads(ast.literal_eval(response.strip())[0])
    run("plasma-apply-wallpaperimage", DATA / WALLPAPER)
    refresh(layout)
    verify_panel(layout)



def configure_kwin():
    settings = {
        "library": "org.kde.kwin.aurorae.v2", "theme": "__aurorae__svg__DesktopBlue",
        "ButtonsOnLeft": "M", "ButtonsOnRight": "IAX",
    }
    for key, value in settings.items():
        config(CONFIG / "kwinrc", ("org.kde.kdecoration2",), key, value)


def refresh(layout):
    run("systemctl", "--user", "stop", "plasma-plasmashell.service")
    try:
        tray_config = ("Containments", str(layout["panel"]), "Applets", str(layout["tray"]), "General")
        applets_file = CONFIG / "plasma-org.kde.plasma.desktop-appletsrc"
        config(applets_file, tray_config, "showAllItems", "false")
        config(applets_file, tray_config, "hiddenItems", ",".join(TRAY_HIDDEN))
    finally:
        run("systemctl", "--user", "start", "plasma-plasmashell.service")
    dbus("org.kde.KWin", "/KWin", "org.kde.KWin", "reconfigure")
    run("gdbus", "emit", "--session", "--object-path", "/KDEPlatformTheme",
        "--signal", "org.kde.KDEPlatformTheme.refreshFonts")
    xwayland = Path(icon_command()).with_name("plasma-setup-xwayland")
    if xwayland.is_file():
        run(xwayland)


def verify_panel(layout):
    script = f"""
const panel = panelById({layout["panel"]});
const launcher = panel.widgetById({layout["launcher"]});
print(launcher && launcher.geometry.width > 60 && panel.lengthMode === "fill");
"""
    for _ in range(20):
        try:
            if "true" in evaluate(script, capture=True):
                return
        except subprocess.CalledProcessError:
            pass
        time.sleep(0.5)
    raise ValueError("The reloaded panel did not report a working wide Start button.")


def snapshot(paths):
    STATE.mkdir(parents=True, exist_ok=True, mode=0o700)
    manifest = STATE / "backup.json"
    if manifest.exists():
        print(f"Keeping the original restore point at {STATE}.")
        return
    with tempfile.TemporaryDirectory(dir=STATE) as intermediate:
        work = Path(intermediate)
        saved = work / "files"
        saved.mkdir()
        recorded = []
        for index, path in enumerate(paths):
            present = path.exists() or path.is_symlink()
            recorded.append({"path": str(path), "present": present})
            if present:
                copy_path(path, saved / str(index))
        linked = "true" in favorite("IsResourceLinkedToActivity")
        if (STATE / "files").exists():
            raise ValueError(f"Incomplete prior snapshot in {STATE}; inspect it before reinstalling.")
        saved.replace(STATE / "files")
        (work / "backup.json").write_text(json.dumps({"files": recorded, "favorite": linked}, indent=2))
        (work / "backup.json").replace(manifest)


def copy_path(source, destination):
    if source.is_dir() and not source.is_symlink():
        shutil.copytree(source, destination, symlinks=True)
    else:
        shutil.copy2(source, destination, follow_symlinks=False)


def remove_path(path):
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)


def restore():
    manifest = STATE / "backup.json"
    if not manifest.exists():
        raise ValueError(f"No restore point found at {STATE}.")
    active_plasma()
    snapshot = json.loads(manifest.read_text())
    if not snapshot["favorite"]:
        favorite("UnlinkResourceFromActivity")
    run("systemctl", "--user", "stop", "plasma-plasmashell.service")
    try:
        for index, item in enumerate(snapshot["files"]):
            path = Path(item["path"])
            remove_path(path)
            if item["present"]:
                path.parent.mkdir(parents=True, exist_ok=True)
                copy_path(STATE / "files" / str(index), path)
    finally:
        run("systemctl", "--user", "start", "plasma-plasmashell.service")
    run("fc-cache", "-f")
    run("kbuildsycoca6")
    dbus("org.kde.KWin", "/KWin", "org.kde.KWin", "reconfigure")
    run("gdbus", "emit", "--session", "--object-path", "/KDEPlatformTheme",
        "--signal", "org.kde.KDEPlatformTheme.refreshFonts")
    print(f"Restored the pre-install settings from {STATE}.")


def install():
    check()
    active_plasma()
    desktop = Path(run("xdg-user-dir", "DESKTOP", capture=True).strip())
    if not desktop.is_absolute() or desktop == HOME:
        raise ValueError("A dedicated XDG Desktop directory is needed for the Recycle Bin.")
    shortcut = desktop / "trash:⁄.desktop"
    gtk2 = HOME / ".gtkrc-2.0"
    with tempfile.TemporaryDirectory() as intermediate:
        target = Path(intermediate) / "payload"
        stage(target)
        destinations = [DATA / asset for asset in ASSETS]
        paths = destinations + [CONFIG / name for name in CONFIG_FILES] + [shortcut, gtk2]
        snapshot(paths)
        try:
            for asset, destination in zip(ASSETS, destinations):
                remove_path(destination)
                destination.parent.mkdir(parents=True, exist_ok=True)
                copy_path(target / asset, destination)
            desktop.mkdir(parents=True, exist_ok=True)
            apply_configuration(shortcut)
        except (OSError, ValueError, subprocess.CalledProcessError):
            print(f"Installation was interrupted. Run {REPO / 'install.py'} --restore to recover.", file=sys.stderr)
            raise
    print("Desktop Blue is installed. Reopen any apps that still show their previous fonts.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="check dependencies without changing the session")
    mode.add_argument("--stage", type=Path, metavar="DIR", help="assemble theme files in a new directory")
    mode.add_argument("--restore", action="store_true", help="restore the original user's desktop settings")
    options = parser.parse_args()
    if os.geteuid() == 0:
        parser.error("Run as the desktop user.")
    if options.check:
        check()
    elif options.stage:
        check()
        stage(options.stage)
        print(f"Staged assets at {options.stage}. No desktop settings changed.")
    elif options.restore:
        restore()
    else:
        install()


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, ImportError, subprocess.CalledProcessError) as error:
        print(f"Desktop Blue: {error}", file=sys.stderr)
        raise SystemExit(1)
