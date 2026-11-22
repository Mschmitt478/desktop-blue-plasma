const panel = panels().find(candidate => candidate.screen === 0 && candidate.location === "bottom")
    || panels().find(candidate => candidate.screen === 0)
    || new Panel;

const launcherType = "org.kde.plasma.kicker";
const taskType = "org.kde.plasma.taskmanager";
const trayType = "org.kde.plasma.systemtray";
const clockType = "org.kde.plasma.digitalclock";

function widget(type) {
    const result = panel.widgets(type)[0] || panel.addWidget(type);
    if (!result) throw Error("Unable to load " + type);
    return result;
}

function configure(applet, group, settings) {
    applet.currentConfigGroup = [group];
    for (const [key, value] of Object.entries(settings)) applet.writeConfig(key, value);
    applet.reloadConfig();
}

const launcher = widget(launcherType);
const tasks = widget(taskType);
const tray = widget(trayType);
const clock = widget(clockType);
const keep = [launcher.id, tasks.id, tray.id, clock.id];
const oldLauncher = panel.widgets("org.kde.plasma.kickoff")[0];
const shortcut = oldLauncher ? oldLauncher.globalShortcut : "";

configure(launcher, "General", {
    icon: "start-here-kde-symbolic",
    customButtonImage: assets.startButton,
    useCustomButtonImage: true,
    showIconsRootLevel: true,
    showRecentFolders: true,
});
configure(tasks, "General", {
    launchers: assets.launchers,
    groupingStrategy: 0,
    separateLaunchers: true,
    maxStripes: 1,
});
configure(clock, "Appearance", {
    showDate: false,
    autoFontAndSize: false,
    fontFamily: "Tahoma",
    fontSize: 10,
    fontStyleName: "Regular",
    use24hFormat: 0,
});

for (const applet of panel.widgets()) {
    if (!keep.includes(applet.id)) applet.remove();
}
[launcher, tasks, tray, clock].forEach((applet, index) => { applet.index = index; });
if (shortcut) launcher.globalShortcut = shortcut;

panel.location = "bottom";
panel.floating = false;
panel.lengthMode = "fill";
panel.height = 32;
for (const desktop of desktops()) {
    for (const clock of desktop.widgets(clockType)) clock.remove();
}
print(JSON.stringify({ panel: panel.id, launcher: launcher.id, tray: tray.id }));
