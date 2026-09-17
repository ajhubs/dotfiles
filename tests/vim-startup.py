"""Exercise actual VimEnter startup with optional NERDTree unavailable or present."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--vimrc', type=Path, default=Path(__file__).resolve().parents[1] / '.vimrc')
args = parser.parse_args()
vim = os.environ.get('VIM_TEST_BIN') or shutil.which('vim')
assert vim, 'Vim is required'
config = args.vimrc.resolve().read_bytes().replace(b'\r\n', b'\n')

cases = [
    ('plugin unavailable', False, [], '', 0, ''),
    ('plugin available', True, [], '', 1, ''),
    ('file argument', True, ['buffer.txt'], '', 0, 'from file'),
    ('stdin buffer', True, ['-'], 'from stdin\n', 0, 'from stdin'),
]

for name, plugin_present, filenames, stdin, expected_calls, expected_line in cases:
    with tempfile.TemporaryDirectory(prefix='dotfiles-vim-startup-') as directory:
        scratch = Path(directory)
        (scratch / 'config.vim').write_bytes(config)
        (scratch / 'buffer.txt').write_text('from file\n', encoding='utf-8')
        setup = ['set nomore', 'let g:nerdtree_calls=0']
        if plugin_present:
            setup.append('command! -bar NERDTree let g:nerdtree_calls += 1')
        setup += [
            'source config.vim',
            'function! CheckStartup()',
            "  call writefile([string(g:nerdtree_calls), getline(1), v:errmsg], 'result')",
            '  qa!',
            'endfunction',
            # Register after the config so its startup handler runs first.
            'autocmd VimEnter * call CheckStartup()',
        ]
        (scratch / 'startup.vim').write_text('\n'.join(setup) + '\n', encoding='utf-8')
        env = os.environ.copy()
        env['HOME'] = str(scratch)
        # Ex mode treats stdin as commands; use normal startup to read a stdin buffer
        # and exercise the real StdinReadPre event before VimEnter.
        mode = ['--not-a-term'] if stdin else ['-es']
        result = subprocess.run(
            [vim, '-N', '--noplugin', '-u', 'startup.vim', '-i', 'NONE', '-n',
             '-V1test.log'] + mode + filenames,
            cwd=scratch, env=env, input=stdin, capture_output=True, text=True, timeout=20,
        )
        actual = ((scratch / 'result').read_text().splitlines()
                  if (scratch / 'result').exists() else None)
        log = (scratch / 'test.log').read_text(errors='replace')
        assert result.returncode == 0, (name, result.returncode, result.stderr, log)
        assert actual == [str(expected_calls), expected_line, ''], (name, actual, log)
        print('PASS:', name)
