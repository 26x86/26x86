#!/usr/bin/env python3
"""Run the real hook without staging prohibited paths or altering any Git index."""
import argparse
import os
from pathlib import Path
import subprocess
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--hook', type=Path, required=True)
    args = parser.parse_args()
    hook = args.hook.resolve(strict=True)
    cases = [
        ('empty', [], 0, False),
        ('public', ['src/main.rs', 'docs/_isolated-notes.md'], 0, False),
        ('root', ['_isolated'], 0, True),
        ('private', ['src/main.rs', '_isolated/fixture'], 0, True),
        ('dot-prefix', ['./_isolated/fixture'], 0, True),
        ('newline', ['_isolated/line\nbreak'], 0, True),
        ('quote-tab', ['_isolated/"tab\tname'], 0, True),
        ('unicode', ['_isolated/한글'], 0, True),
        ('lookalike', ['_isolated-other/fixture', 'nested/_isolated/fixture'], 0, False),
        ('git-failure', [], 17, True),
    ]
    with tempfile.TemporaryDirectory(prefix='nextcore-guard-') as directory:
        scratch = Path(directory)
        shim = scratch / 'git'
        shim.write_text(
            '#!/usr/bin/env python3\n'
            'import os, sys\n'
            'assert sys.argv[1:] == ["diff", "--cached", "--name-only", "--diff-filter=ACMRT", "-z"]\n'
            'sys.stdout.buffer.write(open(os.environ["NX_GUARD_FIXTURE"], "rb").read())\n'
            'sys.exit(int(os.environ["NX_GUARD_GIT_EXIT"]))\n', encoding='utf8')
        shim.chmod(0o700)
        fixture = scratch / 'git-output'
        for name, paths, git_exit, reject in cases:
            fixture.write_bytes(b''.join(p.encode('utf8') + b'\0' for p in paths))
            env = dict(os.environ, PATH=str(scratch) + os.pathsep + os.environ['PATH'],
                       NX_GUARD_FIXTURE=str(fixture), NX_GUARD_GIT_EXIT=str(git_exit))
            result = subprocess.run(['bash', str(hook)], env=env, capture_output=True, timeout=10)
            assert (result.returncode != 0) == reject, (name, result.returncode, result.stderr)
            if reject and git_exit == 0:
                assert b'COMMIT REJECTED' in result.stderr, (name, result.stderr)
            if git_exit:
                assert result.returncode == git_exit, (name, result.returncode)
            print(f'{name}: PASS')


if __name__ == '__main__':
    main()
