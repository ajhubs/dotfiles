"""Exercise login-profile contents with temporary homes and interactive Bash."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[1])
args = parser.parse_args()
bash = os.environ.get('BASH_TEST_BIN') or shutil.which('bash')
assert bash, 'Bash is required'

cases = [
    ('profile loads bashrc', "export PROFILE_MARKER=loaded\n. \"$HOME/.bashrc\"\n", True),
    ('profile without bashrc', 'export PROFILE_MARKER=loaded\n', True),
    ('missing profile', None, True),
    ('missing bashrc', 'export PROFILE_MARKER=loaded\n', False),
]
for name, profile, have_bashrc in cases:
    for tmux in (False, True):
        with tempfile.TemporaryDirectory(prefix='dotfiles bash startup ') as directory:
            scratch = Path(directory)
            for file in ('.bash_profile', '.bashrc'):
                if file == '.bashrc' and not have_bashrc:
                    continue
                content = (args.repo / file).read_bytes().replace(b'\r\n', b'\n')
                if file == '.bashrc':
                    content += b'\nRC_COUNT=$(( ${RC_COUNT:-0} + 1 ))\n'
                (scratch / file).write_bytes(content)
            if profile is not None:
                (scratch / '.profile').write_bytes(profile.encode())
            env = os.environ.copy()
            env['HOME'] = str(scratch)
            env['TERM'] = 'dumb'
            if tmux:
                env['TMUX'] = 'test-session'
            else:
                env.pop('TMUX', None)
            for variable in ('PROFILE_MARKER', 'RC_COUNT', '_dotfiles_login_startup',
                             '_dotfiles_login_bashrc_loaded', 'BASH_ENV', 'ENV'):
                env.pop(variable, None)
            # Source only the tracked login-profile contents, without /etc/profile
            # or the real user's startup files. -i exercises .bashrc's real guard.
            commands = ['. "$HOME/.bash_profile"']
            commands += [
                'test "${PROFILE_MARKER-}" = ' + ('loaded' if profile is not None else "''") + ' || exit 11',
                'test "${RC_COUNT:-0}" = ' + ('1' if have_bashrc else '0') + ' || exit 12',
                'test "${_dotfiles_login_startup+x}${_dotfiles_login_bashrc_loaded+x}" = "" || exit 13',
            ]
            if have_bashrc:
                commands += ['. "$HOME/.bashrc"', 'test "$RC_COUNT" = 2 || exit 14']
            commands.append('exit 0')
            result = subprocess.run([bash, '--noprofile', '--norc', '-ic', '\n'.join(commands)],
                                    env=env, cwd=scratch, capture_output=True, text=True, timeout=20)
            assert result.returncode == 0, (name, tmux, result.returncode, result.stderr)
            # Noninteractive login must preserve .profile setup without executing
            # interactive .bashrc configuration (or the appended counter).
            if have_bashrc:
                noninteractive = commands[:1] + [
                    'test "${PROFILE_MARKER-}" = ' + ('loaded' if profile is not None else "''") + ' || exit 21',
                    'test "${RC_COUNT:-0}" = 0 || exit 22',
                    'test "${_dotfiles_login_startup+x}${_dotfiles_login_bashrc_loaded+x}" = "" || exit 23',
                ]
                result = subprocess.run([bash, '--noprofile', '--norc', '-c', '\n'.join(noninteractive)],
                                        env=env, cwd=scratch, capture_output=True, text=True, timeout=20)
                assert result.returncode == 0, (name, tmux, 'noninteractive', result.returncode, result.stderr)
            print('PASS:', name, 'inside tmux' if tmux else 'outside tmux')
