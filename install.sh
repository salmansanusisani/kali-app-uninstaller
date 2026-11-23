#!/bin/sh
set -eu

install -Dm755 kali-uninstaller.py /usr/bin/kali-uninstaller
install -Dm644 kali-uninstaller.svg /usr/share/icons/hicolor/scalable/apps/kali-uninstaller.svg
install -Dm644 kali-uninstaller.desktop /usr/share/applications/kali-uninstaller.desktop
echo "Installed Kali Uninstaller. Open it from the application menu."
