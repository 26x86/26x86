#!/usr/bin/env python3
"""Fetch the exact unmodified GuC test fixture; verify hash, never load/flash it."""
import argparse
import hashlib
import json
from pathlib import Path
import urllib.request

p=argparse.ArgumentParser()
p.add_argument('--output',required=True,type=Path,help='New scratch file; does not overwrite a different existing file.')
args=p.parse_args()
meta=json.loads(Path(__file__).with_name('xe_submission_provenance.json').read_text(encoding='utf-8'))['firmware']
if args.output.exists():
    data=args.output.read_bytes()
else:
    request=urllib.request.Request(meta['url'],headers={'User-Agent':'Mellow-firmware-fixture/1'})
    with urllib.request.urlopen(request,timeout=30) as stream:data=stream.read(meta['bytes']+1)
if len(data)!=meta['bytes'] or hashlib.sha256(data).hexdigest()!=meta['sha256']:
    raise SystemExit('Size/hash mismatch: no file written, no firmware loaded.')
if not args.output.exists():
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open('xb') as stream:stream.write(data)
print(json.dumps({'path':str(args.output.resolve()),'sha256':meta['sha256'],'bytes':len(data),
                  'hardware_authenticated':False,'action':'download/read verification only'},indent=2))
