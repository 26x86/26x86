#!/usr/bin/env python3
"""Verify a graphics candidate using only bundled/authored synthetic inputs."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

PROBES = Path(__file__).resolve().parent
PROJECT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT))
from venfire.artifacts import create_manifest, require_intact, read_regular


def read(path):
    with read_regular(path) as stream:
        return stream.read()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--binary', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--reims-source', required=True, type=Path)
    parser.add_argument('--rust-target', required=True, type=Path)
    parser.add_argument('--rust-profile', choices=('debug', 'release'), required=True)
    parser.add_argument('--vulkan-icd', required=True, type=Path)
    parser.add_argument('--jobs', type=int, default=4)
    args = parser.parse_args()
    if not 1 <= args.jobs <= 64:
        parser.error('jobs must be 1..64')
    output = args.output.absolute()
    output.mkdir(parents=True, exist_ok=False)
    (output / 'tmp').mkdir()
    lock = json.loads(read(PROBES.parent / 'lock.json'))
    fixture = args.reims_source / 'crates/reims-vgpu/tests/fixtures/air/float_mul4_add3.air'
    if hashlib.sha256(read(fixture)).hexdigest() != lock['air_fixture_sha256']:
        raise ValueError('Only the pinned authored AIR fixture is accepted')
    paths = [args.binary, args.vulkan_icd, fixture, args.reims_source / 'Cargo.lock']
    for name, digest in lock['probes'].items():
        if hashlib.sha256(read(PROBES / name)).hexdigest() != digest:
            raise ValueError('Verification source changed: ' + name)
        paths.append(PROBES / name)
    manifest = create_manifest(paths, kind='graphics-verification')
    environment = {k: v for k, v in os.environ.items() if not k.startswith(('REIMS_', 'METAL2VULKAN_'))}
    for name in ('DISPLAY', 'WAYLAND_DISPLAY', 'XDG_RUNTIME_DIR'):
        environment.pop(name, None)
    environment['VK_DRIVER_FILES'] = str(args.vulkan_icd.absolute())
    environment['VK_ICD_FILENAMES'] = environment['VK_DRIVER_FILES']
    environment['TMPDIR'] = str(output / 'tmp')
    environment['CARGO_TARGET_DIR'] = str(args.rust_target.absolute())
    report = {'schema': 1, 'passed': False, 'steps': [], 'checks': {},
              'distribution_status': 'NONREDISTRIBUTABLE DEVELOPMENT ARTIFACT',
              'macos_boot_verified': False, 'physical_display_verified': False,
              'guest_trust_or_cpu_requirements_waived': False}

    def run(name, command, timeout=300):
        print('VERIFY ' + name, flush=True)
        start = time.monotonic()
        proc = subprocess.run(list(map(str, command)), env=environment, capture_output=True,
                              text=True, timeout=timeout)
        (output / (name + '.stdout.log')).write_text(proc.stdout)
        (output / (name + '.stderr.log')).write_text(proc.stderr)
        report['steps'].append({'name': name, 'command': list(map(str, command)),
                                'exit_code': proc.returncode, 'seconds': time.monotonic() - start})
        if proc.returncode != 0:
            raise RuntimeError(f'{name} failed with exit {proc.returncode}; see its output logs')
        return proc.stdout, proc.stderr

    try:
        info, _ = run('vulkan-info', ['vulkaninfo', '--summary'])
        if not re.search(r'deviceType\s*=\s*.*CPU', info):
            raise ValueError('This acceptance suite requires a CPU/software Vulkan ICD')
        report['checks']['software_vulkan_device'] = True
        profile = args.rust_target / args.rust_profile
        dependencies = profile / 'deps'
        translator = list(dependencies.glob('libmetal2vulkan-*.rlib'))
        if len(translator) != 1:
            raise ValueError('Expected one pinned translator rlib in the fresh target directory')
        executable = output / 'air-compute'
        run('air-compile', ['rustc', '--edition', '2021', PROBES / 'air_compute.rs',
                           '-L', 'dependency=' + str(dependencies),
                           '--extern', 'reims_vgpu=' + str(profile / 'libreims_vgpu.rlib'),
                           '--extern', 'metal2vulkan=' + str(translator[0]), '-o', executable], timeout=600)
        for key, command in (('METAL2VULKAN_LLVM_DIS', 'llvm-dis'), ('METAL2VULKAN_SPIRV_VAL', 'spirv-val')):
            tool = shutil.which(command, path=environment['PATH'])
            if not tool:
                raise ValueError('Missing translator tool: ' + command)
            environment[key] = tool
        air, _ = run('air-compute', [executable, fixture, output / 'air-scratch'])
        air_result = json.loads(air)
        if (air_result.get('passed') is not True or air_result.get('spirv_bytes') != 632
                or air_result.get('software_vulkan_values') != [7, 11, 15, 19, 23, 27, 31, 35]):
            raise ValueError('AIR compute did not produce the expected values')
        report['checks']['air_compute'] = air_result
        for test in ('compute_inc_ssbo_known_result', 'compute_2d_grid_tiles_global_invocation_xy',
                     'compute_storage_image_rgba8unorm_known_result'):
            command = ['cargo', 'test', '--manifest-path', args.reims_source / 'Cargo.toml',
                       '--locked', '--no-default-features', '--features', ','.join(lock['rust_features']),
                       '-p', 'reims-vgpu', '-j', args.jobs, '--test', 'vk_engine_compute', test]
            if args.rust_profile == 'release':
                command.append('--release')
            command.extend(['--', '--exact', '--test-threads=1', '--nocapture'])
            stdout, stderr = run(test, command, timeout=900)
            if '1 passed; 0 failed; 0 ignored' not in stdout or 'SKIP' in stdout + stderr:
                raise ValueError('Upstream compute test skipped or did not run exactly one case: ' + test)
            report['checks'][test] = True
        for variant in ('final-graphics', 'final-headless'):
            run(variant, [sys.executable, PROBES / 'cpu_startup.py', '--binary', args.binary,
                          '--output', output, '--variant', variant])
            result = json.loads(read(output / ('qemu-startup-result-' + variant + '.json')))
            if result.get('passed') is not True or result['self_authored_guest']['passed_count'] != 12:
                raise ValueError('CPU/MMIO integration evidence did not pass: ' + variant)
            report['checks'][variant] = result
        run('mapper-handoff', [sys.executable, PROBES / 'mapper_handoff.py', '--binary', args.binary,
                              '--output', output, '--variant', 'final'])
        mapper = json.loads(read(output / 'mapper-handoff-result-final.json'))
        if mapper.get('passed') is not True:
            raise ValueError('Actual mapper handoff failed')
        report['checks']['mapper_handoff'] = mapper
        run('firmware-console', [sys.executable, PROBES / 'firmware_console.py', '--binary', args.binary,
                                '--output', output])
        console = json.loads(read(output / 'firmware-console-result.json'))
        if console.get('passed') is not True or console.get('case_count') != 11:
            raise ValueError('Actual firmware pixel/refusal evidence did not pass')
        report['checks']['firmware_console'] = console
        report['passed'] = True
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        report['error'] = f'{type(exc).__name__}: {exc}'
    finally:
        try:
            require_intact(manifest)
            report['inputs_intact'] = True
        except Exception as exc:
            report.update({'passed': False, 'inputs_intact': False, 'integrity_error': str(exc)})
        (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'passed': report['passed'], 'report': str(output / 'report.json'),
                      'error': report.get('error')}))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
