#!/usr/bin/env python3
"""Execute the actual GuC loader with the pinned Intel binary and a device emulator."""
import argparse, hashlib, json, os, shutil, subprocess, tempfile
from pathlib import Path
root = Path(__file__).resolve().parents[1]
p = argparse.ArgumentParser()
p.add_argument('--firmware', required=True, type=Path)
p.add_argument('--compiler', default=shutil.which('g++') or shutil.which('clang++'))
p.add_argument('--report', type=Path)
a = p.parse_args()
expected = '7794f0b6abe5fcd9c6f47035dafe2199f30a6e7d230bd5a53fbf8005a60e5911'
if hashlib.sha256(a.firmware.read_bytes()).hexdigest() != expected:
    raise SystemExit('Input is not the pinned unmodified mtl_guc_70.bin; tests not run')
if not a.compiler: raise SystemExit('Native C++ compiler unavailable; tests not run')
sources = [root/'Mellow/XeGuCFirmware.cpp', root/'Mellow/XeFirmware.cpp',
           root/'Mellow/XeGuCTransport.cpp', root/'tests/xe_guc_firmware_tests.cpp']
with tempfile.TemporaryDirectory(prefix='mellow-guc-firmware-') as tmp:
    exe = Path(tmp)/('loader.exe' if os.name == 'nt' else 'loader')
    build = subprocess.run([a.compiler, '-O2', '-std=c++17', '-Wall', '-Wextra', '-Werror',
                            '-I'+str(root/'Mellow'), *map(str,sources), '-o', str(exe)],
                           capture_output=True, text=True)
    if build.returncode: raise SystemExit(build.stdout+build.stderr)
    run = subprocess.run([str(exe), str(a.firmware.resolve())], capture_output=True, text=True, timeout=60)
    if run.returncode: raise SystemExit(run.stdout+run.stderr)
    result = json.loads(run.stdout)
result['firmware_sha256'] = expected
result['scope'] = ('Production loader and GGTT readback helper, original Intel firmware, emulated MMIO '
                   'and ownership callbacks. No physical upload, BootROM authentication, or GPU execution tested.')
tracked = sources+[root/'Mellow/XeGuCFirmware.hpp',root/'Mellow/XeGuCFirmwareIOKit.hpp',root/'Mellow/XeGuCFirmwareIOKit.cpp']
result['source_sha256'] = {str(s.relative_to(root)):hashlib.sha256(s.read_bytes()).hexdigest() for s in tracked}
result['iokit_adapter_runtime_tested'] = False
output = json.dumps(result,indent=2)
if a.report: a.report.write_text(output+'\n',encoding='utf-8')
print(output)
