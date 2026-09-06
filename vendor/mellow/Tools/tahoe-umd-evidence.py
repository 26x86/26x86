#!/usr/bin/env python3
"""Inventory actual extracted plugin metadata/helper; never confuse helper with main executable."""
import argparse,hashlib,importlib.util,json,plistlib
from pathlib import Path
root=Path(__file__).resolve().parents[1]
def inspect(info_path,helper_path):
    if info_path.stat().st_size>1024*1024 or helper_path.stat().st_size>128*1024*1024:raise ValueError('Input size limit')
    info=plistlib.loads(info_path.read_bytes())
    if not isinstance(info,dict):raise ValueError('Bundle plist dictionary required')
    name=info.get('CFBundleExecutable')
    if not isinstance(name,str) or not name or Path(name).name!=name or '/' in name or '\\' in name:raise ValueError('Executable name')
    spec=importlib.util.spec_from_file_location('tahoe_abi',root/'Tools/tahoe-abi.py')
    abi=importlib.util.module_from_spec(spec);spec.loader.exec_module(abi)
    data=helper_path.read_bytes();image=abi.macho(abi.thin_x86(data))
    return {'scope':'Actual bundle metadata and helper Mach-O analysis, not a complete Intel Metal plugin',
            'bundle_identifier':info.get('CFBundleIdentifier'),'bundle_version':info.get('CFBundleVersion'),
            'short_version':info.get('CFBundleShortVersionString'),'principal_class':info.get('NSPrincipalClass'),
            'declared_executable':name,'examined_binary_name':helper_path.name,
            'examined_binary_is_declared_executable':helper_path.name==name,
            'main_executable_acquired':False,'private_plugin_abi_verified':False,'plugin_loaded':False,'metal_executed':False,
            'metadata_sha256':hashlib.sha256(info_path.read_bytes()).hexdigest(),
            'binary_sha256':hashlib.sha256(data).hexdigest(),'binary_bytes':len(data),
            'uuid':image.get('uuid'),'defined_symbols':len(image['definitions']),
            'imports':len(image['imports']),'dependencies':image['dependencies'],
            'selected_definitions':{k:v for k,v in image['definitions'].items() if k in
              ('_OpenMetricsDevice','_CloseMetricsDevice','_OpenPerformanceInterface','_OBJC_CLASS_$_MTLIGAccelDevice')},
            'extraction_integrity':'HTTPS selected ZIP shards passed CRC and PBZX/XZ decoding; whole InstallAssistant signature not validated'}
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--info',type=Path,required=True)
    p.add_argument('--helper',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();report=inspect(a.info,a.helper)
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('dependencies','selected_definitions')},indent=2))
