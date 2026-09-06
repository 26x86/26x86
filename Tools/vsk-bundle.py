#!/usr/bin/env python3
"""Create/inspect VSK bundles with explicit external keys; no key generation."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from x86.vsk_bundle import BundleError,create_bundle,load_private_key,verify_bundle,_read


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    commands=parser.add_subparsers(dest="command",required=True)
    create=commands.add_parser("create")
    create.add_argument("--config",required=True)
    create.add_argument("--core",required=True)
    create.add_argument("--service",action="append",required=True,metavar="INSTANCE=ELF")
    create.add_argument("--output",required=True)
    create.add_argument("--private-key",required=True,help="External raw32 Ed25519 seed file; never copied")
    create.add_argument("--release-epoch",required=True,type=int)
    verify=commands.add_parser("verify")
    verify.add_argument("--bundle",required=True)
    verify.add_argument("--trusted-public-key",required=True,help="External trusted raw32 public key")
    verify.add_argument("--minimum-release-epoch",required=True,type=int)
    for item in (create,verify):
        item.add_argument("--target-major",type=int,choices=(26,27),required=True)
    args=parser.parse_args()
    try:
        if args.command=="create":
            services={}
            for value in args.service:
                instance,separator,path=value.partition("=")
                if not separator or not instance.isascii() or not instance.isdecimal() or not path:
                    raise BundleError("Service must be decimal INSTANCE=ELF")
                number=int(instance)
                if number in services:
                    raise BundleError("Duplicate service instance")
                services[number]=path
            report=create_bundle(args.config,args.core,services,args.output,
                private_key=load_private_key(args.private_key),target_major=args.target_major,release_epoch=args.release_epoch)
        else:
            _,public,_=_read(args.trusted_public_key,32)
            report=verify_bundle(args.bundle,trusted_public_key=public,expected_target=args.target_major,
                                 minimum_release_epoch=args.minimum_release_epoch)
        print(json.dumps({"ok":True,**report},ensure_ascii=True,indent=2))
        return 0
    except (ValueError,OSError) as error:
        print(json.dumps({"ok":False,"error":str(error),"boot_authorized":False},ensure_ascii=True))
        return 2


if __name__=="__main__":
    raise SystemExit(main())
