#!/usr/bin/env python3
"""Exercise real VSK EFI signed-input path with own-code fixtures under OVMF."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor
import traceback

ROOT = Path(__file__).resolve().parent.parent


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def resolve_executable(value):
    """Resolve a QEMU executable without passing a shell command through."""
    candidate = Path(value).expanduser()
    if candidate.is_absolute() or candidate.parent != Path('.'):
        return candidate.resolve(strict=True)
    located = shutil.which(str(value))
    if not located:
        raise FileNotFoundError(f'QEMU executable not found: {value}')
    return Path(located).resolve(strict=True)


def resolve_file(value, label):
    path = Path(value).expanduser().resolve(strict=True)
    if not path.is_file():
        raise FileNotFoundError(f'{label} is not a regular file: {path}')
    return path


def qemu_version(qemu):
    try:
        completed = subprocess.run(
            [str(qemu), '--version'], capture_output=True, text=True,
            timeout=5, check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        return {'ok': False, 'error': str(error)}
    line = (completed.stdout or completed.stderr).splitlines()
    return {
        'ok': completed.returncode == 0 and bool(line),
        'returncode': completed.returncode,
        'text': line[0] if line else '',
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--efi', type=Path, default=ROOT / 'build' / 'efi' / 'test' / 'TESTVSK.EFI')
    parser.add_argument(
        '--qemu', type=Path,
        default=Path(os.environ.get('QEMU_SYSTEM_X86_64', 'qemu-system-x86_64')),
        help='QEMU x86_64 executable (or a command available on PATH).',
    )
    parser.add_argument(
        '--ovmf-code', type=Path,
        default=Path(os.environ.get('OVMF_CODE', '/usr/share/OVMF/OVMF_CODE_4M.fd')),
        help='Read-only OVMF code flash image.',
    )
    parser.add_argument(
        '--ovmf-vars', type=Path,
        default=Path(os.environ.get('OVMF_VARS', '/usr/share/OVMF/OVMF_VARS_4M.fd')),
        help='Clean OVMF variable template copied per case.',
    )
    parser.add_argument('--timeout', type=float, default=60.0)
    parser.add_argument(
        '--display', choices=('none', 'gtk', 'sdl'), default='none',
        help='QEMU display backend. The default keeps CI/headless validation deterministic.',
    )
    parser.add_argument(
        '--gui', action='store_true',
        help='Open one GTK QEMU window for the valid EFI case.',
    )
    parser.add_argument(
        '--case', choices=('all', 'valid', 'bad-signature', 'bad-blob'), default='all',
        help='Select a case; --gui defaults to the valid case so it does not open three windows.',
    )
    parser.add_argument('--force', action='store_true')
    args = parser.parse_args()
    if args.gui and args.display != 'none':
        parser.error('--gui cannot be combined with --display; use --display gtk instead')
    if args.display != 'none' and args.case == 'all':
        parser.error('--display gtk|sdl requires --case valid|bad-signature|bad-blob')
    display = 'gtk' if args.gui else args.display
    case_names = ['valid', 'bad-signature', 'bad-blob'] if args.case == 'all' else [args.case]
    if args.gui and args.case == 'all':
        case_names = ['valid']
    qemu = resolve_executable(args.qemu)
    ovmf_code = resolve_file(args.ovmf_code, 'OVMF code image')
    ovmf_vars = resolve_file(args.ovmf_vars, 'OVMF variable template')
    qemu_info = qemu_version(qemu)
    bundle = args.bundle.resolve(strict=True)
    binary = args.efi.resolve(strict=True)
    build = json.loads((binary.parent/'report.json').read_text())

    if not args.force and args.output.exists():
        raise FileExistsError(
            f"Output directory already exists: {args.output}. Retry with --force to replace it."
        )

    if not build.get('test_instrumentation') or digest(binary) != build['sha256']:
        raise ValueError('Need the matching explicitly instrumented test EFI')
    originals = {p.name:digest(p) for p in bundle.iterdir() if p.is_file()}
    if args.force and args.output.exists():
        shutil.rmtree(args.output)
    output = args.output.absolute()
    output.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(binary, output/'TESTVSK.EFI')
    shutil.copyfile(binary.parent/'report.json', output/'efi-build-report.json')

    def case(name):
        directory = output/name
        boot = directory/'esp/EFI/BOOT'
        boot.mkdir(parents=True)
        shutil.copyfile(binary,boot/'BOOTX64.EFI')
        staged = directory/'esp/EFI/26x86/VSK'
        shutil.copytree(bundle,staged)
        if name != 'valid':
            path = staged/('manifest.vfb' if name=='bad-signature' else 'core.elf')
            raw=bytearray(path.read_bytes());raw[-1]^=1;path.write_bytes(raw)
        shutil.copyfile(ovmf_vars, directory/'vars.fd')
        command=[str(qemu),'-machine','q35,accel=tcg','-cpu','Nehalem',
                 '-device','intel-iommu,intremap=on,caching-mode=on','-m','512','-smp','1',
                 '-display',display,'-serial','none','-monitor','none',
                 '-drive',f'if=pflash,format=raw,readonly=on,file={ovmf_code}',
                 '-drive',f'if=pflash,format=raw,file={directory/"vars.fd"}',
                 '-drive',f'format=raw,file=fat:rw:{directory/"esp"}',
                 '-debugcon',f'file:{directory/"debug.log"}',
                 '-device','isa-debug-exit,iobase=0xf4,iosize=0x04','-net','none','-no-reboot']
        try:
            completed = subprocess.run(command, capture_output=True, text=True, timeout=args.timeout)
            completion_error = None
        except Exception:
            completion_error = traceback.format_exc()
            completed = type('Completed', (), {'returncode': 1, 'stderr': str(completion_error)})()
        log=(directory/'debug.log').read_text(errors='replace')
        required=['VSK INPUT_ALLOCATIONS_RELEASED']
        forbidden=[]
        if name=='valid':
            required+=['VSK MANIFEST_SIGNATURE_VERIFIED','VSK ALL_BLOB_HASHES_VERIFIED',
                       'VSK CORE_AND_SERVICE_ELF_COPIED_RW_NX','VSK FIRMWARE_SNAPSHOT_READ',
                       'VSK DMAR_UNITS 0x0000000000000001','VSK DMAR_IR_ADVERTISED 0x0000000000000001',
                       'VSK E_PLATFORM_PROFILE_UNREGISTERED']
            expected=33
        elif name=='bad-signature':
            required+=['VSK E_BUNDLE_AUTH'];forbidden+=['VSK MANIFEST_SIGNATURE_VERIFIED']
            expected=35
        else:
            required+=['VSK MANIFEST_SIGNATURE_VERIFIED','VSK E_BLOB_INTEGRITY']
            forbidden+=['VSK ALL_BLOB_HASHES_VERIFIED','VSK CORE_AND_SERVICE_ELF_COPIED_RW_NX']
            expected=35
        result={'name':name,'passed':completed.returncode==expected and all(v in log for v in required)
                and not any(v in log for v in forbidden) and completion_error is None,'qemu_exit':completed.returncode,
                'required':required,'log':log,'stderr':completed.stderr,'command':command}
        if completion_error is not None:
            result['execution_error'] = completion_error
        (directory/'case.json').write_text(json.dumps(result,indent=2)+'\n')
        return result

    if len(case_names) == 1:
        results = [case(case_names[0])]
    else:
        with ThreadPoolExecutor(max_workers=3) as pool:
            results=list(pool.map(case,case_names))
    unchanged=originals=={p.name:digest(p) for p in bundle.iterdir() if p.is_file()}
    report={'schema':'26x86.vsk-efi-input-execution/1','passed':unchanged and all(v['passed'] for v in results),
            'test_efi_sha256':digest(binary),'target_major':build['target_major'],
            'original_inputs_unchanged':unchanged,'validation_level':'SIMULATED',
            'actual_efi_executed':True,'linux_guest_used':False,'host_cpu_model':'Nehalem',
            'boot_authorized':False,'macos_boot_verified':False,'physical_mac_verified':False,
            'exit_boot_services_called':False,'guest_code_executed_in_efi':False,
            'display_backend':display,'gui_requested':args.gui,
            'qemu_path':str(qemu),'qemu_version':qemu_info,
            'ovmf_code':{'path':str(ovmf_code),'sha256':digest(ovmf_code)},
            'ovmf_vars_template':{'path':str(ovmf_vars),'sha256':digest(ovmf_vars)},
            'display_environment':{
                'display':bool(os.environ.get('DISPLAY')),
                'wayland_display':bool(os.environ.get('WAYLAND_DISPLAY')),
            },
            'target_name':'Tahoe' if build['target_major'] == 26 else 'Golden Gate',
            'guest_profile':'arm64-conformance-v1 (macOS target label; iBoot/XNU not executed)',
            'original_file_sha256':originals,'cases':results}
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='cases'},indent=2))
    raise SystemExit(0 if report['passed'] else 1)


if __name__=='__main__':
    main()
