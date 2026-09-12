#!/usr/bin/env python3
"""Actual production EFI configuration recovery through authored protocol hooks."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import plistlib
import re
import shutil
import signal
import socket
import subprocess
import time

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def run_case(args, case):
    out=args.output/f'case-{case}'
    esp=out/'esp'
    for p in ('EFI/BOOT','EFI/NEXTCORE','EFI/OC'):
        (esp/p).mkdir(parents=True,exist_ok=True)
    wrapper=args.probe.read_bytes()
    marker=b'NXCONFIG_CASE=00!'
    assert wrapper.count(marker)==1
    (esp/'EFI/BOOT/BOOTX64.EFI').write_bytes(wrapper.replace(marker,f'NXCONFIG_CASE={case:02d}!'.encode()))
    shutil.copyfile(args.efi,esp/'EFI/NEXTCORE/BASELINE.EFI')
    shutil.copyfile(args.child,esp/'EFI/NEXTCORE/NXTEST.EFI')
    config=dict(Misc=dict(Boot=dict(ShowPicker=False),Entries=[dict(Name='Authored child',Enabled=True,Path='\\EFI\\NEXTCORE\\NXTEST.EFI')]))
    if case in (0,1,9):
        data=plistlib.dumps(config)
    elif case==3:
        data=b''
    elif case==4:
        data=b'not a plist'
    elif case==5:
        data=plistlib.dumps(dict(Misc=dict(Boot=dict(ShowPicker=False),Entries=[])))
    else:
        data=None
    if data is not None:
        (esp/'EFI/OC/config.plist').write_bytes(data)
    variables=out/'vars.fd'
    shutil.copyfile('/usr/share/OVMF/OVMF_VARS_4M.fd',variables)
    serial=out/'serial.log';qmp=out/'qmp.sock'
    command=['qemu-system-x86_64','-machine','q35,accel=tcg,smm=off','-cpu','Nehalem','-m','256','-smp','1','-display','none','-vga','std','-net','none','-no-reboot','-serial',f'file:{serial}','-qmp',f'unix:{qmp},server=on,wait=off','-drive','if=pflash,format=raw,readonly=on,file=/usr/share/OVMF/OVMF_CODE_4M.fd','-drive',f'if=pflash,format=raw,file={variables}','-drive',f'format=raw,file=fat:rw:{esp}']
    (out/'command.json').write_text(json.dumps(command,indent=2))
    def text():
        raw=serial.read_bytes() if serial.exists() else b''
        complete=raw[:raw.rfind(b'\n')+1].decode(errors='replace').replace('\r\n','\n')
        return re.sub(r'\x1b\[[0-?]*[ -/]*[@-~]','',complete)
    def terminal():
        return re.search(r'^NXCONFIG: RETURN case=\d+ status=\w+ opens=\d+ injected=\d+\n',text(),re.M) is not None
    started=time.monotonic()
    # Six seconds reserved for TERM/KILL and wait within the 45-second case cap.
    deadline=started+39
    def wait(predicate):
        while time.monotonic()<deadline and process.poll() is None:
            if predicate():return
            if terminal():raise RuntimeError('firmware returned before required recovery observation')
            time.sleep(.05)
        raise RuntimeError('firmware observation timeout')
    error=None;stopped_by_host=False
    with (out/'qemu.log').open('wb') as log:
        process=subprocess.Popen(command,stdout=log,stderr=log,start_new_session=True)
        try:
            wait(qmp.exists)
            with socket.socket(socket.AF_UNIX) as connection:
                connection.settimeout(3);connection.connect(str(qmp));stream=connection.makefile('rwb',buffering=0);json.loads(stream.readline())
                sequence=0
                def execute(name,arguments=None):
                    nonlocal sequence
                    sequence+=1
                    stream.write((json.dumps(dict(execute=name,arguments=arguments or {},id=sequence))+'\n').encode())
                    while True:
                        answer=json.loads(stream.readline())
                        if answer.get('id')==sequence:
                            if 'error' in answer:raise RuntimeError(str(answer['error']))
                            return
                def key(name):
                    execute('human-monitor-command',{'command-line':f'sendkey {name} 80'});time.sleep(.15)
                execute('qmp_capabilities')
                if case in (1,2,3,4,5,7,9):
                    wait(lambda:'CONFIG_RECOVERY_READY' in text())
                    execute('screendump',{'filename':str(out/'recovery-screen.ppm')})
                    # An idle recovery screen must not load a child or reread.
                    time.sleep(.25)
                    assert 'NXTEST: EFI_ENTRY' not in text() and 'attempt=2 ' not in text()
                    key('ret')
                    if case in (2,3,4,5):
                        wait(lambda:'attempt=2 ' in text() and text().count('CONFIG_RECOVERY_READY')>=2)
                        key('esc')
                wait(terminal)
                stream.close()
        except Exception as e:
            error=str(e)
        finally:
            if process.poll() is None:
                stopped_by_host=True
                os.killpg(process.pid,signal.SIGTERM)
                try:process.wait(timeout=3)
                except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);process.wait(timeout=3)
    log=text()
    status={0:'SUCCESS',1:'SUCCESS',2:'NOT_FOUND',3:'BAD_BUFFER_SIZE',4:'INVALID_PARAMETER',5:'NOT_FOUND',6:'DEVICE_ERROR',7:'DEVICE_ERROR',8:'UNSUPPORTED',9:'SUCCESS'}[case]
    checks=dict(observed=error is None,terminal=f'NXCONFIG: RETURN case={case} status={status}' in log,
        child_policy=('NXTEST: EFI_ENTRY' in log)==(case in (0,1,9)),
        original_images_preserved=sha(args.efi)==sha(esp/'EFI/NEXTCORE/BASELINE.EFI') and sha(args.child)==sha(esp/'EFI/NEXTCORE/NXTEST.EFI'),
        no_setup_error='NXCONFIG: SETUP_ERROR' not in log)
    if case==0:checks['no_recovery']='CONFIG_RECOVERY_BEGIN' not in log
    if case in (1,9):checks.update(first_injected=('injected=1' if case==1 else 'injected=2') in log,retried='CONFIG_RECOVERY_ACTION retry' in log and 'opens=2 ' in log,read_after_input=log.find('CONFIG_RECOVERY_ACTION retry')<log.find('attempt=2 '))
    if case in (2,3,4,5):checks.update(retry_then_escape='CONFIG_RECOVERY_ACTION retry' in log and 'CONFIG_RECOVERY_ACTION exit' in log,exact_rereads='opens=2 ' in log)
    if case==9:checks['clear_failure_continues']='CONFIG_RECOVERY_DISPLAY_WARNING operation=clear status=DEVICE_ERROR' in log and 'CONFIG_RECOVERY_READY' in log
    if case==6:checks['no_false_screen']='CONFIG_RECOVERY_READY' not in log
    if case in (6,7,8):checks['actual_error']=f'CONFIG_RECOVERY_ERROR status={status}' in log
    if case!=0:
        checks['exact_path_reason']='CONFIG_RECOVERY_BEGIN path=\\EFI\\OC\\config.plist reason=' in log
    if case==3:checks['empty_reason']='Configuration file is empty: BAD_BUFFER_SIZE' in log
    if case==4:checks['parse_repeated']=log.count('NEXTCORE: CONFIG_INVALID reason=')==2
    if case==5:checks['no_entry_reason']='reason=No enabled boot entries' in log
    checks['process_reaped']=process.poll() is not None
    return dict(case=case,passed=all(checks.values()),checks=checks,error=error,serial_sha256=sha(serial),
        elapsed_seconds=time.monotonic()-started,exit_code=process.returncode,stopped_by_host=stopped_by_host,process_reaped=process.poll() is not None,
        child_observed='NXTEST: EFI_ENTRY' in log,screenshot_sha256=sha(out/'recovery-screen.ppm') if (out/'recovery-screen.ppm').exists() else None)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('efi','probe','child','output'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--cases',type=int,nargs='+',default=list(range(10)),choices=range(10))
    args=p.parse_args();args.output=args.output.resolve();args.output.mkdir(parents=True,exist_ok=False)
    for name in ('efi','probe','child'):setattr(args,name,getattr(args,name).resolve(strict=True))
    before={name:sha(getattr(args,name)) for name in ('efi','probe','child')}
    root=Path(__file__).resolve().parents[1]
    sources=[Path(__file__).resolve(),root/'nextcore/crates/nextcore-efi/src/config_recovery_probe.rs',root/'nextcore/crates/nextcore-efi/src/main.rs',root/'nextcore/crates/nextcore-efi/src/configuration_recovery.rs',root/'nextcore/crates/nextcore-efi/Cargo.toml']
    source_hashes={str(s.relative_to(root)):sha(s) for s in sources}
    cases=[run_case(args,i) for i in args.cases]
    result=dict(passed=all(c['passed'] for c in cases),cases=cases,input_sha256=before,physical_hardware_verified=False,macos_boot_verified=False)
    assert before=={name:sha(getattr(args,name)) for name in before}
    result['source_sha256']=source_hashes
    result['sources_preserved']=source_hashes=={str(s.relative_to(root)):sha(s) for s in sources}
    result['passed'] &= result['sources_preserved']
    (args.output/'report.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result));return 0 if result['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
