#!/bin/bash
set -euo pipefail

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
source "$script_dir/lib/dotfiles.sh"
lock_home

conflicts=0
for file in "${dotfiles[@]}"; do
    destination="$HOME/$file"
    if ! owned_link "$destination" "$script_dir/$file"; then
        if exists "$destination" || exists "$destination.dtbak"; then
            printf 'Left unchanged (not a link to this checkout): %s\n' "$destination" >&2
            conflicts=1
        fi
        continue
    fi
    rm -- "$destination"
    if exists "$destination.dtbak"; then
        move_without_overwrite "$destination.dtbak" "$destination"
    fi
    printf 'Uninstalled: %s\n' "$file"
done

if (( conflicts )); then
    fail 'Some files were left unchanged. Review them and their backups manually.'
fi
printf 'Uninstalled.\n'
