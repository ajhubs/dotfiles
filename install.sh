#!/bin/bash
set -euo pipefail

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
source "$script_dir/lib/dotfiles.sh"
lock_home

# Check every destination before changing anything.
for file in "${dotfiles[@]}"; do
    source_file="$script_dir/$file"
    destination="$HOME/$file"
    [[ -f "$source_file" && ! -L "$source_file" ]] || fail "Invalid source: $source_file"
    owned_link "$destination" "$source_file" && continue
    exists "$destination.dtbak" && fail "Backup already exists; resolve manually: $destination.dtbak"
    [[ -d "$destination" && ! -L "$destination" ]] && fail "Refusing to replace directory: $destination"
done

for file in "${dotfiles[@]}"; do
    source_file="$script_dir/$file"
    destination="$HOME/$file"
    if owned_link "$destination" "$source_file"; then
        printf 'Already installed: %s\n' "$file"
        continue
    fi
    backed_up=false
    if exists "$destination"; then
        move_without_overwrite "$destination" "$destination.dtbak"
        backed_up=true
    fi
    if ! ln -sT -- "$source_file" "$destination"; then
        if "$backed_up"; then
            move_without_overwrite "$destination.dtbak" "$destination"
        fi
        fail "Could not install: $destination"
    fi
    printf 'Installed: %s\n' "$file"
done

printf 'Installed. Optional Vim packages: sudo apt update && sudo apt install vim-scripts\n'
