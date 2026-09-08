import hashlib,json,pathlib,re,shutil,subprocess
base=pathlib.Path(__file__).resolve().parent
out=pathlib.Path(r'C:\Users\Admin\Documents\ChatGPT\26x86darwin\nextcore\artifacts\module-release-v011-20260908')
out.mkdir(exist_ok=True)
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def run(args):return subprocess.run(args,capture_output=True,check=True).stdout
modules=[]
for short in ['Core','GPU','HAL','ISE','APLS','EFI','Tool']:
 name='Nextcore-'+short
 receipt=load(base/'tool-v012/published.json' if short=='Tool' else base/(name+'-published.json'))
 refs=run(['git','ls-remote','https://github.com/26x86/'+name+'.git','refs/heads/main','refs/tags/'+receipt['tag']]).decode().splitlines()
 assert len(refs)==2 and all(r.split()[0]==receipt['head'] for r in refs)
 runs=json.loads(run(['gh','run','list','--repo','26x86/'+name,'--branch','main','--limit','5','--json','databaseId,headSha,status,conclusion,url']))
 ci=next(r for r in runs if r['headSha']==receipt['head'])
 assert ci['status']=='completed' and ci['conclusion']=='success',(name,ci)
 if short=='Tool': gate=load(base/'tool-v012/post-linux-receipt.json')
 else: gate=load(base/'gates'/('post-r2' if short in ['Core','GPU','HAL','ISE'] else 'post')/name/'receipt.json')
 assert gate['passed']
 receipt['post_publish_gate']=gate
 receipt['github_ci']=ci
 modules.append(receipt)
profile=load(base/'profile-published.json')
result={'schema':1,'layer':'module snapshot release and organization documentation','modules':modules,'profile':profile,
 'all_latest_modules_clone_gates_passed':True,'all_latest_modules_exact_head_ci_passed':True,
 'existing_history_and_tags_preserved':True,'force_push_used':False,'shared_source_or_index_modified_by_release_agent':False,
 'superseded_failed_release':{'repository':'26x86/Nextcore-Tool','tag':'26x86-Nextcore-Tool-v0.1.1','head':'f1d26043f3f8c8f4bb663ef9f9b203dbf42c8c2d','ci_url':'https://github.com/26x86/Nextcore-Tool/actions/runs/34196324452','reason':'Test fixture escaped crate to sibling Core folder; Windows sibling clones masked failure','preserved':True},
 'private_paths_exported':False,'module_tests_claim_guest_execution':False,'guest_metal_verified_by_release':False}
(out/'release-receipt.json').write_text(json.dumps(result,indent=2)+'\n')
for name in ['remote-before.json','post-test-counts.json','cargo-clean-receipt.json','cleanup-targets-before.json','profile-published.json','tool-ci-failure.log']:
 shutil.copy2(base/name,out/name)
shutil.copytree(base/'gates',out/'gates',dirs_exist_ok=True)
shutil.copytree(base/'tool-v012',out/'tool-v012',dirs_exist_ok=True)
helpers=['prepare_incremental.py','validate_module-r1.py','validate_module.py','publish_module.py','prepare_tool_fix.py','verify_tool_linux-r1.py','verify_tool_linux.py','finalize_release.py']
helper_dir=out/'helpers';helper_dir.mkdir(exist_ok=True)
for name in helpers:shutil.copy2(base/name,helper_dir/name)
for name in ['Nextcore-Core','Nextcore-GPU','Nextcore-HAL','Nextcore-ISE','Nextcore-APLS','Nextcore-EFI','Nextcore-Tool']:
 shutil.copy2(base/(name+'-prepared.json'),out/(name+'-prepared-v011.json'))
text='\n## Completed release\n\nAll seven latest module snapshots passed fresh-clone gates and GitHub CI at the exact published main/tag commit. Existing history and all earlier tags remain intact.\n\n'
text+='| Module | Latest tag | Commit | Exact-head CI |\n| --- | --- | --- | --- |\n'
for r in modules:
 name=r['repository'].split('/')[1];url='https://github.com/'+r['repository']
 text+=f'| [{name}]({url}) | [{r["tag"]}]({url}/tree/{r["tag"]}) | [{r["head"][:7]}]({url}/commit/{r["head"]}) | [success]({r["github_ci"]["url"]}) |\n'
text+='\nCore passed 180 tests and its no_std check. GPU passed 94 default tests and 97 with Vulkan enabled; HAL passed 32 and ISE 26. APLS passed 49. EFI passed its all-feature x86_64 UEFI check. Counts are suite totals for the documented invocation, not proof of guest hardware execution. Tool’s corrected standalone Linux invocation and raw logs are preserved separately; its opt-in ignored test remains ignored.\n\n'
text+=f'The organization profile was independently reviewed and published at [{profile["head"][:7]}](https://github.com/26x86/.github/commit/{profile["head"]}); GitHub API content readback confirmed the new NextCore logo, release links and explicit `metal_verified=false`. Latest development links follow main while module source references remain immutable.\n\n'
text+='The [release receipt](release-receipt.json) contains source commits, old/new heads, post-clone commands, remote CI URLs and the retained failed Tool v0.1.1 history. Gate logs, the corrected Linux receipts, public-file inventories, release helper sources and Cargo cleanup records accompany it. This release changed only fresh module clones and the explicitly delegated organization profile; the parent controlled the shared source, index and source-fixture fix.\n'
with (out/'README.md').open('a') as f:f.write(text)
print(json.dumps({'modules':len(modules),'all_gates_passed':True,'profile_head':profile['head'],'report':str(out/'README.md')},indent=2))
