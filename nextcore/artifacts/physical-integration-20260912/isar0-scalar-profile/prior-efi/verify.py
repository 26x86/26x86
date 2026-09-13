"""Use the same authored fixture to discriminate the preceding ZFR0 EFI."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys

proof = Path(sys.argv[1]).resolve(strict=True)
out = Path('/tmp/nextcore-isar0-prior-efi-20260913')
out.mkdir(exist_ok=False)
old = Path('/tmp/nextcore-zfr0-mapped-final-20260913.efi')
assert hashlib.sha256(old.read_bytes()).hexdigest() == 'fc329f8cf372ac4a2706f0cc270058d88a6f5056e76e171536935b9c28b0591a'
receipt = json.loads((proof / 'receipt.json').read_text())
assert receipt['passed']
commands = json.loads((proof / 'commands.json').read_text())
command = next(c['argv'][:] for c in commands if '--output' in c['argv'] and c['argv'][c['argv'].index('--output')+1] == str(proof / 'cached'))
command[command.index('--efi')+1] = str(old)
command[command.index('--output')+1] = str(out / 'run')
inputs = [old, proof / 'probe.kc', proof / 'probe.bin', proof / 'diagnostic.dt']
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
before = {str(p): sha(p) for p in inputs}
word = 0xd538060b  # Independently assembled authored MRS x11, ID_AA64ISAR0_EL1.
payload = (proof / 'probe.bin').read_bytes()
encoded = word.to_bytes(4, 'little')
assert payload.count(encoded) == 1
offset = payload.index(encoded)
assert offset % 4 == 0
run = subprocess.run(command, capture_output=True, timeout=210)
(out / 'run.log').write_bytes(run.stdout + run.stderr)
report = json.loads((out / 'run/report.json').read_text())
execution = report.get('execution') or {}
instruction = execution.get('fault_instruction')
if isinstance(instruction, str): instruction = int(instruction, 0)
memory = execution.get('memory') or {}
checks = {
    'current_authored_proof_passed': receipt['passed'],
    'prior_exact_isar0_boundary': execution.get('status') == 13 and instruction == word and execution.get('retired') == offset // 4,
    'mapped_profile_accepted': report['mapped_profile']['validated'],
    'provider_has_no_error': memory.get('provider_status') == 0,
    'reported_inputs_preserved': report['original_inputs_preserved'] and report['esp_copies_preserved'] and report['tool_sources_preserved'],
    'same_authored_inputs_and_prior_binary_preserved': before == {str(p): sha(p) for p in inputs},
    'host_has_no_failure': report['failure'] is None,
    'complete_terminal_diagnostic': report['diagnostic_completed'] and report['requested_checks_completed'] and run.returncode == 0,
}
result = dict(schema='nextcore.authored-isar0-prior-efi.v1', passed=all(checks.values()), checks=checks,
    previous_binary_sha256=before[str(old)], authored_inputs_sha256=before,
    actual_retired=execution.get('retired'), expected_retired=offset // 4,
    execution_status=execution.get('status'), expected_instruction_class='MRS ID_AA64ISAR0_EL1',
    return_code=run.returncode, qemu_exit_code=report['qemu_exit_code'], stopped_by_harness=report['stopped_by_harness'],
    command=command, original_images_used=False, physical_boot_verified=False, macos_boot_verified=False)
(out / 'receipt.json').write_text(json.dumps(result, indent=2)+'\n')
print(json.dumps(result))
assert result['passed']
