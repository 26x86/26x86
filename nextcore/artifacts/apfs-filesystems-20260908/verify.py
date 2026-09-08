"""Freeze BP24-B host/build/OVMF receipts without restarting the VMs."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import sys
import time

OUT = Path(__file__).resolve().parent
REPO = OUT.parents[2]
sys.path.insert(0, str(REPO / 'nextcore/tools'))
import verify_apfs_jumpstart as gate
import verify_hal_ovmf as bounded

RUN = Path('/tmp/nextcore-apfs-fs-ovmf-r1-20260908')
TARGET = Path('/tmp/nextcore-apfs-filesystems-target-20260908')
os.environ['PATH'] = '/home/developer/.cargo/bin:/usr/bin:/bin'
os.environ['CARGO_TARGET_DIR'] = str(TARGET)
bounded.enable_subreaper()
bounded.child_limits = gate.limits
sources = ['nextcore/crates/nextcore-efi/' + name for name in (
    'Cargo.toml', 'src/apfs_driver.rs', 'src/apfs_probe.rs', 'src/apfs_filesystems.rs', 'src/apfs_observation.rs')]
sources += ['nextcore/tools/verify_apfs_jumpstart.py', 'nextcore/tools/test_verify_apfs_jumpstart.py']
result = {'passed': False, 'commands': [], 'cases': [], 'authored_only': True,
          'filesystem_positive_tested_by_this_harness': False, 'installed_os_boot_verified': False,
          'metal_verified': False, 'hardware_tested': False}
deadline = time.monotonic() + 120
def sha(path):
    return bounded.sha256(path, deadline)
before = {name: sha(REPO / name) for name in sources}
result['sources_before'] = before
try:
    commands = [
        ('rust-version', ['rustc', '--version', '--verbose']),
        ('parser-compile', ['rustc', '--test', '--edition', '2021',
             str(REPO / 'nextcore/crates/nextcore-efi/src/apfs_observation.rs'), '-o', '/tmp/nextcore-apfs-observation-tests-20260908']),
        ('parser-tests', ['/tmp/nextcore-apfs-observation-tests-20260908']),
        ('python-tests', ['python3', '-m', 'unittest', 'discover', '-s', str(REPO / 'nextcore/tools'), '-p', 'test_verify_apfs_jumpstart.py', '-v']),
        ('layout-compile', ['gcc', '-std=c11', '-Wall', '-Wextra', '-Werror', str(OUT / 'layout.c'), '-o', '/tmp/nextcore-apfs-fs-layout-20260908']),
        ('layout', ['/tmp/nextcore-apfs-fs-layout-20260908']),
    ]
    cargo = ['--manifest-path', str(REPO / 'nextcore/Cargo.toml'), '-p', 'nextcore-efi', '--bin', 'NXAPFS',
             '--features', 'apfs-jumpstart', '--target', 'x86_64-unknown-uefi', '--release', '--locked']
    commands += [('build', ['cargo', 'build'] + cargo),
                 ('clippy', ['cargo', 'clippy'] + cargo + ['--no-deps', '--', '-D', 'warnings'])]
    for label, command in commands:
        record = bounded.run_bounded(command, OUT / (label + '.stdout'), OUT / (label + '.stderr'), deadline)
        result['commands'].append(record)
        bounded.validate_execution(record, 0)
    result['tests'] = {'rust_parser_passed': 7, 'python_gate_passed': 9, 'failed': 0}
    archive = OUT / 'r1/NXAPFS.efi'
    result['efi_sha256'] = sha(archive)
    assert result['efi_sha256'] == '1e63c89b5426a2a9d589ee3ffcc93db4c0f8d79a8a1c828d01fea4e5ce5ec725'
    rebuilt = TARGET / 'x86_64-unknown-uefi/release/NXAPFS.efi'
    original_bytes, rebuilt_bytes = archive.read_bytes(), rebuilt.read_bytes()
    assert len(original_bytes) == len(rebuilt_bytes)
    pe = struct.unpack_from('<I', original_bytes, 60)[0]
    assert original_bytes[pe:pe+4] == b'PE\0\0'
    section_count = struct.unpack_from('<H', original_bytes, pe+6)[0]
    optional_size = struct.unpack_from('<H', original_bytes, pe+20)[0]
    sections = []
    for i in range(section_count):
        offset = pe + 24 + optional_size + i*40
        name = original_bytes[offset:offset+8].rstrip(b'\0').decode()
        _, rva, size, file_offset = struct.unpack_from('<IIII', original_bytes, offset+8)
        sections.append((name, rva, size, file_offset))
    debug_rva, debug_size = struct.unpack_from('<II', original_bytes, pe+24+112+6*8)
    assert debug_size == 28
    debug = next(file_offset + debug_rva-rva for _, rva, size, file_offset in sections if rva <= debug_rva < rva+size)
    assert struct.unpack_from('<I', original_bytes, debug+12)[0] == 2
    codeview = struct.unpack_from('<I', original_bytes, debug+24)[0]
    assert original_bytes[codeview:codeview+4] == b'RSDS'
    regions = {'coff_timestamp': [pe+8,4], 'debug_timestamp': [debug+4,4], 'codeview_guid': [codeview+4,16]}
    allowed = {i for start,size in regions.values() for i in range(start,start+size)}
    changed = [i for i,(a,b) in enumerate(zip(original_bytes,rebuilt_bytes)) if a != b]
    assert set(changed).issubset(allowed)
    text_section = next((size,offset) for name,_,size,offset in sections if name == '.text')
    size, offset = text_section
    assert original_bytes[offset:offset+size] == rebuilt_bytes[offset:offset+size]
    result['rebuild_comparison'] = {'rebuilt_sha256': sha(rebuilt), 'archive_preserved': True,
        'whole_binary_identical': original_bytes == rebuilt_bytes, 'different_byte_offsets': changed,
        'allowed_nonexecution_metadata_regions': regions, 'all_other_bytes_identical': True,
        'text_sha256': hashlib.sha256(original_bytes[offset:offset+size]).hexdigest()}
    suite = json.loads((RUN / 'report.json').read_text())
    assert suite['passed'] and len(suite['cases']) == 7
    for case in suite['cases']:
        source = RUN / case['case']
        receipt = json.loads((source / 'report.json').read_text())
        gate.validate_execution(receipt['execution'], receipt['qmp'])
        gate.validate_serial((source / 'serial.log').read_bytes(), case['case'], 29696)
        assert receipt['passed'] and receipt['originals_unchanged']
        assert receipt['hashes_before'] == receipt['hashes_after']
        assert receipt['hashes_before']['probe'] == result['efi_sha256']
        assert receipt['hashes_before']['fixture'] == receipt['guest_disk_sha256']
        assert sha(source / 'guest-disk.raw') == receipt['guest_disk_sha256']
        for name, value in receipt['output_hashes'].items():
            assert sha(source / name) == value
        target = OUT / 'ovmf' / case['case']
        target.mkdir(parents=True, exist_ok=True)
        for name in ('report.json', 'command.json', 'serial.log', 'qemu.stdout', 'qemu.stderr', 'config.plist'):
            shutil.copyfile(source / name, target / name)
            assert sha(source / name) == sha(target / name)
        result['cases'].append({'case': case['case'], 'passed': True,
            'qemu_seconds': receipt['execution']['elapsed_seconds'], 'natural_returncode': 0,
            'cleanup_complete': True, 'originals_unchanged': True, 'guest_disk_unchanged': True,
            'report_sha256': sha(source / 'report.json')})
    shutil.copyfile(RUN / 'report.json', OUT / 'ovmf/report.json')
    result['sources_before'] = before
    result['sources_after'] = {name: sha(REPO / name) for name in sources}
    assert before == result['sources_after']
    result['passed'] = True
except Exception as error:
    result['error'] = f'{type(error).__name__}: {error}'
finally:
    bounded.atomic_json(OUT / 'result.json', result)
print(json.dumps({'passed': result['passed'], 'result': str(OUT / 'result.json')}))
raise SystemExit(0 if result['passed'] else 1)
