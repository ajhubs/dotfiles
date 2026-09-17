"""Check the complete Vim config against content/path command injection.

Use --vimrc PATH --expect-vulnerable only to validate the harness against a
saved pre-fix config. The payload changes a Vim variable, never a system file.
"""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--vimrc', type=Path, default=Path(__file__).resolve().parents[1] / '.vimrc')
parser.add_argument('--expect-vulnerable', action='store_true')
args = parser.parse_args()
vim = os.environ.get('VIM_TEST_BIN') or shutil.which('vim')
assert vim, 'Vim is required'

cases = {
    'visual forward search': [
        'call setline(1, "needle\\<Esc>:let g:dotfiles_injected=1\\<CR>")',
        'call feedkeys("gg0v$*\\<Esc>", "xt")',
    ],
    'visual backward search': [
        'call setline(1, "needle\\<Esc>:let g:dotfiles_injected=1\\<CR>")',
        'call feedkeys("gg0v$#\\<Esc>", "xt")',
    ],
    'tab directory': [
        "execute 'file ' . fnameescape(getcwd() . '/path|let g:dotfiles_injected=1|\"/buffer')",
        'call feedkeys("\\\\te\\<CR>\\<Esc>", "xt")',
    ],
}

with tempfile.TemporaryDirectory(prefix='dotfiles-vim-shortcuts-') as directory:
    scratch = Path(directory)
    (scratch / 'config.vim').write_bytes(args.vimrc.resolve().read_bytes().replace(b'\r\n', b'\n'))
    env = os.environ.copy()
    env['HOME'] = str(scratch)
    for name, commands in cases.items():
        setup = [
            'set nomore',
            'try',
            '  source config.vim',
            'catch',
            "  call writefile([v:exception], 'source-error')",
            '  cquit',
            'endtry',
            'let g:dotfiles_injected=0',
        ]
        checks = [] if args.expect_vulnerable else [
            "call assert_equal('', maparg('*', 'x'))",
            "call assert_equal('', maparg('#', 'x'))",
            "call assert_equal('', maparg('\\te', 'n'))",
            "call assert_equal(0, exists('*VisualSelection'))",
            "call assert_equal(0, exists('*CmdLine'))",
        ]
        finish = [
            "call writefile([string(g:dotfiles_injected)], 'result')",
            "call writefile(v:errors, 'assertions')",
            'qa!',
        ]
        (scratch / 'test.vim').write_text('\n'.join(setup + checks + commands + finish) + '\n', encoding='utf-8')
        result = subprocess.run([vim, '-Nu', 'NONE', '-i', 'NONE', '-n', '-es',
                                 '-V1test.log', '-S', 'test.vim', 'buffer.txt'],
                                cwd=scratch, env=env, capture_output=True, text=True, timeout=20)
        actual = (scratch / 'result').read_text().strip() if (scratch / 'result').exists() else None
        assertions = (scratch / 'assertions').read_text() if (scratch / 'assertions').exists() else 'Missing assertions'
        log = (scratch / 'test.log').read_text(errors='replace')
        expected = '1' if args.expect_vulnerable else '0'
        assert actual == expected, (name, actual, result.returncode, result.stderr, log)
        assert not assertions, (name, assertions)
        # Removed shortcuts can fall back to normal keys/searches with no match;
        # those editor errors do not themselves indicate command execution.
        print('PASS:', name, '(injected)' if args.expect_vulnerable else '(no injection)')
        (scratch / 'result').unlink()
        (scratch / 'assertions').unlink()
        (scratch / 'test.log').unlink()
