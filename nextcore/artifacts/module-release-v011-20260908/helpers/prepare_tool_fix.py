import hashlib,json,pathlib,re,subprocess
base=pathlib.Path(__file__).resolve().parent
root=pathlib.Path(r'C:\Users\Admin\Documents\ChatGPT\26x86darwin')
repo=base/'Nextcore-Tool';out=base/'tool-v012';out.mkdir(exist_ok=False)
source='045065700cbd037eaaa974faf957ba15cb628370'
release='26x86-Nextcore-Tool-v0.1.2'
def git(cwd,*args):
 p=subprocess.run(['git',*args],cwd=cwd,capture_output=True,check=True);return p.stdout
assert not git(repo,'status','--porcelain')
old=git(repo,'rev-parse','HEAD').decode().strip()
assert old=='f1d26043f3f8c8f4bb663ef9f9b203dbf42c8c2d'
assert git(repo,'ls-remote','origin','refs/heads/main').decode().split()[0]==old
assert not git(repo,'ls-remote','origin','refs/tags/'+release)
meta=json.loads((repo/'repository.json').read_text())
payload={r['path']:git(repo,'show','HEAD:'+r['path']) for r in json.loads((repo/'repository-files.json').read_text())['files']}
prefix='nextcore/crates/nextcore-tool/'
paths=git(root,'ls-tree','-r','--name-only',source,'--',prefix).decode().splitlines()
source_inventory=[]
for path in paths:
 rel=path[len(prefix):]
 assert not any(p in {'..','_isolated','artifacts','target','.git'} for p in pathlib.PurePosixPath(rel).parts)
 raw=git(root,'show',source+':'+path)
 payload[rel]=raw
 source_inventory.append({'path':rel,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
manifest=payload['Cargo.toml'].decode()
for dep in ['Core','APLS']:
 slug=dep.lower()
 old_dep=f'nextcore-{slug} = {{ path = "../nextcore-{slug}" }}'
 new_dep=f'nextcore-{slug} = {{ git = "https://github.com/26x86/Nextcore-{dep}.git", tag = "26x86-Nextcore-{dep}-v0.1.1" }}'
 assert manifest.count(old_dep)==1
 manifest=manifest.replace(old_dep,new_dep)
assert not re.search(r'path\s*=\s*"\.\./nextcore-',manifest)
payload['Cargo.toml']=manifest.encode()
payload['README.md']=payload['README.md'].replace(b'dcc90013109eac694ccbf997b1e44a7018480f78',source.encode()).replace(b'26x86-Nextcore-Tool-v0.1.1',release.encode())
for path,raw in payload.items():
 target=repo/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
meta.update(source_commit=source,release_tag=release,previous_head=old,release_note='Make the authored CLI test fixture crate-local for standalone Linux clones')
(repo/'repository.json').write_text(json.dumps(meta,indent=2)+'\n')
inventory=[{'path':p,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()} for p,raw in sorted(payload.items())]
(repo/'repository-files.json').write_text(json.dumps({'schema':'26x86.repository-files/1','files':inventory},indent=2)+'\n')
git(repo,'add','-A')
expected=set(payload)|{'repository.json','repository-files.json'}
assert set(git(repo,'ls-files','-z').decode().split('\0')[:-1])==expected
for row in inventory:
 raw=git(repo,'show',':'+row['path']);assert hashlib.sha256(raw).hexdigest()==row['sha256']
git(repo,'-c','user.name=26x86 release tooling','-c','user.email=release@26x86.local','commit','-m','Release Tool v0.1.2 with a crate-local CLI fixture')
head=git(repo,'rev-parse','HEAD').decode().strip()
assert git(repo,'rev-parse','HEAD^').decode().strip()==old
result={'source_commit':source,'head':head,'previous_head':old,'tag':release,'dependency_tags':meta['dependency_tags'],'source_inventory':source_inventory,'inventory':inventory,'pushed':False}
(out/'prepared.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in {'inventory','source_inventory'}},indent=2))
