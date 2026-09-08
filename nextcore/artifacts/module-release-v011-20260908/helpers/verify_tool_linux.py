"""Independent single-repository Linux gate; siblings cannot satisfy fixtures."""
import argparse,hashlib,json,os,pathlib,subprocess,time
parser=argparse.ArgumentParser();parser.add_argument('phase',choices=['pre','post']);parser.add_argument('--attempt',type=int,default=1);args=parser.parse_args()
label=args.phase if args.attempt==1 else args.phase+'-r'+str(args.attempt)
record=pathlib.Path(__file__).resolve().parent/'tool-v012'
prepared=json.loads((record/'prepared.json').read_text())
base=pathlib.Path('/tmp/nextcore-tool-v012-'+label+'-20260908')
base.mkdir(exist_ok=False)
repo=base/'module'
source=('/mnt/c/Users/Admin/AppData/Local/Temp/nextcore-modules-v011-20260908-153614/Nextcore-Tool' if args.phase=='pre' else 'https://github.com/26x86/Nextcore-Tool.git')
commands=[]
def run(argv,cwd=None,timeout=300):
 start=time.monotonic()
 env=os.environ.copy();env['CARGO_TERM_COLOR']='never';env['PATH']='/home/developer/.cargo/bin:'+env.get('PATH','')
 result=subprocess.run(argv,cwd=cwd,env=env,capture_output=True,timeout=timeout)
 n=len(commands)
 (record/f'{label}-{n}.stdout').write_bytes(result.stdout)
 (record/f'{label}-{n}.stderr').write_bytes(result.stderr)
 commands.append({'argv':argv,'exit_code':result.returncode,'elapsed_seconds':round(time.monotonic()-start,3)})
 if result.returncode: raise RuntimeError(result.stderr.decode(errors='replace')[-4000:])
 return result.stdout
result={'phase':args.phase,'attempt':args.attempt,'source_commit':prepared['source_commit'],'expected_head':prepared['head'],'single_repo_parent':str(base),'passed':False,'commands':commands,'guest_execution_claimed':False}
try:
 run(['git','clone','--no-local',source,str(repo)],timeout=60)
 assert run(['git','rev-parse','HEAD'],repo).decode().strip()==prepared['head']
 assert sorted(p.name for p in base.iterdir())==['module']
 inventory=json.loads((repo/'repository-files.json').read_text())['files']
 for row in inventory:
  content=(repo/row['path']).read_bytes();assert hashlib.sha256(content).hexdigest()==row['sha256'],row['path']
 assert b'include_bytes!("data/sample.plist")' in (repo/'tests/bundle_cli.rs').read_bytes()
 run(['cargo','test','--all-targets'],repo)
 result['lock_sha256']=hashlib.sha256((repo/'Cargo.lock').read_bytes()).hexdigest()
 result['passed']=True
except Exception as failure:
 result['error']=str(failure)
finally:
 (record/(label+'-linux-receipt.json')).write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps(result,indent=2))
raise SystemExit(0 if result['passed'] else 1)
