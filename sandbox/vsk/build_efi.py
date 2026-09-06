#!/usr/bin/env python3
"""Build authenticated-input VSK EFI bootstrap; no post-EBS kernel yet."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import build as native_build

ROOT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--trust-public-key', type=Path, help='Build-time raw32 trusted Ed25519 public key; never read from bundle')
    parser.add_argument('--target', type=int, choices=(26, 27), default=27)
    parser.add_argument('--minimum-epoch', type=int, default=1)
    parser.add_argument('--test', action='store_true', help='Distinct non-release QEMU diagnostic executable')
    args = parser.parse_args()
    if not 1 <= args.minimum_epoch < 2**64:
        parser.error('Minimum epoch must be a nonzero uint64')
    key = args.trust_public_key.read_bytes() if args.trust_public_key else bytes(32)
    if len(key) != 32 or (args.trust_public_key and key == bytes(32)):
        parser.error('Trust key must be a nonzero raw32 public key')
    directory = ROOT / 'build/efi' / ('test' if args.test else 'production')
    directory.mkdir(parents=True, exist_ok=True)
    report_path = directory / 'report.json'
    report_path.write_text('{"passed":false,"boot_authorized":false}\n')
    anchor = directory / 'trust_anchor.h'
    anchor.write_text('#define VF_TRUST_KEY_BYTES {' + ','.join(str(v) for v in key) + '}\n'
                      f'#define VF_MIN_RELEASE_EPOCH UINT64_C({args.minimum_epoch})\n'
                      f'#define VF_TARGET_MAJOR {args.target}u\n')
    sources = [ROOT/'boot/efi/main.c', ROOT/'boot/efi/platform.c',
               *(ROOT/'src'/name for name in ('vf_boot.c','vf_bundle.c','vf_dmar.c','vf_elf.c','vf_runtime.c','vf_efi.c')),
               *native_build.crypto_sources()]
    tracked = [*sources, Path(__file__), ROOT/'build.py', anchor,
               *(ROOT/'include').glob('*.h'), *(ROOT/'boot/efi').rglob('*.h'),
               *(p for p in (ROOT/'crypto').rglob('*') if p.is_file()),
               ROOT.parent/'efi/uefi.h', ROOT.parent/'efi/jit.h']
    def hashes():
        return {str(p.relative_to(ROOT.parent)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(set(tracked))}
    before = hashes()
    flags = ['--target=x86_64-pc-win32-coff', '-std=c17', '-ffreestanding', '-fshort-wchar',
             '-fno-stack-protector', '-fno-builtin', '-mno-red-zone', '-mno-stack-arg-probe',
             '-mgeneral-regs-only', '-mno-avx', '-mno-avx2', '-O2', '-Wall', '-Wextra', '-Werror',
             '-I', str(ROOT/'include'), '-I', str(ROOT/'boot/efi/freestanding'), '-I', str(directory)]
    objects = []
    for source in sources:
        obj = directory / (source.stem + '.obj')
        subprocess.run(['clang', *flags, *(['-DVF_QEMU_TEST'] if args.test else []),
                        '-c', str(source), '-o', str(obj)], check=True, timeout=120)
        objects.append(obj)
    binary = directory / ('TESTVSK.EFI' if args.test else 'VSKBOOT.EFI')
    subprocess.run(['lld-link', '/subsystem:efi_application', '/entry:efi_main', '/nodefaultlib',
                    '/machine:x64', '/dynamicbase', '/nxcompat', '/timestamp:0', '/out:'+str(binary),
                    *map(str, objects)], check=True, timeout=120)
    if hashes() != before:
        raise RuntimeError('EFI source changed during build; evidence rejected')
    report = {'schema':'26x86.vsk-efi-input/1', 'passed':True,
              'artifact':binary.name, 'bytes':binary.stat().st_size,
              'sha256':hashlib.sha256(binary.read_bytes()).hexdigest(),
              'test_instrumentation':args.test, 'trust_anchor_provisioned':key != bytes(32),
              'public_key_sha256':hashlib.sha256(key).hexdigest(), 'target_major':args.target,
              'minimum_release_epoch':args.minimum_epoch, 'source_sha256':before,
              'compiler':subprocess.check_output(['clang','--version'], text=True).splitlines()[0],
              'boot_authorized':False, 'macos_boot_verified':False,
              'exit_boot_services_implemented':False,
              'exit_boot_services_adapter_implemented':True,
              'exit_boot_services_called':False,
              'scope':'Authenticates bundle, copies verified ELF into RW/NX EFI-owned memory, samples firmware, and ships an uninvoked final-map/EBS adapter; stops before platform admission'}
    report_path.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='source_sha256'}, indent=2))


if __name__ == '__main__':
    main()
