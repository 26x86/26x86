#!/usr/bin/env python3
"""Run native target compute repeatedly; never equate this with full acceleration.

For offscreen render use Tools/metal-run.py. Backend IRQ/fence, WindowServer,
installation and OS error counters require independent evidence.
"""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import platform
import secrets
import sys
import time

from metal_session import MetalSession, expected


def accepts(result):
    return (isinstance(result, dict)
            and result.get('terminal') is True
            and result.get('status') == 4
            and result.get('target_probe_passed') is True
            and result.get('native_metal_executed') is True
            and result.get('output_matches') is True
            and result.get('output_changed') is True
            and result.get('device_chain_matches') is True
            and result.get('gpu_timing_recorded') is True
            and result.get('nonce_witness_matches') is True
            and result.get('public_metal_target_compute_verified') is True
            and result.get('timed_out', False) is False)


def summary(requested, completed, rejected, timed_out):
    passed = completed == requested and requested >= 1000 and not rejected and not timed_out
    return {
        'requested_submissions': requested, 'accepted_submissions': completed,
        'rejected_submissions': rejected, 'command_timeouts': timed_out,
        'target_compute_stress_passed': passed,
        'assessment': 'TARGET_COMPUTE_STRESS_ONLY' if passed else 'NOT_PASSED',
        'gpu_resets': None, 'gpu_page_faults': None, 'hardware_fence_mismatches': None,
        'kernel_panics': None, 'telemetry_coverage_verified': False,
        'render_verified': False, 'windowserver_acceleration_verified': False,
        'installation_verified': False, 'hardware_irq_fence_verified': False,
        'mellow_7d41_metal_acceleration_pass': False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--registry-id', type=lambda text: int(text, 0), required=True)
    parser.add_argument('--iterations', type=int, default=10000)
    parser.add_argument('--timeout', type=float, default=10)
    parser.add_argument('--output', type=Path, required=True, help='NEW evidence directory')
    args = parser.parse_args()
    if not 1 <= args.iterations <= 100000 or not 0 < args.timeout <= 60:
        parser.error('iterations: 1..100000; timeout: (0,60]')
    if not 0 < args.registry_id < 2**64:
        parser.error('registry-id must be a nonzero uint64')
    args.output.mkdir(parents=True, exist_ok=False)
    report = {
        'schema_version': 1, 'started_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'host': platform.platform(), 'registry_id': str(args.registry_id),
        'client_sha256': hashlib.sha256(Path(__file__).with_name('metal_session.py').read_bytes()).hexdigest(),
        'native_calls_attempted': False,
    }
    completed = rejected = timed_out = 0
    session = None
    def save():
        report.update(summary(args.iterations, completed, rejected, timed_out))
        (args.output / 'summary.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    save()
    try:
        if sys.platform != 'darwin':
            raise RuntimeError('Native macOS Metal required; no test backend or CPU fallback is available in this CLI')
        report['native_calls_attempted'] = True
        session = MetalSession(args.registry_id)
        with (args.output / 'submissions.jsonl').open('x', encoding='utf-8') as evidence:
            for index in range(args.iterations):
                values = [1, 2, 3, 4] if index == 0 else [secrets.randbits(32) for _ in range(256)]
                nonce = secrets.randbits(32)
                ticket = session.submit(values, nonce)
                result = session.wait(ticket, timeout=args.timeout)
                event = {'submission': index + 1, 'nonce': nonce, 'result': result}
                if index == 0:
                    event.update(input=values, expected=expected(values, nonce))
                evidence.write(json.dumps(event) + '\n')
                evidence.flush()
                if result.get('timed_out') or not result.get('terminal'):
                    timed_out += 1
                    report['pending_gpu_command'] = True
                    save()
                    print('TIMEOUT: stopping submission; retaining the session until the outstanding command reaches a terminal state.', flush=True)
                    # Never call close() or free unresolved native buffers because a
                    # host timer expired. Report failure before waiting for drain.
                    drain_deadline = time.monotonic() + 60
                    while not result.get('terminal') and time.monotonic() < drain_deadline:
                        time.sleep(1)
                        result = session.poll(ticket)
                    report['pending_gpu_command'] = not bool(result.get('terminal'))
                    break
                if not accepts(result):
                    rejected += 1
                    break
                completed += 1
                if completed % 100 == 0:
                    save()
                    print(f'{completed}/{args.iterations} accepted target compute submissions', flush=True)
    except (Exception, KeyboardInterrupt) as error:
        report['error'] = type(error).__name__ + ': ' + str(error)
        rejected += 1
    finally:
        if session is not None:
            if session.pending:
                report['pending_gpu_command'] = True
                report['process_exit_does_not_prove_gpu_cancellation'] = True
            else:
                session.close()
        save()
    print(json.dumps(report, indent=2))
    return 0 if report['target_compute_stress_passed'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
