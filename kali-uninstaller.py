#!/usr/bin/env python3
"""A small, safe GTK interface for removing manually installed APT packages."""

import subprocess
import threading
from pathlib import Path

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import GLib, Gtk, Pango


APP_NAME = "Kali Uninstaller"


class PackageRow(Gtk.ListBoxRow):
    def __init__(self, package, name, description, icon_name):
        super().__init__()
        self.package = package
        self.search_text = f"{package} {name} {description}".lower()

        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        box.set_border_width(12)
        self.check = Gtk.ToggleButton(label="Select")
        self.check.set_relief(Gtk.ReliefStyle.NORMAL)
        self.check.connect("toggled", self.on_toggled)
        box.pack_start(self.check, False, False, 0)

        icon = Gtk.Image()
        if icon_name and icon_name.startswith("/") and Path(icon_name).is_file():
            icon.set_from_file(icon_name)
        elif icon_name:
            icon.set_from_icon_name(icon_name, Gtk.IconSize.DIALOG)
        else:
            icon.set_from_icon_name("application-x-executable", Gtk.IconSize.DIALOG)
        icon.set_pixel_size(40)
        box.pack_start(icon, False, False, 0)

        labels = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        title = Gtk.Label(label=name, xalign=0)
        title.get_style_context().add_class("package-name")
        detail_text = description or package
        if description:
            detail_text = f"{package} — {description}"
        detail = Gtk.Label(label=detail_text, xalign=0)
        detail.set_ellipsize(Pango.EllipsizeMode.END)
        detail.get_style_context().add_class("package-detail")
        labels.pack_start(title, False, False, 0)
        labels.pack_start(detail, False, False, 0)
        box.pack_start(labels, True, True, 0)
        self.add(box)

    def on_toggled(self, button):
        button.set_label("Selected" if button.get_active() else "Select")
        window = self.get_toplevel()
        if hasattr(window, "update_selection"):
            window.update_selection()


class Uninstaller(Gtk.Window):
    def __init__(self):
        super().__init__(title=APP_NAME)
        self.set_default_size(780, 620)
        self.set_border_width(22)
        self.rows = []

        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        self.add(outer)

        title = Gtk.Label(xalign=0)
        title.set_markup("<span size='22000' weight='bold'>Manage installed apps</span>")
        subtitle = Gtk.Label(
            label="Select manually installed APT packages to remove. System dependencies are not shown.",
            xalign=0,
        )
        subtitle.get_style_context().add_class("subtitle")
        outer.pack_start(title, False, False, 0)
        outer.pack_start(subtitle, False, False, 0)

        self.search = Gtk.SearchEntry(placeholder_text="Search installed apps")
        self.search.connect("search-changed", self.filter_rows)
        outer.pack_start(self.search, False, False, 0)

        self.listbox = Gtk.ListBox(selection_mode=Gtk.SelectionMode.NONE)
        self.listbox.set_filter_func(self.row_visible)
        scroller = Gtk.ScrolledWindow()
        scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroller.add(self.listbox)
        outer.pack_start(scroller, True, True, 0)

        footer = Gtk.Box(spacing=10)
        self.status = Gtk.Label(label="Loading installed packages…", xalign=0)
        footer.pack_start(self.status, True, True, 0)
        self.remove_button = Gtk.Button(label="Remove selected")
        self.remove_button.get_style_context().add_class("destructive-action")
        self.remove_button.set_sensitive(False)
        self.remove_button.connect("clicked", self.confirm_removal)
        footer.pack_end(self.remove_button, False, False, 0)
        outer.pack_start(footer, False, False, 0)

        self.apply_css()
        threading.Thread(target=self.load_packages, daemon=True).start()

    def apply_css(self):
        provider = Gtk.CssProvider()
        provider.load_from_data(b"""
            window { background: #f5f8f6; color: #20302a; }
            entry { color: #20302a; caret-color: #20302a; border-radius: 10px; padding: 9px; border: 1px solid #cbd9d1; background: white; }
            entry selection { color: white; background-color: #4e9270; }
            list { background: white; border-radius: 12px; }
            row { border-bottom: 1px solid #edf1ee; }
            row:hover { background: #edf7f0; }
            .subtitle, .package-detail { color: #64756c; }
            .package-name { color: #20302a; font-weight: 600; }
            .destructive-action { background: #b54545; color: white; border-radius: 8px; padding: 8px 14px; }
        """)
        Gtk.StyleContext.add_provider_for_screen(
            self.get_screen(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def load_packages(self):
        try:
            manual_packages = set(subprocess.check_output(
                ["apt-mark", "showmanual"], text=True, stderr=subprocess.PIPE
            ).splitlines())
            result = subprocess.run(
                ["dpkg-query", "-W", "-f=${binary:Package}\t${db:Status-Abbrev}\t${binary:Summary}\n"],
                text=True, capture_output=True, check=True,
            )
            installed_packages = {}
            for line in result.stdout.splitlines():
                fields = line.split("\t", 2)
                if len(fields) == 3 and fields[1].startswith("ii"):
                    package = fields[0].split(":", 1)[0]
                    if package in manual_packages:
                        installed_packages[package] = fields[2]

            desktop_files = list(Path("/usr/share/applications").glob("*.desktop"))
            if desktop_files:
                ownership = subprocess.run(
                    ["dpkg-query", "-S", *map(str, desktop_files)],
                    text=True, capture_output=True, check=False,
                ).stdout
                owners = {}
                for line in ownership.splitlines():
                    if ": " in line:
                        owner, path = line.split(": ", 1)
                        owners[path] = owner.split(",", 1)[0].split(":", 1)[0]
                apps = []
                for desktop_file in desktop_files:
                    package = owners.get(str(desktop_file))
                    if package not in installed_packages:
                        continue
                    key_file = GLib.KeyFile()
                    try:
                        key_file.load_from_file(str(desktop_file), GLib.KeyFileFlags.NONE)
                        try:
                            no_display = key_file.get_boolean("Desktop Entry", "NoDisplay")
                        except GLib.Error:
                            no_display = False
                        if no_display:
                            continue
                        name = key_file.get_locale_string("Desktop Entry", "Name", None)
                        icon = key_file.get_string("Desktop Entry", "Icon")
                    except GLib.Error:
                        continue
                    apps.append((package, name, installed_packages[package], icon))
                GLib.idle_add(self.populate, apps)
            else:
                GLib.idle_add(self.populate, [])
        except (OSError, subprocess.CalledProcessError) as error:
            GLib.idle_add(self.show_error, f"Could not read installed packages: {error}")

    def populate(self, apps):
        for package, name, description, icon in sorted(apps, key=lambda app: app[1].lower()):
            row = PackageRow(package, name, description, icon)
            self.rows.append(row)
            self.listbox.add(row)
        self.listbox.show_all()
        self.status.set_text(f"{len(self.rows)} installed apps")

    def show_error(self, message):
        self.status.set_text(message)

    def row_visible(self, row):
        return self.search.get_text().lower() in row.search_text

    def filter_rows(self, *_):
        self.listbox.invalidate_filter()

    def selected_packages(self):
        return [row.package for row in self.rows if row.check.get_active()]

    def update_selection(self):
        selected = self.selected_packages()
        self.remove_button.set_sensitive(bool(selected))
        self.status.set_text(
            f"{len(selected)} package{'s' if len(selected) != 1 else ''} selected"
            if selected else f"{len(self.rows)} installed apps"
        )

    def confirm_removal(self, *_):
        packages = self.selected_packages()
        dialog = Gtk.MessageDialog(
            transient_for=self, modal=True, message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.CANCEL,
            text=f"Remove {len(packages)} selected package(s)?",
        )
        dialog.format_secondary_text(
            "APT will show its final removal plan and ask for administrator approval. "
            "Your package configuration files will be kept."
        )
        dialog.add_button("Remove packages", Gtk.ResponseType.OK)
        response = dialog.run()
        dialog.destroy()
        if response == Gtk.ResponseType.OK:
            self.run_removal(packages)

    def run_removal(self, packages):
        self.remove_button.set_sensitive(False)
        self.status.set_text("Waiting for administrator approval…")
        threading.Thread(target=self.remove_packages, args=(packages,), daemon=True).start()

    def remove_packages(self, packages):
        result = subprocess.run(["pkexec", "apt", "remove", *packages])
        GLib.idle_add(self.removal_finished, result.returncode)

    def removal_finished(self, returncode):
        if returncode == 0:
            self.status.set_text("Removal completed. Restart the app to refresh the list.")
            for row in self.rows:
                row.check.set_sensitive(False)
        else:
            self.status.set_text("Removal was cancelled or did not finish. No refresh was made.")
            self.update_selection()


if __name__ == "__main__":
    window = Uninstaller()
    window.connect("destroy", Gtk.main_quit)
    window.show_all()
    Gtk.main()
