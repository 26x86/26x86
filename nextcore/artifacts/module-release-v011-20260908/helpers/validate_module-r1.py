import argparse, hashlib, json, os, pathlib, subprocess, time
BASE=pathlib.Path(__file__).resolve().parent
NAMES={'Core','GPU','HAL','ISE','APLS','EFI','Tool'}
parser=argparse.ArgumentParser()
parser.add_argument('module',choices=sorted(NAMES))
parser.add_argument('--phase',choices=['pre','post'],default='pre')
args=parser.parse_args()
name='Nextcore-'+args.module
repo=(BASE if args.phase=='pre' else BASE/'verification')/name
out=BASE/'gates'/args.phase/name
out.mkdir(parents=True,exist_ok=False)
meta=json.loads((repo/'repository.json').read_text())
assert meta['source_commit']=='dcc90013109eac694ccbf997b1e44a7018480f78'
assert meta['release_tag']=='26x86-'+name+'-v0.1.1'
inventory=json.loads((repo/'repository-files.json').read_text())['files']
for row in inventory:
    b=(repo/row['path']).read_bytes()
    assert len(b)==row['bytes'] and hashlib.sha256(b).hexdigest()==row['sha256'],row['path']
commands=[['cargo','test','--all-targets']]
if args.module=='Core': commands.append(['cargo','check','--no-default-features'])
if args.module=='GPU': commands.append(['cargo','test','--all-targets','--features','vulkan'])
if args.module=='EFI': commands=[['cargo','check','--target','x86_64-unknown-uefi','--all-features']]
result={'module':name,'phase':args.phase,'source_commit':meta['source_commit'],'inventory_files_verified':len(inventory),'commands':[],'passed':False,'guest_execution_claimed':False}
env=os.environ.copy();env['CARGO_TERM_COLOR']='never'
for i,command in enumerate(commands):
    start=time.monotonic()
    try:
        run=subprocess.run(command,cwd=repo,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=300)
        code=run.returncode; stdout=run.stdout;stderr=run.stderr
    except subprocess.TimeoutExpired as failure:
        code=124;stdout=failure.stdout or b'';stderr=failure.stderr or b''
    (out/f'{i}.stdout').write_bytes(stdout)
    (out/f'{i}.stderr').write_bytes(stderr)
    record={'argv':command,'exit_code':code,'elapsed_seconds':round(time.monotonic()-start,3),'stdout':f'{i}.stdout','stderr':f'{i}.stderr'}
    result['commands'].append(record)
    if code:
        print(stderr.decode(errors='replace')[-5000:])
        break
result['passed']=len(result['commands'])==len(commands) and all(x['exit_code']==0 for x in result['commands'])
(out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
raise SystemExit(0 if result['passed'] else 1)
