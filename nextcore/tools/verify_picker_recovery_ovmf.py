#!/usr/bin/env python3
"""Exercise production BOOTX64 failure recovery with real EFI child images."""
import argparse
import hashlib
import json
from pathlib import Path
import plistlib
import re
import shutil
import socket
import subprocess
import time


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_case(root, efi, child, kind):
    out = root / kind
    boot = out / 'esp/EFI/BOOT'
    oc = out / 'esp/EFI/OC'
    boot.mkdir(parents=True)
    oc.mkdir(parents=True)
    shutil.copyfile(efi, boot / 'BOOTX64.EFI')
    shutil.copyfile(child, boot / 'NXTEST.EFI')
    interactive = kind != 'direct-error'
    entries = [dict(Name='Expected failure', Enabled=True,
                    Path='\\EFI\\BOOT\\MISSING.EFI' if kind == 'load-error' else '\\EFI\\BOOT\\NXTEST.EFI',
                    Arguments='' if kind == 'load-error' else 'nextcore-child-error')]
    if interactive:
        entries.append(dict(Name='Authored working child', Enabled=True, Path='\\EFI\\BOOT\\NXTEST.EFI'))
    (oc / 'config.plist').write_bytes(plistlib.dumps(dict(Misc=dict(Boot=dict(ShowPicker=interactive), Entries=entries))))
    variables = out / 'vars.fd'
    shutil.copyfile('/usr/share/OVMF/OVMF_VARS_4M.fd', variables)
    serial, qmp = out / 'serial.log', out / 'qmp.sock'
    command = ['qemu-system-x86_64', '-machine', 'q35,accel=tcg,smm=off', '-cpu', 'Nehalem',
        '-m', '256', '-smp', '1', '-display', 'none', '-vga', 'std', '-net', 'none', '-no-reboot',
        '-serial', f'file:{serial}', '-qmp', f'unix:{qmp},server=on,wait=off',
        '-drive', 'if=pflash,format=raw,readonly=on,file=/usr/share/OVMF/OVMF_CODE_4M.fd',
        '-drive', f'if=pflash,format=raw,file={variables}', '-drive', f'format=raw,file=fat:rw:{out / "esp"}']
    (out / 'command.json').write_text(json.dumps(command, indent=2))
    def text():
        return re.sub(r'\x1b\[[0-?]*[ -/]*[@-~]', '', serial.read_text(errors='replace')) if serial.exists() else ''
    deadline = time.monotonic() + 30
    def wait(predicate):
        while time.monotonic() < deadline and process.poll() is None:
            if predicate():
                return
            time.sleep(.05)
        raise RuntimeError('required firmware observation timed out')
    error = None
    with (out / 'stdout.log').open('wb') as stdout, (out / 'stderr.log').open('wb') as stderr:
        process = subprocess.Popen(command, stdout=stdout, stderr=stderr)
        try:
            wait(qmp.exists)
            with socket.socket(socket.AF_UNIX) as connection:
                connection.settimeout(3)
                connection.connect(str(qmp))
                stream = connection.makefile('rwb', buffering=0)
                json.loads(stream.readline())
                sequence = 0
                def execute(name, arguments=None):
                    nonlocal sequence
                    sequence += 1
                    stream.write((json.dumps(dict(execute=name, arguments=arguments or {}, id=sequence)) + '\n').encode())
                    while True:
                        answer = json.loads(stream.readline())
                        if answer.get('id') == sequence:
                            if 'error' in answer:
                                raise RuntimeError(str(answer['error']))
                            return
                def key(name):
                    execute('human-monitor-command', {'command-line': f'sendkey {name} 80'})
                    time.sleep(.12)
                execute('qmp_capabilities')
                if interactive:
                    wait(lambda: 'PICKER_READY' in text())
                    key('ret')
                    wait(lambda: 'NEXTCORE: BOOT_FAILED index=0' in text())
                    key('ret')
                    wait(lambda: 'NEXTCORE: PICKER_RETRY' in text() and text().count('PICKER_READY') >= 2)
                    key('down')
                    wait(lambda: re.search(r'PICKER_READY renderer=\w+ selected=1', text()) is not None)
                    key('ret')
                    wait(lambda: 'NEXTCORE: IMAGE_RETURN status=SUCCESS' in text())
                else:
                    wait(lambda: 'NEXTCORE: IMAGE_RETURN status=ABORTED' in text())
                    time.sleep(.2)
                stream.close()
        except Exception as exception:
            error = str(exception)
        finally:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=3)
    log = text()
    checks = dict(no_observation_error=error is None,
        real_child='NXTEST: EFI_ENTRY' in log,
        input_copies=sha(efi) == sha(boot / 'BOOTX64.EFI') and sha(child) == sha(boot / 'NXTEST.EFI'))
    if interactive:
        checks.update(retry=log.count('NEXTCORE: PICKER_RETRY') == 1,
                      selected_next='NEXTCORE: PICKER_BOOT index=1' in log,
                      success='NXTEST: OPTIONS_EMPTY' in log and 'NEXTCORE: IMAGE_RETURN status=SUCCESS' in log,
                      original_failure=('NEXTCORE: IMAGE_LOAD_ERROR' if kind == 'load-error' else 'NEXTCORE: IMAGE_RETURN status=ABORTED') in log)
    else:
        checks.update(no_retry='PICKER_RETRY' not in log and 'PICKER_BEGIN' not in log,
                      original_status='NEXTCORE: IMAGE_RETURN status=ABORTED' in log)
    return dict(case=kind, passed=all(checks.values()), checks=checks, error=error)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--efi', required=True, type=Path)
    parser.add_argument('--child', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    efi, child = args.efi.resolve(strict=True), args.child.resolve(strict=True)
    before = [sha(efi), sha(child)]
    cases = [run_case(out, efi, child, kind) for kind in ('load-error', 'child-error', 'direct-error')]
    result = dict(passed=all(c['passed'] for c in cases) and before == [sha(efi), sha(child)],
                  cases=cases, efi_sha256=before[0], child_sha256=before[1], macos_boot_verified=False,
                  physical_hardware_verified=False)
    (out / 'report.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
