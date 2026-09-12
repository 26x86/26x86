import pathlib,hashlib,json,shutil,socket,struct,subprocess,time,os,signal
out=pathlib.Path(__file__).parent
commands=[]
class Options:qemu='qemu-system-aarch64'
a=Options()
cmd=['clang-18','--target=aarch64-none-elf','-march=armv8-a+sve','-nostdlib','-Wl,-Ttext=0x40080000','-Wl,-e,_start',str(out/'probe.S'),'-o',str(out/'probe.elf')]
commands.append(cmd)
p=subprocess.run(cmd,capture_output=True,timeout=30);(out/'build.log').write_bytes(p.stdout+p.stderr);assert p.returncode==0
qemu=shutil.which(a.qemu);assert qemu;ep=out/'qmp.sock';cmd=[qemu,'-machine','virt,virtualization=off,secure=off','-cpu','max,sve=off,sme=off','-m','128','-display','none','-serial','none','-monitor','none','-nic','none','-qmp',f'unix:{ep},server=on,wait=off','-kernel',str(out/'probe.elf')];commands.append(cmd)
with (out/'qemu.log').open('wb') as log:
 proc=subprocess.Popen(cmd,stdout=log,stderr=log,start_new_session=True)
 try:
  deadline=time.monotonic()+20
  while not ep.exists() and time.monotonic()<deadline:time.sleep(.05)
  with socket.socket(socket.AF_UNIX) as sock:
   sock.settimeout(5);sock.connect(str(ep));stream=sock.makefile('rwb',buffering=0);json.loads(stream.readline())
   def qmp(execute,arguments=None):
    v={'execute':execute}
    if arguments is not None:v['arguments']=arguments
    stream.write((json.dumps(v)+'\n').encode())
    while True:
     v=json.loads(stream.readline());assert 'error' not in v,v
     if 'return' in v:return v['return']
   qmp('qmp_capabilities')
   while time.monotonic()<deadline:
    regs=qmp('human-monitor-command',{'command-line':'info registers'})
    if 'X00=000000000000064e' in regs:break
    time.sleep(.05)
   else:raise AssertionError(regs)
   qmp('stop');qmp('human-monitor-command',{'command-line':f'pmemsave 0x40100000 160 "{out / "oracle-results.bin"}"'})
 finally:
  if proc.poll() is None:os.killpg(proc.pid,signal.SIGTERM)
  try:proc.wait(timeout=5)
  except subprocess.TimeoutExpired:
   os.killpg(proc.pid,signal.SIGKILL);proc.wait(timeout=5)

raw=(out/'oracle-results.bin').read_bytes();v=struct.unpack('<20Q',raw)
records=[]
for i,name in enumerate(['ID_AA64PFR0_EL1','ID_AA64PFR1_EL1','ID_AA64ZFR0_EL1','NEGATIVE_UDF']):
 value,esr,elr,trapped=v[4+i*4:8+i*4];records.append(dict(register=name,value=hex(value),esr=hex(esr),elr=hex(elr),trapped=bool(trapped)))
assert v[0]==4 and not any(x['trapped'] for x in records[:3]) and records[3]['trapped']
assert ((v[4]>>8)&15)==0 and ((v[4]>>32)&15)==0 and ((v[8]>>24)&15)==0
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
receipt=dict(passed=True,initial_currentel=hex(v[0]),initial_sctlr_el1=hex(v[1]),records=records,cpu='max,sve=off,sme=off',machine='virt,virtualization=off,secure=off',accelerator='TCG',el2_absent=True,hcr_el2_written=False,hcr_scope='EL2 absent; no accessible EL2 control register was written.',qemu_version=subprocess.check_output([qemu,'--version'],text=True).splitlines()[0],qemu_sha256=sha(pathlib.Path(qemu)),commands=commands,process_reaped=proc.poll() is not None,source_sha256=sha(out/'probe.S'),elf_sha256=sha(out/'probe.elf'),result_sha256=sha(out/'oracle-results.bin'),original_inputs_used=False,physical_boot_verified=False)
(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
