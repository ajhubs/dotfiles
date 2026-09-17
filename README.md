# Installation
### Download and change folder
```
cd ~
git clone https://github.com/ajhubs/dotfiles.git

cd dotfiles
```
### Run install
```
./install.sh
```

Requires Bash and GNU coreutils (as provided by Ubuntu). Keep the checkout in
its own directory. Both scripts locate files relative to themselves, so they
can also be invoked by absolute path from another directory.

Existing configuration is preserved as `~/<filename>.dtbak`. Re-running the
installer skips links already pointing to this checkout. If a backup already
exists for any other destination, installation stops before making changes;
review the existing file and backup manually. Do not delete the backup unless
you no longer need it. Concurrent installer/uninstaller runs are blocked by
`~/.dotfiles-install.lock`. After an interrupted process, remove that empty
directory only after confirming neither script is still running.

The installer does not install system packages. Optional Vim scripts can be
installed separately:

```sh
sudo apt update && sudo apt install vim-scripts
```

The Vim `:w!!` shortcut shell-escapes the full filename and passes it after `--`
to `tee`, so spaces and shell metacharacters are treated as filename content.

The custom visual-selection `*` / `#` mappings and `<leader>te` shortcut have
been removed: they could interpret crafted selected text or directory names
as Vim commands. The `VisualSelection` and `CmdLine` helpers are also removed.
Use Vim's built-in searches and `:tabedit` with filename completion instead.
Restart Vim after updating so previously loaded mappings are discarded.
NERDTree opens on an empty startup only if the plugin is available; it is optional.

Login shells load your readable `~/.profile` inside and outside tmux. Interactive
shells also load `.bashrc`, avoiding a duplicate load when `.profile` already
sources it. You can still source `.bashrc` manually to reload settings.

These are per-user dotfiles. Root must not load configuration or plugins from
a checkout writable by another user. A shared root configuration requires
root-controlled files and parent directories; the installer does not change
ownership or audit an existing shared installation.

# Uninstallation

### Change to dotfiles folder
```
cd ~/dotfiles
```

### Run uninstaller
```
./uninstall.sh
```

Only links pointing to this checkout are removed, then their backups are
restored. Files or links changed by another tool are left untouched, together
with their backups, and the command exits with an error for manual review.

### Regression checks

Run from the checkout on Linux with Bash, GNU coreutils, Python 3 and Vim:

```sh
bash tests/install.sh
python3 tests/bash-startup.py
python3 tests/vim-save.py
python3 tests/vim-shortcuts.py
python3 tests/vim-startup.py
```

Tests use temporary homes and a harmless `sudo` substitute; they do not modify
your home configuration or request administrator access.
