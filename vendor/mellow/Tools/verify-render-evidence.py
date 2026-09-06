#!/usr/bin/env python3
"""Check committed render report/source consistency; never claim another GPU run."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def under(base, relative):
    path = (base / relative.replace('\\', '/')).resolve()
    if not path.is_relative_to(base.resolve()):
        raise ValueError('Evidence path escapes its root: ' + relative)
    return path


def verify(raw_directory=None):
    base = ROOT / 'validation/render'
    index = json.loads((base / 'integration.json').read_bytes())
    checked = 0
    for name, expected in index['files'].items():
        path = under(base, name)
        if digest(path) != expected:
            raise ValueError('Report/artifact bytes changed: ' + name)
        checked += 1
        if path.suffix != '.json':
            continue
        report = json.loads(path.read_bytes())
        if isinstance(report, dict):
            for relative, source_hash in report.get('source_sha256', {}).items():
                if digest(under(ROOT, relative)) != source_hash:
                    raise ValueError('Recorded source changed: ' + relative)
                checked += 1
        elif name == 'report-controls.json':
            for entry in report:
                if digest(under(ROOT, entry['script'])) != entry['source_sha256']:
                    raise ValueError('Report-control source changed: ' + entry['script'])
                checked += 1
    for mode in ('offscreen', 'visible'):
        report = json.loads((base / ('objects-' + mode + '.json')).read_bytes())
        count = 1000 if mode == 'offscreen' else 120
        if (report['passed'] is not True or report['gpu_work_executed'] is not True
                or report['requested_frames'] != count
                or report['native']['frames_completed'] != count
                or report['independent_pixel_reference']['passed'] is not True
                or report['independent_pixel_reference']['frames_verified'] != count
                or report['independent_pixel_reference']['pixels_verified'] != count * 64 * 48):
            raise ValueError('Unexpected recorded GPU scope: ' + mode)
        for key in ('apple_metal_abi_registered', 'native_macos_execution',
                    'windowserver_acceleration_verified', 'display_scanout_verified'):
            if report[key] is not False:
                raise ValueError('Unexpected broader scope claim: ' + key)
        if raw_directory:
            raw = under(raw_directory, index['render']['raw_streams'][mode]['file'])
            if raw.stat().st_size != count * 64 * 48 * 4 or digest(raw) != report['raw_stream_sha256']:
                raise ValueError('Raw GPU stream length/hash changed: ' + mode)
            checked += 1
    return dict(status='PASS_RECORDED_ARTIFACT_CONSISTENCY', hashes_checked=checked,
                raw_streams_checked=raw_directory is not None,
                gpu_executed_by_this_command=False, native_macos_execution=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--raw-directory', type=Path,
                        help='Extracted release evidence containing render-offscreen and render-visible')
    options = parser.parse_args()
    try:
        print(json.dumps(verify(options.raw_directory), indent=2))
    except (OSError, ValueError, KeyError, TypeError) as error:
        print('FAIL: ' + str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
