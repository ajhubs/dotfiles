#!/bin/bash
set -euo pipefail

root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)
scratch=$(mktemp -d -t dotfiles-test.XXXXXXXX)
printf 'Test fixtures: %s\n' "$scratch"
repo="$scratch/checkout with spaces"
mkdir -p -- "$repo/lib" "$scratch/unrelated" "$scratch/bin"
cp -- "$root/install.sh" "$root/uninstall.sh" "$repo/"
cp -- "$root/lib/dotfiles.sh" "$repo/lib/"
cp -- "$root"/.bash* "$root/.screenrc" "$root/.tmux.conf" "$root/.vimrc" "$repo/"
printf 'not a config\n' > "$repo/.extra"
printf 'untrusted cwd\n' > "$scratch/unrelated/.bashrc"
printf '#!/bin/bash\nexit 99\n' > "$scratch/bin/sudo"
chmod +x "$scratch/bin/sudo"
export PATH="$scratch/bin:$PATH"
cd -- "$scratch/unrelated"

check() { "$@" || { printf 'FAILED: %s\n' "$*" >&2; exit 1; }; }
reject() { if "$@"; then printf 'Unexpected success: %s\n' "$*" >&2; exit 1; fi; }
new_home() { export HOME="$scratch/$1"; mkdir -- "$HOME"; }
install() { bash "$repo/install.sh"; }
uninstall() { bash "$repo/uninstall.sh"; }

new_home 'home with spaces'
printf 'original\n' > "$HOME/.bashrc"
install
check test -L "$HOME/.bashrc"
check test "$(readlink -- "$HOME/.bashrc")" = "$repo/.bashrc"
check test "$(cat -- "$HOME/.bashrc.dtbak")" = original
check test ! -e "$HOME/.extra"
install
check test ! -L "$HOME/.bashrc.dtbak"
check test "$(cat -- "$HOME/.bashrc.dtbak")" = original
uninstall
check test ! -L "$HOME/.bashrc"
check test "$(cat -- "$HOME/.bashrc")" = original
check test ! -e "$HOME/.bashrc.dtbak"
check test ! -e "$HOME/.vimrc"

new_home 'backup conflict'
printf 'original\n' > "$HOME/.bashrc"
printf 'precious backup\n' > "$HOME/.vimrc.dtbak"
reject install
check test "$(cat -- "$HOME/.bashrc")" = original
check test "$(cat -- "$HOME/.vimrc.dtbak")" = 'precious backup'
check test ! -e "$HOME/.bash_aliases"
check test ! -e "$HOME/.dotfiles-install.lock"

new_home 'broken original link'
ln -s -- "$scratch/missing-target" "$HOME/.bashrc"
install
check test -L "$HOME/.bashrc.dtbak"
uninstall
check test -L "$HOME/.bashrc"
check test "$(readlink -- "$HOME/.bashrc")" = "$scratch/missing-target"

new_home 'changed configuration'
printf 'original\n' > "$HOME/.bashrc"
install
rm -- "$HOME/.bashrc"
ln -s -- "$scratch/unrelated/.bashrc" "$HOME/.bashrc"
rm -- "$HOME/.vimrc"
printf 'new vim config\n' > "$HOME/.vimrc"
reject uninstall
check test "$(readlink -- "$HOME/.bashrc")" = "$scratch/unrelated/.bashrc"
check test "$(cat -- "$HOME/.bashrc.dtbak")" = original
check test "$(cat -- "$HOME/.vimrc")" = 'new vim config'

new_home 'locked'
mkdir -- "$HOME/.dotfiles-install.lock"
reject install
check test -d "$HOME/.dotfiles-install.lock"
check test ! -e "$HOME/.bashrc"

new_home 'link failure'
printf 'original alias\n' > "$HOME/.bash_aliases"
printf '#!/bin/bash\nexit 1\n' > "$scratch/bin/ln"
chmod +x "$scratch/bin/ln"
reject install
check test "$(cat -- "$HOME/.bash_aliases")" = 'original alias'
check test ! -e "$HOME/.bash_aliases.dtbak"
check test ! -e "$HOME/.dotfiles-install.lock"
rm -- "$scratch/bin/ln"

new_home 'directory conflict'
mkdir -- "$HOME/.vimrc"
reject install
check test -d "$HOME/.vimrc"
check test ! -e "$HOME/.bashrc"

HOME="$repo" reject install
printf 'PASS: install/uninstall security regression checks\n'
