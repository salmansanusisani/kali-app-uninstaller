# Kali Uninstaller

A small GTK app for Kali Linux that shows manually installed desktop apps with their supplied icons, then lets you remove selected packages using the normal APT confirmation screen. It includes an application-menu icon.

## Run without installing

```sh
python3 kali-uninstaller.py
```

## Install into the application menu

```sh
sudo ./install.sh
```

The app uses `pkexec` only after you select packages and confirm removal. It uses `apt remove`, which keeps configuration files; it never runs `autoremove` automatically.

## Build an installable application package

```sh
./package-deb.sh
sudo apt install ./kali-uninstaller_1.0.0_amd64.deb
```

This produces a native Kali/Debian application package. The package adds the app and icon to your Applications menu.

`build-deb.sh` is also included when you specifically want a standalone PyInstaller-compiled binary package; it takes considerably longer to build.
