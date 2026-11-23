#!/bin/sh
set -eu

project_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
build_dir=$(mktemp -d)
trap 'rm -rf "$build_dir"' EXIT
architecture=$(dpkg --print-architecture)
package_dir="$build_dir/kali-uninstaller_1.0.0_${architecture}"

install -Dm755 "$project_dir/kali-uninstaller.py" "$package_dir/usr/bin/kali-uninstaller"
install -Dm644 "$project_dir/kali-uninstaller.desktop" "$package_dir/usr/share/applications/kali-uninstaller.desktop"
install -Dm644 "$project_dir/kali-uninstaller.svg" "$package_dir/usr/share/icons/hicolor/scalable/apps/kali-uninstaller.svg"
install -d "$package_dir/DEBIAN"
cat > "$package_dir/DEBIAN/control" <<EOF
Package: kali-uninstaller
Version: 1.0.0
Section: admin
Priority: optional
Architecture: $architecture
Depends: python3, python3-gi, gir1.2-gtk-3.0, apt, policykit-1
Maintainer: Local User
Description: A simple graphical uninstaller for Kali Linux desktop apps
EOF

dpkg-deb --build --root-owner-group "$package_dir" "$project_dir/kali-uninstaller_1.0.0_${architecture}.deb"
echo "Package created: $project_dir/kali-uninstaller_1.0.0_${architecture}.deb"
