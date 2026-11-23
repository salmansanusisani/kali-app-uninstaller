#!/bin/sh
set -eu

project_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
build_dir=$(mktemp -d)
trap 'rm -rf "$build_dir"' EXIT
architecture=$(dpkg --print-architecture)
package_dir="$build_dir/kali-uninstaller_1.0.0_${architecture}"

pyinstaller --noconfirm --clean --onefile --windowed \
  --name kali-uninstaller \
  --distpath "$build_dir/dist" \
  --workpath "$build_dir/work" \
  --specpath "$build_dir" \
  "$project_dir/kali-uninstaller.py"

install -Dm755 "$build_dir/dist/kali-uninstaller" "$package_dir/usr/bin/kali-uninstaller"
install -Dm644 "$project_dir/kali-uninstaller.desktop" "$package_dir/usr/share/applications/kali-uninstaller.desktop"
install -Dm644 "$project_dir/kali-uninstaller.svg" "$package_dir/usr/share/icons/hicolor/scalable/apps/kali-uninstaller.svg"
install -d "$package_dir/DEBIAN"
cat > "$package_dir/DEBIAN/control" <<EOF
Package: kali-uninstaller
Version: 1.0.0
Section: admin
Priority: optional
Architecture: $architecture
Depends: apt, policykit-1
Maintainer: Local User
Description: A simple graphical uninstaller for Kali Linux desktop apps
EOF

dpkg-deb --build --root-owner-group "$package_dir" "$project_dir/kali-uninstaller_1.0.0_${architecture}.deb"
echo "Package created: $project_dir/kali-uninstaller_1.0.0_${architecture}.deb"
