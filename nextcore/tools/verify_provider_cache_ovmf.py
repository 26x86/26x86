#!/usr/bin/env python3
"""Compare cached and uncached EFI consumers using authored inputs only."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def protection(receipt):
    rows = [row for row in receipt['markers']
            if row.startswith('NXARMJIT: TRACE_PROTECTION_CALLS ')]
    if len(rows) != 1:
        raise ValueError('Exactly one protection observation required')
    match = re.fullmatch(r'NXARMJIT: TRACE_PROTECTION_CALLS writable=(\d+) '
                         r'executable=(\d+) failures=(\d+) includes_restore=true', rows[0])
    if not match:
        raise ValueError('Invalid protection observation')
    return dict(zip(('writable', 'executable', 'failures'), map(int, match.groups())))


def observed_state(receipt):
    prefixes = ('NXARMJIT: TRACE_MEMORY_OBSERVATION ', 'NXARMJIT: TRACE_MEMORY_REQUEST ',
                'NXARMJIT: TRACE_VIDEO_READBACK ', 'NXARMJIT: TRACE_PLATFORM_STATE ',
                'NXARMJIT: TRACE_EXCEPTION_STATE ')
    return {'execution': receipt['execution'],
            'observed_markers': [row for row in receipt['markers'] if row.startswith(prefixes)]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cached-efi', required=True, type=Path)
    parser.add_argument('--uncached-efi', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    tools = Path(__file__).resolve().parent
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    binaries = {'cached': args.cached_efi.resolve(), 'uncached': args.uncached_efi.resolve()}
    hashes = {key: sha(path) for key, path in binaries.items()}
    results = {}
    commands = []
    for case, script, options in [
        ('framebuffer', 'verify_boot_framebuffer_ovmf.py', ['--memory-observation']),
        ('long-bfm', 'verify_ubfm_consumer_ovmf.py',
         ['--instruction-family', 'bitfield-merge', '--long-diagnostic']),
    ]:
        runs = {}
        for mode, binary in binaries.items():
            folder = output / case / mode
            command = [sys.executable, str(tools / script), '--efi', str(binary),
                       '--output', str(folder), *options]
            commands.append(command)
            run = subprocess.run(command, capture_output=True, text=True, timeout=100)
            folder.mkdir(parents=True, exist_ok=True)
            (folder / 'driver.log').write_text(run.stdout + run.stderr)
            authored = json.loads((folder / 'receipt.json').read_text())
            receipt = json.loads((folder / 'firmware/report.json').read_text())
            runs[mode] = {'passed': run.returncode == 0 and authored['passed'],
                          'state': observed_state(receipt), 'protection': protection(receipt)}
        cached, uncached = runs['cached'], runs['uncached']
        retired = uncached['state']['execution']['retired']
        counts = [entry['protection'] for entry in runs.values()]
        checks = {
            'authored_acceptance': all(entry['passed'] for entry in runs.values()),
            'same_observed_execution_and_requests': cached['state'] == uncached['state'],
            'uncached_exact_calls': uncached['protection'] ==
                {'writable': retired + 1, 'executable': retired, 'failures': 0},
            'balanced_transitions_and_restore': all(count['writable'] == count['executable'] + 1
                and count['failures'] == 0 for count in counts),
            'fewer_real_permission_calls': 0 < cached['protection']['executable']
                < uncached['protection']['executable'],
        }
        results[case] = {'checks': checks,
                         'protection': {mode: run['protection'] for mode, run in runs.items()}}
    preserved = hashes == {key: sha(path) for key, path in binaries.items()}
    passed = preserved and all(all(case['checks'].values()) for case in results.values())
    receipt = {'schema': 'nextcore.provider-cache-efi-comparison.v1', 'passed': passed,
               'cases': results, 'efi_sha256': hashes, 'binaries_preserved': preserved,
               'commands': commands, 'original_images_used': False,
               'physical_boot_verified': False, 'macos_boot_verified': False}
    (output / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt))
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
