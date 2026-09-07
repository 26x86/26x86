#!/usr/bin/env python3
"""Build and verify a pinned, optional Linux/TCG Reims graphics candidate.

All source and generated output live in a fresh work directory. Git reference
repositories provide read-only object reuse. No Apple guest input is accepted.
The default backend patch series and active native builds are never changed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import stat
import subprocess
import sys
import time

PROJECT = Path(__file__).resolve().parents[1]
OPTIONAL = PROJECT / 'patches/graphics'
sys.path.insert(0, str(PROJECT))
from venfire.artifacts import read_regular, hash_artifact
from venfire.host import detect_host

STATUS = 'NONREDISTRIBUTABLE DEVELOPMENT ARTIFACT'


def regular_bytes(path: Path) -> bytes:
    with read_regular(path) as stream:
        return stream.read()


def checked_directory(path: Path, *, exists=True) -> Path:
    path = path.expanduser().absolute()
    if '..' in path.parts:
        raise ValueError('Parent traversal is not accepted in build paths')
    for candidate in (*reversed(path.parents), path):
        try:
            info = candidate.lstat()
        except FileNotFoundError:
            if exists:
                raise ValueError(f'Directory does not exist: {candidate}')
            continue
        if not stat.S_ISDIR(info.st_mode) or stat.S_ISLNK(info.st_mode):
            raise ValueError(f'Directory path contains a link or non-directory: {candidate}')
    return path


def load_inputs():
    lock = json.loads(regular_bytes(OPTIONAL / 'lock.json'))
    if not isinstance(lock, dict) or type(lock.get('schema')) is not int or lock['schema'] != 1:
        raise ValueError('Unsupported optional graphics lock schema')
    snapshots = {}
    for category, directory in (('core_patches', PROJECT / 'patches'),
                                ('optional_patches', OPTIONAL),
                                ('probes', OPTIONAL / 'probes')):
        if not isinstance(lock.get(category), dict) or not lock[category]:
            raise ValueError('Missing or invalid graphics lock input table: ' + category)
        for name, digest in lock[category].items():
            if not isinstance(name, str) or not name or Path(name).name != name:
                raise ValueError('Lockfile input must be a direct filename')
            if not isinstance(digest, str) or not re.fullmatch(r'[0-9a-f]{64}', digest):
                raise ValueError('Lockfile input must have a SHA-256 digest: ' + name)
            data = regular_bytes(directory / name)
            if hashlib.sha256(data).hexdigest() != digest:
                raise ValueError(f'Reviewed input changed: {category}/{name}')
            snapshots[category + '/' + name] = data
    # The optional Reims candidate is a frozen graphics acceptance line.  It
    # intentionally keeps the core-0001..0004 lock separate from the newer
    # j274/iBoot research series used by the portable raw-Stage2 runner.
    core_series = regular_bytes(OPTIONAL / 'core-series').decode().splitlines()
    if core_series != list(lock['core_patches']):
        raise ValueError('Core series differs from the explicitly pinned graphics candidate')
    if regular_bytes(OPTIONAL / 'series').decode().splitlines() != list(lock['optional_patches']):
        raise ValueError('Optional graphics series differs from lockfile')
    return lock, snapshots


class Builder:
    def __init__(self, work, environment, report):
        self.work, self.env, self.report = work, environment, report
        self.counter = 0

    def save(self):
        (self.work / 'build-report.json').write_text(json.dumps(self.report, indent=2) + '\n')

    def run(self, args, *, cwd=None, timeout=900, capture=False):
        command = list(map(str, args))
        self.counter += 1
        log_path = self.work / 'logs' / f'{self.counter:03d}-{Path(command[0]).name}.log'
        print('+ ' + ' '.join(command), flush=True)
        start = time.monotonic()
        with log_path.open('wb') as log:
            result = subprocess.run(command, cwd=cwd, env=self.env,
                                    stdout=subprocess.PIPE if capture else log,
                                    stderr=log, timeout=timeout)
        self.report['steps'].append({'command': command, 'cwd': str(cwd) if cwd else None,
                                     'exit_code': result.returncode,
                                     'seconds': time.monotonic() - start,
                                     'log': str(log_path)})
        self.save()
        if result.returncode:
            raise RuntimeError(f'Command failed ({result.returncode}); see {log_path}')
        return result.stdout if capture else None

    def checkout(self, name, pin, reference=None, *, materialize=True):
        destination = self.work / name
        if reference:
            reference = checked_directory(reference)
            self.run(['git', 'clone', '--shared', '--no-checkout', reference, destination])
            self.run(['git', 'remote', 'set-url', 'origin', pin['url']], cwd=destination)
        else:
            self.run(['git', 'init', destination])
            self.run(['git', 'remote', 'add', 'origin', pin['url']], cwd=destination)
            self.run(['git', 'fetch', '--depth=1', 'origin', pin['commit']], cwd=destination)
        actual = self.run(['git', 'rev-parse', pin['commit'] + '^{commit}'],
                          cwd=destination, capture=True).decode().strip()
        if actual != pin['commit']:
            raise ValueError('Git reference did not supply the pinned commit')
        if materialize:
            self.run(['git', 'checkout', '--detach', pin['commit']], cwd=destination)
        return destination


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work', required=True, type=Path)
    parser.add_argument('--jobs', type=int, default=min(os.cpu_count() or 2, 12))
    for name in ('qemu-reference', 'reims-reference', 'reims-qemu-reference', 'cargo-cache'):
        parser.add_argument('--' + name, type=Path)
    parser.add_argument('--tool-bin', action='append', type=Path, default=[])
    parser.add_argument('--library-dir', action='append', type=Path, default=[])
    parser.add_argument('--linker', choices=('system', 'lld'), default='system')
    parser.add_argument('--rust-profile', choices=('debug', 'release'), default='release')
    parser.add_argument('--vulkan-icd', type=Path, default=Path('/usr/share/vulkan/icd.d/lvp_icd.json'))
    parser.add_argument('--verify-only', action='store_true', help='Recheck a previously completed build')
    args = parser.parse_args()
    if platform.system() != 'Linux' or platform.machine().lower() not in ('x86_64', 'amd64'):
        parser.error('Use x86_64 Linux; Windows callers can invoke through WSL')
    host = detect_host()
    if not host.cpu_eligible:
        parser.error('Intel x86_64 with OS-visible AVX2 is required, including synthetic tests')
    if not 1 <= args.jobs <= 64:
        parser.error('jobs must be 1..64')
    lock, snapshots = load_inputs()
    work = checked_directory(args.work, exists=args.verify_only)
    if work == PROJECT or work in PROJECT.parents or work.is_relative_to(PROJECT):
        parser.error('Use a fresh build directory outside the source project')
    env = {k: v for k, v in os.environ.items() if not k.startswith(('REIMS_', 'METAL2VULKAN_'))}
    for key in ('CFLAGS', 'CPPFLAGS', 'CXXFLAGS', 'LDFLAGS', 'RUSTFLAGS', 'CARGO_ENCODED_RUSTFLAGS'):
        env.pop(key, None)
    bins = [str(checked_directory(p)) for p in args.tool_bin]
    env['PATH'] = os.pathsep.join(bins + [env.get('PATH', '/usr/bin:/bin')])
    libs = [str(checked_directory(p)) for p in args.library_dir]
    if libs:
        env['LD_LIBRARY_PATH'] = os.pathsep.join(libs + ([env['LD_LIBRARY_PATH']] if env.get('LD_LIBRARY_PATH') else []))
    for tool in ('git', 'cargo', 'rustc', 'cc', 'ninja', 'aarch64-linux-gnu-as',
                 'aarch64-linux-gnu-ld', 'aarch64-linux-gnu-objcopy', 'glslc',
                 'spirv-as', 'spirv-val', 'llvm-dis', 'vulkaninfo'):
        if not shutil.which(tool, path=env['PATH']):
            parser.error(f'Required build/verification tool missing: {tool}')
    if args.linker == 'lld' and not shutil.which('ld.lld', path=env['PATH']):
        parser.error('Requested LLD linker is not in the supplied tool path')
    regular_bytes(args.vulkan_icd.absolute())
    if args.verify_only:
        report = json.loads(regular_bytes(work / 'build-report.json'))
        binary = work / 'qemu-build/qemu-system-aarch64'
        if hash_artifact(binary, kind='graphics-backend').sha256 != report.get('binary_sha256'):
            parser.error('Previously built binary changed')
        if report.get('source_lock') != lock:
            parser.error('Previously built candidate uses a different lockfile')
        args.rust_profile = report['rust_profile']
    else:
        work.mkdir(parents=True, exist_ok=False)
        for name in ('inputs', 'logs', 'tmp'):
            (work / name).mkdir()
        for relative, data in snapshots.items():
            target = work / 'inputs' / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        report = {'schema': 1, 'distribution_status': STATUS,
                  'upstream_licenses_unchanged': True, 'host_guard_bypass_included': False,
                  'source_lock': lock, 'host': host.to_dict(),
                  'rust_profile': args.rust_profile, 'steps': [], 'passed': False,
                  'macos_boot_verified': False}
        (work / 'DEVELOPMENT_ONLY.json').write_text(json.dumps({
            'schema': 1, 'distribution_status': STATUS,
            'policy': 'Private project-generated experimental candidate; upstream licenses unchanged.'}, indent=2) + '\n')
    env['CARGO_HOME'] = str(checked_directory(args.cargo_cache) if args.cargo_cache else work / 'cargo-home')
    env['CARGO_TARGET_DIR'] = str(work / 'rust-target')
    env['TMPDIR'] = str(work / 'tmp')
    builder = Builder(work, env, report)
    try:
        if not args.verify_only:
            reims = builder.checkout('reims-source', lock['reims'], args.reims_reference)
            qemu = builder.checkout('qemu-source', lock['qemu'], args.qemu_reference)
            fork = builder.checkout('reims-qemu-reference', lock['reims_qemu'], args.reims_qemu_reference,
                                    materialize=False)
            if hashlib.sha256(regular_bytes(reims / 'Cargo.lock')).hexdigest() != lock['cargo_lock_sha256']:
                raise ValueError('Pinned Cargo.lock does not match the reviewed manifest')
            if lock['metal2vulkan']['commit'].encode() not in regular_bytes(reims / 'Cargo.lock'):
                raise ValueError('Shader translator commit is not present in Cargo.lock')
            touched = set(lock['imported_files']) | {'hw/display/trace-events'}
            for category in ('core_patches',):
                for name in lock[category]:
                    patch = work / 'inputs' / category / name
                    touched.update(re.findall(r'^\+\+\+ b/(.+)$', patch.read_text(), re.M))
                    builder.run(['git', 'apply', '--check', patch], cwd=qemu)
                    builder.run(['git', 'apply', patch], cwd=qemu)
            for name, digest in lock['imported_files'].items():
                content = builder.run(['git', 'show', lock['reims_qemu']['commit'] + ':' + name],
                                      cwd=fork, capture=True)
                if hashlib.sha256(content).hexdigest() != digest:
                    raise ValueError(f'Unreviewed GPU host source: {name}')
                if (qemu / name).exists():
                    raise ValueError(f'Import would overwrite an existing source: {name}')
                (qemu / name).write_bytes(content)
            trace = builder.run(['git', 'show', lock['reims_qemu']['commit'] + ':hw/display/trace-events'],
                                cwd=fork, capture=True).decode()
            events = '\n'.join(line for line in trace.splitlines() if line.startswith('reims_vgpu_')) + '\n'
            if hashlib.sha256(events.encode()).hexdigest() != lock['trace_events_sha256']:
                raise ValueError('Imported GPU trace declarations changed')
            with (qemu / 'hw/display/trace-events').open('a') as stream:
                stream.write('\n# Reims host device trace events, pinned external import.\n' + events)
            for name in lock['optional_patches']:
                patch = work / 'inputs/optional_patches' / name
                touched.update(re.findall(r'^\+\+\+ b/(.+)$', patch.read_text(), re.M))
                builder.run(['git', 'apply', '--check', patch], cwd=qemu)
                builder.run(['git', 'apply', patch], cwd=qemu)
            builder.run(['git', 'add', '-N', '--', *lock['imported_files']], cwd=qemu)
            actual = set(builder.run(['git', 'diff', '--name-only'], cwd=qemu, capture=True).decode().splitlines())
            if actual != touched:
                raise ValueError(f'Unexpected source change scope: {sorted(actual ^ touched)}')
            report['source_audit'] = {'changed_paths': sorted(actual), 'matched_expected_scope': True}
            diff = builder.run(['git', 'diff', '--binary'], cwd=qemu, capture=True)
            (work / 'combined-host.patch').write_bytes(diff)
            report['combined_patch_sha256'] = hashlib.sha256(diff).hexdigest()
            report['source_hashes'] = {name: hash_artifact(qemu / name, kind='qemu-source').sha256 for name in sorted(actual)}
            for tool in ('cargo', 'rustc', 'cc'):
                report[tool + '_version'] = builder.run([tool, '--version'], capture=True).decode().splitlines()[0]
            cargo = ['cargo', 'build', '--manifest-path', reims / 'Cargo.toml', '--locked',
                     '--no-default-features', '--features', ','.join(lock['rust_features']),
                     '-p', 'reims-vgpu', '-j', args.jobs]
            if args.rust_profile == 'release':
                cargo.append('--release')
            builder.run(cargo, timeout=3600)
            library = work / 'rust-target' / args.rust_profile / 'libreims_vgpu.a'
            report['rust_staticlib_sha256'] = hash_artifact(library, kind='rust-staticlib').sha256
            build = work / 'qemu-build'
            build.mkdir()
            configure = [qemu / 'configure', '--target-list=aarch64-softmmu', '--enable-tcg',
                         '--disable-kvm', '--disable-hvf', '--disable-docs', '--disable-gtk',
                         '--disable-sdl', '--disable-opengl', '--enable-vnc', '--disable-tools',
                         '--disable-debug-info', '--disable-werror', '--extra-cflags=-mavx2',
                         '-Dreims_vgpu_library=' + str(library),
                         '-Dreims_vgpu_include=' + str(reims / 'crates/reims-vgpu/include')]
            if args.linker == 'lld':
                configure.extend(['-Dc_link_args=-fuse-ld=lld', '-Dcpp_link_args=-fuse-ld=lld'])
            builder.run(configure, cwd=build, timeout=600)
            builder.run(['ninja', '-j', args.jobs, 'qemu-system-aarch64'], cwd=build, timeout=3600)
            binary = build / 'qemu-system-aarch64'
            report['binary_sha256'] = hash_artifact(binary, kind='graphics-backend').sha256
            report['binary_size'] = binary.stat().st_size
            report['binary'] = str(binary)
            builder.save()
        verify = OPTIONAL / 'probes/verify.py'
        if hashlib.sha256(regular_bytes(verify)).hexdigest() != lock['probes']['verify.py']:
            raise ValueError('Verification harness changed during build')
        result_dir = work / ('evidence-' + time.strftime('%Y%m%d-%H%M%S'))
        builder.run([sys.executable, verify, '--binary', binary, '--output', result_dir,
                     '--reims-source', work / 'reims-source', '--rust-target', work / 'rust-target',
                     '--rust-profile', args.rust_profile, '--vulkan-icd', args.vulkan_icd.absolute(),
                     '--jobs', args.jobs], timeout=1800)
        verification = json.loads(regular_bytes(result_dir / 'report.json'))
        if verification.get('passed') is not True:
            raise ValueError('Graphics verification did not pass')
        for name, digest in report['source_hashes'].items():
            if hash_artifact(work / 'qemu-source' / name, kind='qemu-source').sha256 != digest:
                raise ValueError('QEMU source changed during build or verification')
        if builder.run(['git', 'status', '--porcelain'], cwd=work / 'reims-source', capture=True):
            raise ValueError('Pinned Reims source tree changed')
        if hash_artifact(binary, kind='graphics-backend').sha256 != report['binary_sha256']:
            raise ValueError('Built binary changed during verification')
        report.update({'passed': True, 'verification': str(result_dir / 'report.json')})
        builder.save()
        print(json.dumps(report, indent=2))
        return 0
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        report.update({'passed': False, 'error': f'{type(exc).__name__}: {exc}'})
        builder.save()
        print(json.dumps({'passed': False, 'error': report['error'], 'report': str(work / 'build-report.json')}))
        return 1


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError, ValueError) as exc:
        print(json.dumps({'passed': False, 'error': f'{type(exc).__name__}: {exc}'}), file=sys.stderr)
        raise SystemExit(1)
