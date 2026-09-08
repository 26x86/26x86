"""Publish one validated incremental module without history rewriting."""
import argparse, hashlib, json, pathlib, subprocess
BASE=pathlib.Path(__file__).resolve().parent
parser=argparse.ArgumentParser();parser.add_argument('module',choices=['Core','GPU','HAL','ISE','APLS','EFI','Tool']);args=parser.parse_args()
name='Nextcore-'+args.module;repo=BASE/name
prepared=json.loads((BASE/(name+'-prepared.json')).read_text())
gate=json.loads((BASE/'gates/pre'/name/'receipt.json').read_text())
assert gate['passed'] and gate['source_commit']==prepared['source_commit']

def git(*argv):
    p=subprocess.run(['git',*argv],cwd=repo,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    if p.returncode: raise RuntimeError(str(argv)+': '+p.stderr.decode(errors='replace'))
    return p.stdout

def remote(ref):
    data=git('ls-remote','origin',ref).decode().strip()
    return data.split()[0] if data else None

if remote('refs/heads/main')!=prepared['previous_head']: raise ValueError('remote main advanced; stop and review')
if remote('refs/tags/'+prepared['tag']) is not None: raise ValueError('tag already exists')
for row in prepared['files']:
    content=(repo/row['path']).read_bytes()
    assert len(content)==row['bytes'] and hashlib.sha256(content).hexdigest()==row['sha256'],row['path']
git('add','-A')
paths=git('ls-files','-z').decode().split('\0')[:-1]
expected={x['path'] for x in prepared['files']}|{'repository.json','repository-files.json'}
assert set(paths)==expected,(set(paths)-expected,expected-set(paths))
for row in prepared['files']:
    content=git('show',':'+row['path'])
    assert len(content)==row['bytes'] and hashlib.sha256(content).hexdigest()==row['sha256'],'index mismatch '+row['path']
git('-c','user.name=26x86 release tooling','-c','user.email=release@26x86.local','commit','-m',f'Release NextCore {args.module} v0.1.1 from {prepared["source_commit"][:7]}')
head=git('rev-parse','HEAD').decode().strip()
assert git('rev-parse','HEAD^').decode().strip()==prepared['previous_head']
git('tag',prepared['tag'])
push=git('push','--atomic','origin','HEAD:refs/heads/main','refs/tags/'+prepared['tag']).decode()
assert remote('refs/heads/main')==head and remote('refs/tags/'+prepared['tag'])==head
assert not git('status','--porcelain')
result={'repository':'26x86/'+name,'tag':prepared['tag'],'source_commit':prepared['source_commit'],'previous_head':prepared['previous_head'],'head':head,'main_and_tag_match':True,'parent_matches_previous_head':True,'pre_gate_passed':True,'inventory_index_verified':True,'force_push':False,'atomic_push':True}
(BASE/(name+'-published.json')).write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
