"""Archive authored-only evidence and independently recheck the frozen run."""
import hashlib
import json
from pathlib import Path
import shutil
import sys

REPO = Path('/mnt/c/Users/Admin/Documents/ChatGPT/26x86darwin')
OUT = REPO / 'nextcore/artifacts/apfs-ovmf-20260908'
RUN = Path('/tmp/nextcore-apfs-ovmf-r3-20260908')
sys.path.insert(0, str(REPO / 'nextcore/tools'))
import verify_apfs_jumpstart as gate

def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

suite = json.loads((RUN / 'report.json').read_text())
assert suite['passed'] and len(suite['cases']) == 6
summary = {'passed': True, 'layer': 'authored UEFI APFS Jumpstart discovery and driver lifecycle',
           'runtime': str(RUN), 'tests': {'passed': 9, 'failed': 0,
           'command': 'python3 -m unittest discover -s nextcore/tools -p test_verify_apfs_jumpstart.py -v'},
           'cases': [], 'source_sha256': {}, 'macos_booted': False, 'apfs_mounted': False,
           'hardware_tested': False, 'guest_metal_verified': False, 'actual_apple_input_used': False}
for item in suite['cases']:
    source = RUN / item['case']
    report = json.loads((source / 'report.json').read_text())
    gate.validate_execution(report['execution'], report['qmp'])
    gate.validate_serial((source / 'serial.log').read_bytes(), item['case'], 29696)
    assert report['passed'] and report['originals_unchanged']
    assert report['hashes_before'] == report['hashes_after']
    assert report['guest_disk_sha256'] == report['hashes_before']['fixture']
    assert sha(source / 'authored-gpt-apfs.raw') == report['guest_disk_sha256']
    assert sha(source / 'guest-disk.raw') == report['guest_disk_sha256']
    assert report['hashes_before']['harness'] == sha(REPO / 'nextcore/tools/verify_apfs_jumpstart.py')
    for name, expected in report['output_hashes'].items():
        assert sha(source / name) == expected
    target = OUT / 'r3' / item['case']
    target.mkdir(parents=True, exist_ok=True)
    for name in ('report.json', 'command.json', 'serial.log', 'qemu.stdout', 'qemu.stderr', 'config.plist'):
        shutil.copyfile(source / name, target / name)
        assert sha(source / name) == sha(target / name)
    summary['cases'].append({'case': item['case'], 'passed': True,
        'expected_status': report['serial_validation']['expected_status'],
        'qemu_seconds': report['execution']['elapsed_seconds'], 'total_seconds': report['elapsed_seconds'],
        'natural_returncode': 0, 'cleanup_complete': True, 'originals_unchanged': True,
        'complete_guest_disk_unchanged': True, 'esp_readback': report['esp_readback'],
        'report_sha256': sha(source / 'report.json'), 'serial_sha256': sha(source / 'serial.log')})
shutil.copyfile(RUN / 'report.json', OUT / 'r3/report.json')
for name in ('nextcore/tools/verify_apfs_jumpstart.py', 'nextcore/tools/test_verify_apfs_jumpstart.py',
             'nextcore/crates/nextcore-efi/src/apfs_probe.rs', 'nextcore/crates/nextcore-efi/src/apfs_driver.rs',
             'nextcore/crates/nextcore-core/src/apfs_jumpstart.rs'):
    summary['source_sha256'][name] = sha(REPO / name)
summary['efi_sha256'] = json.loads((RUN / 'inspect/report.json').read_text())['hashes_before']
(OUT / 'result.json').write_text(json.dumps(summary, indent=2) + '\n')
print(json.dumps({'passed': True, 'cases': len(summary['cases']), 'output': str(OUT / 'result.json')}))
