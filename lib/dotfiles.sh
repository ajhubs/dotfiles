# Shared by install.sh and uninstall.sh; requires Bash and GNU coreutils.
# Explicit list prevents unrelated dotfiles in the checkout being installed.
dotfiles=(.bash_aliases .bash_exports .bash_profile .bash_wrappers .bashrc .screenrc .tmux.conf .vimrc)

fail() {
    printf 'Error: %s\n' "$*" >&2
    exit 1
}

exists() {
    [[ -e "$1" || -L "$1" ]]
}

owned_link() {
    local target
    [[ -L "$1" ]] || return 1
    # Read through NUL so trailing newlines remain part of the link target.
    IFS= read -r -d '' target < <(readlink -z -- "$1") || return 1
    [[ "$target" == "$2" ]]
}

move_without_overwrite() {
    # GNU mv -n can return success when it skips a destination. Verify the move.
    exists "$2" && fail "Refusing to overwrite: $2"
    mv -Tn -- "$1" "$2" || fail "Could not move: $1"
    exists "$1" && fail "Move was skipped; preserved: $1"
    return 0
}

lock_home() {
    [[ -n "${HOME:-}" && -d "$HOME" ]] || fail 'HOME must name an existing directory.'
    HOME=$(cd -- "$HOME" && pwd -P)
    [[ "$HOME" != "$script_dir" ]] || fail 'Keep this checkout in its own directory, not directly in HOME.'
    lock_dir="$HOME/.dotfiles-install.lock"
    (umask 077; mkdir -- "$lock_dir") || fail "Another operation or stale lock exists: $lock_dir"
    trap 'rmdir -- "$lock_dir"' EXIT
    trap 'exit 130' INT
    trap 'exit 143' TERM
}
