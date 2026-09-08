"""Prepare fixed-commit public snapshots in existing clones; never push."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess

ROOT = Path(r'C:\Users\Admin\Documents\ChatGPT\26x86darwin')
BASE = Path(__file__).resolve().parent
MODULES = [
 ('Core','core boot configuration and public format codecs',()),
 ('GPU','graphics API contracts and an optional host Vulkan backend',()),
 ('HAL','public ACPI, PCI, SMBIOS and device-tree metadata',()),
 ('ISE','instruction-set emulation and CPU feature policy',()),
 ('APLS','AArch64 recovery orchestration and public guest interfaces',('GPU',)),
 ('EFI','UEFI boot selection, platform services and bounded kernel preparation',('Core',)),
 ('Tool','command-line preparation and orchestration',('Core','APLS')),
]
GENERATED = {'.gitignore','.gitattributes','.github/workflows/ci.yml','README.md','LICENSE.txt','repository.json','repository-files.json'}
DENIED = {'_isolated','artifacts','target','.git'}

def run(*argv, cwd=None):
    result = subprocess.run(argv,cwd=cwd,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    if result.returncode:
        raise RuntimeError(f'{argv!r}: {result.stderr.decode(errors="replace")}')
    return result.stdout

def safe(path):
    p=PurePosixPath(path)
    if p.is_absolute() or not p.parts or any(x in ('.','..') or x.lower() in DENIED for x in p.parts):
        raise ValueError(f'prohibited export path: {path}')
    return p

def blob(commit,path):
    return run('git','show',f'{commit}:{path}',cwd=ROOT)

def tag(short):
    return f'26x86-Nextcore-{short}-v0.1.1'

def workflow(short):
    commands = ['cargo test --all-targets']
    if short == 'Core': commands += ['cargo check --no-default-features']
    if short == 'GPU': commands += ['cargo test --all-targets --features vulkan']
    if short == 'EFI': commands=['rustup target add x86_64-unknown-uefi','cargo check --target x86_64-unknown-uefi --all-features']
    return ('name: NextCore '+short+' CI\non:\n  push:\n  pull_request:\n  workflow_dispatch:\n'
      'permissions:\n  contents: read\njobs:\n  verify:\n    runs-on: ubuntu-24.04\n    steps:\n'
      '      - uses: actions/checkout@v4\n      - uses: dtolnay/rust-toolchain@stable\n'+
      ''.join('      - run: '+c+'\n' for c in commands)).encode()

def prepare(commit):
    canonical=run('git','rev-parse',commit+'^{commit}',cwd=ROOT).decode().strip()
    if canonical != commit: raise ValueError('full immutable commit required')
    output=[]
    for short,description,deps in MODULES:
        name='Nextcore-'+short
        repo=BASE/name
        if run('git','status','--porcelain',cwd=repo): raise ValueError(f'non-clean clone: {name}')
        head=run('git','rev-parse','HEAD',cwd=repo).decode().strip()
        if head != run('git','rev-parse','origin/main',cwd=repo).decode().strip(): raise ValueError('unexpected local history')
        if run('git','ls-remote','--tags','origin','refs/tags/'+tag(short),cwd=repo): raise ValueError('release tag exists')
        previous=json.loads(run('git','show','HEAD:repository.json',cwd=repo))
        inventory=json.loads(run('git','show','HEAD:repository-files.json',cwd=repo))
        managed={r['path'] for r in inventory['files']} | GENERATED
        tracked=run('git','ls-files','-z',cwd=repo).decode().split('\0')[:-1]
        payload={p:run('git','show','HEAD:'+p,cwd=repo) for p in tracked if p not in managed}
        prefix='nextcore/crates/nextcore-'+short.lower()+'/'
        entries=run('git','ls-tree','-r','-z',commit,'--',prefix,cwd=ROOT).split(b'\0')[:-1]
        source_files=[]
        for entry in entries:
            header,path=entry.split(b'\t',1)
            mode,kind,_oid=header.split()
            path=path.decode()
            if kind!=b'blob' or mode not in (b'100644',b'100755') or not path.startswith(prefix): raise ValueError('unsupported git object')
            relative=path[len(prefix):]
            safe(relative)
            content=blob(commit,path)
            payload[relative]=content
            source_files.append({'path':relative,'source_path':path,'bytes':len(content),'sha256':hashlib.sha256(content).hexdigest()})
        if not source_files: raise ValueError('empty source crate')
        manifest=payload['Cargo.toml'].decode()
        for dep in deps:
            slug=dep.lower()
            expression=r'(nextcore-'+slug+r'\s*=\s*\{\s*)path\s*=\s*"\.\./nextcore-'+slug+r'"'
            manifest,n=re.subn(expression,lambda m:m[1]+f'git = "https://github.com/26x86/Nextcore-{dep}.git", tag = "{tag(dep)}"',manifest)
            if n!=1: raise ValueError(f'expected exactly one dependency {dep}')
        if re.search(r'path\s*=\s*"\.\./nextcore-',manifest): raise ValueError('unrewritten sibling dependency')
        payload['Cargo.toml']=manifest.encode()
        payload['LICENSE.txt']=blob(commit,'LICENSE.txt')
        payload['.gitignore']=b'/target/\nCargo.lock\n'
        payload['.gitattributes']=b'* text=auto\n*.S text eol=lf\n'
        readme=f'# NextCore {short}\n\n{description[0].upper()+description[1:]}.\n\n'
        readme+=f'Clean-room module from [26x86](https://github.com/26x86/26x86), source commit `{commit}`.\n\n'
        readme+=f'Repository snapshot: `{tag(short)}`. Package version is preserved from that source.\n\n'
        readme+='Public source only; no Apple firmware, operating-system binaries or private research inputs. Module checks do not establish macOS boot, guest Metal or physical hardware support.\n'
        if deps:
            readme+='\n## Fixed dependencies\n\n'+''.join(f'- [{dep}](https://github.com/26x86/Nextcore-{dep}/tree/{tag(dep)})\n' for dep in deps)
        payload['README.md']=readme.encode()
        payload['.github/workflows/ci.yml']=workflow(short)
        for path in payload: safe(path)
        for path in managed-set(payload):
            safe(path)
            target=repo/path
            if target.exists():
                if not target.is_file(): raise ValueError('refusing non-file removal')
                target.unlink()
        for path,content in payload.items():
            target=repo/path
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(content)
        metadata=dict(previous)
        metadata.update(source_commit=commit,release_tag=tag(short),previous_head=head,
          description=description,generated_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
          dependency_tags={f'26x86/Nextcore-{d}':tag(d) for d in deps},
          export_method='immutable git objects applied to existing main; manifest dependency rewrite only')
        (repo/'repository.json').write_text(json.dumps(metadata,indent=2)+'\n',encoding='utf-8')
        rows=[{'path':p,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()} for p,b in sorted(payload.items())]
        (repo/'repository-files.json').write_text(json.dumps({'schema':'26x86.repository-files/1','files':rows},indent=2)+'\n',encoding='utf-8')
        receipt={'repository':f'26x86/{name}','path':str(repo),'source_commit':commit,'previous_head':head,'tag':tag(short),'source_files':source_files,'files':rows,
          'transformed_source_files':['Cargo.toml'] if deps else [],'forbidden_paths_present':False,'existing_history_preserved':True,'package_version_preserved':True}
        (BASE/(name+'-prepared.json')).write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
        output.append({'repository':name,'source_files':len(source_files),'export_files':len(rows),'previous_head':head,'tag':tag(short)})
    (BASE/'prepared.json').write_text(json.dumps(output,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(output,indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--source-commit',required=True)
    args=parser.parse_args()
    prepare(args.source_commit)
