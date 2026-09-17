"""Exercise the actual :w!! mapping with a harmless sudo substitute."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
mapping = next(line for line in (root / '.vimrc').read_text(encoding='utf-8').splitlines()
               if line.startswith('cnoremap w!! '))
vim = os.environ.get('VIM_TEST_BIN') or shutil.which('vim')
assert vim, 'Vim is required'

def vim_string(value):
    return "'" + str(value).replace("'", "''") + "'"

filenames = ['ordinary file', 'sample;touch AUDIT_MARKER;',
             '$(touch AUDIT_MARKER)', "quote'file;touch AUDIT_MARKER;",
             '-leading-option', 'percent%hash#bang!file']
with tempfile.TemporaryDirectory(prefix='dotfiles-vim-test-') as directory:
    scratch = Path(directory)
    bindir = scratch / 'bin'
    bindir.mkdir()
    sudo = bindir / 'sudo'
    sudo.write_text('#!/bin/bash\nprintf "%s\\0" "$@" > sudo-args\ncat > saved-input\n', encoding='utf-8')
    sudo.chmod(0o700)
    env = os.environ.copy()
    env['PATH'] = str(bindir) + os.pathsep + str(Path(vim).parent) + os.pathsep + env.get('PATH', '')
    for name in filenames:
        script = ['set shell=/bin/bash', 'set shellcmdflag=-c', 'set shellquote=',
                  'set shellxquote=', mapping,
                  "execute 'edit ' . fnameescape(" + vim_string(name) + ')',
                  "call setline(1, 'test buffer')",
                  "call writefile([expand('%:p')], 'expected-name')",
                  'call feedkeys(":w!!\\<CR>", "xt")', 'qa!']
        (scratch / 'test.vim').write_text('\n'.join(script) + '\n', encoding='utf-8')
        result = subprocess.run([vim, '-Nu', 'NONE', '-i', 'NONE', '-n', '-es', '-S', 'test.vim'],
                                cwd=scratch, env=env, capture_output=True, text=True, timeout=20)
        assert result.returncode == 0, (name, result.stderr)
        args = (scratch / 'sudo-args').read_bytes().split(b'\0')[:-1]
        expected = (scratch / 'expected-name').read_text().strip().encode()
        assert args == [b'tee', b'--', expected], (name, args, expected)
        assert (scratch / 'saved-input').read_text().strip() == 'test buffer'
        assert not (scratch / 'AUDIT_MARKER').exists(), name
        (scratch / 'sudo-args').unlink()
        print('PASS:', name)
