import pathlib,hashlib,json,shutil,socket,struct,subprocess,time,os,signal,argparse
ap=argparse.ArgumentParser();ap.add_argument('--qemu',required=True);ap.add_argument('--output',required=True);a=ap.parse_args()
base=pathlib.Path('/tmp/nextcore-pac-frac-qualification-20260913-r1');out=pathlib.Path(a.output);out.mkdir(parents=True,exist_ok=True)
for name in ['probe.S','manifest.json','rust-results.txt']:shutil.copyfile(base/name,out/name)
manifest=json.loads((out/'manifest.json').read_text());sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
commands=[];start=time.monotonic();deadline=start+30;proc=None;failure=None;regs='';stopped=False;killed=False
cmd=['clang-18','--target=aarch64-none-elf','-nostdlib','-Wl,-Ttext=0x40080000','-Wl,-e,_start',str(out/'probe.S'),'-o',str(out/'probe.elf')];commands.append(cmd)
p=subprocess.run(cmd,capture_output=True,timeout=15);(out/'build.log').write_bytes(p.stdout+p.stderr);assert p.returncode==0,p.stderr
qemu=shutil.which(a.qemu);assert qemu;ep=out/'qmp.sock';assert not ep.exists()
cmd=[qemu,'-machine','virt,virtualization=off,secure=off','-cpu','neoverse-v1','-accel','tcg','-m','128','-display','none','-serial','none','-monitor','none','-nic','none','-qmp',f'unix:{ep},server=on,wait=off','-kernel',str(out/'probe.elf')];commands.append(cmd)
with (out/'qemu.log').open('wb') as log:
 proc=subprocess.Popen(cmd,stdout=log,stderr=log,start_new_session=True)
 try:
  while not ep.exists():
   if proc.poll() is not None:raise RuntimeError('QEMU exited before QMP')
   if time.monotonic()>deadline-8:raise TimeoutError('QMP connection deadline')
   time.sleep(.02)
  with socket.socket(socket.AF_UNIX) as sock:
   sock.settimeout(2);sock.connect(str(ep));stream=sock.makefile('rwb',buffering=0);json.loads(stream.readline())
   def qmp(execute,arguments=None):
    v={'execute':execute}
    if arguments is not None:v['arguments']=arguments
    stream.write((json.dumps(v)+'\n').encode())
    while True:
     line=stream.readline()
     if not line:raise EOFError('QMP EOF')
     v=json.loads(line)
     if 'error' in v:raise RuntimeError(v)
     if 'return' in v:return v['return']
   qmp('qmp_capabilities')
   while time.monotonic()<deadline-8:
    regs=qmp('human-monitor-command',{'command-line':'info registers'})
    if 'X00=000000000000064e' in regs or 'X00=0000000000000bad' in regs:break
    time.sleep(.02)
   else:raise TimeoutError('Guest completion deadline')
   qmp('stop');stopped=True
   qmp('human-monitor-command',{'command-line':f'pmemsave 0x40100000 {(4+48*8)*8} "{out / "results.bin"}"'})
   if 'X00=0000000000000bad' in regs:raise RuntimeError('Guest synchronous exception; see x20 ESR and x21 ELR')
 except Exception as e:failure=repr(e)
 finally:
  if proc.poll() is None:os.killpg(proc.pid,signal.SIGTERM)
  try:proc.wait(timeout=3)
  except subprocess.TimeoutExpired:
   killed=True;os.killpg(proc.pid,signal.SIGKILL);proc.wait(timeout=3)
(out/'registers.txt').write_text(regs)
receipt=dict(completed=failure is None,failure=failure,commands=commands,elapsed_seconds=time.monotonic()-start,qemu_returncode=proc.returncode,process_reaped=proc.poll() is not None,qmp_stopped=stopped,kill_fallback=killed,qemu_sha256=sha(qemu),qemu_version=subprocess.check_output([qemu,'--version'],text=True).splitlines()[0],source_sha256=sha(out/'probe.S'),manifest_sha256=sha(out/'manifest.json'),elf_sha256=sha(out/'probe.elf'),original_inputs_used=False,architecture_oracle_qualification='Actual QEMU observations only; asymmetric AddPAC must separately agree with Arm primary pseudocode.')
if (out/'results.bin').exists():
 raw=(out/'results.bin').read_bytes();vals=struct.unpack('<388Q',raw);receipt['header']=dict(zip(manifest['header'],[hex(x) for x in vals[:4]]));receipt['results_sha256']=sha(out/'results.bin')
 expected=[[int(x,16) for x in line.split()] for line in (out/'rust-results.txt').read_text().splitlines()];records=[];diff=[]
 for i,row in enumerate(manifest['rows']):
  v=vals[4+i*8:12+i*8];records.append(dict(input=row,output=dict(zip(manifest['record'],[hex(x) for x in v]))))
  if list(v[2:])!=expected[i]:diff.append(i)
 receipt['observed_el1']=vals[0]==4;receipt['observed_vector_count']=vals[3];receipt['observed_APA']=(vals[1]>>4)&15;receipt['observed_PAC_frac']=(vals[2]>>24)&15;receipt['register_controls_match_manifest']=all(int(row['tcr'],16)==vals[4+i*8] and int(manifest['sctlr'],16)==vals[5+i*8] for i,row in enumerate(manifest['rows']));receipt['rust_differing_rows']=diff;receipt['records']=records
(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({k:v for k,v in receipt.items() if k not in ['records','commands']}))
if failure:raise SystemExit(1)
