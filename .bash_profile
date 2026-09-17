# Preserve login initialization both inside and outside tmux.
# Ubuntu's default .profile also loads .bashrc; avoid loading it twice.
_dotfiles_login_startup=1
unset _dotfiles_login_bashrc_loaded
if [ -r "$HOME/.profile" ]; then
    . "$HOME/.profile"
fi
if [ "${_dotfiles_login_bashrc_loaded-}" != 1 ] && [ -r "$HOME/.bashrc" ]; then
    . "$HOME/.bashrc"
fi
unset _dotfiles_login_startup _dotfiles_login_bashrc_loaded
