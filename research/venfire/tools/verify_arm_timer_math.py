#!/usr/bin/env python3
"""Compile the candidate's actual ARM timer conversion functions and test bounds.

Uses QEMU's own host-utils.h in both native-128 and fallback configurations.
The independent oracle uses unsigned 128-bit arithmetic. This is arithmetic
coverage, separate from verify_arm_timer.py's actual CPU/GIC execution.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shlex
import subprocess

HARNESS = r'''
#include "qemu/osdep.h"
#ifdef VENFIRE_NO_INT128
#undef CONFIG_INT128
#endif
#include "qemu/host-utils.h"
#define NANOSECONDS_PER_SECOND 1000000000ULL
typedef struct ARMCPU { uint64_t gt_cntfrq_hz; } ARMCPU;
@FUNCTIONS@

static uint64_t seed = 24;
static uint64_t random64(void)
{
    seed ^= seed << 13;
    seed ^= seed >> 7;
    seed ^= seed << 17;
    return seed;
}

int main(void)
{
    const uint64_t frequencies[] = {
        1, 1000000, 19200000, 24000000, 62500000, 1000000000,
        1000000001, UINT64_MAX,
    };
    unsigned checks = 0;
    for (unsigned f = 0; f < G_N_ELEMENTS(frequencies); f++) {
        ARMCPU cpu = { .gt_cntfrq_hz = frequencies[f] };
        uint64_t hz = MIN(cpu.gt_cntfrq_hz, NANOSECONDS_PER_SECOND);
        uint64_t max_ticks = (__uint128_t)INT64_MAX * hz / NANOSECONDS_PER_SECOND;
        for (unsigned i = 0; i < 10016; i++) {
            uint64_t ns = random64() & INT64_MAX;
            uint64_t ticks = random64();
            if (i < 8) {
                const uint64_t edge_ns[] = { 0, 1, 41, 42, 83, 84,
                                             INT64_MAX - 1, INT64_MAX };
                const uint64_t edge_ticks[] = { 0, 1, 2, 3, max_ticks - 1,
                                                max_ticks, max_ticks + 1, UINT64_MAX };
                ns = edge_ns[i];
                ticks = edge_ticks[i];
            }
            uint64_t count = (__uint128_t)ns * hz / NANOSECONDS_PER_SECOND;
            if (gt_counter_from_ns(&cpu, ns) != count) {
                fprintf(stderr, "counter mismatch hz=%"PRIu64" ns=%"PRIu64"\n", hz, ns);
                return 1;
            }
            __uint128_t wide = ((__uint128_t)ticks * NANOSECONDS_PER_SECOND + hz - 1) / hz;
            int64_t expiry = wide > INT64_MAX ? INT64_MAX : wide;
            if (gt_counter_to_ns(&cpu, ticks) != expiry) {
                fprintf(stderr, "deadline mismatch hz=%"PRIu64" ticks=%"PRIu64"\n", hz, ticks);
                return 1;
            }
            if (wide <= INT64_MAX &&
                (gt_counter_from_ns(&cpu, expiry) < ticks ||
                 (expiry && gt_counter_from_ns(&cpu, expiry - 1) >= ticks))) {
                fprintf(stderr, "inverse boundary mismatch\n");
                return 1;
            }
            checks += 2;
        }
    }
    printf("{\"passed\":true,\"checks\":%u,\"frequencies\":8}\n", checks);
    return 0;
}
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True, type=Path)
    parser.add_argument('--build', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    raw = (args.source / 'target/arm/cpu.c').read_text()
    start = raw.index('static uint32_t gt_effective_freq_hz(')
    end = raw.index('\nstatic void arm_cpu_propagate_feature_implications', start)
    functions = raw[start:end]
    fixture = args.output / 'timer_math.c'
    fixture.write_text(HARNESS.replace('@FUNCTIONS@', functions), newline='\n')
    cflags = shlex.split(subprocess.check_output(['pkg-config', '--cflags', 'glib-2.0'], text=True))
    report = {'schema': 1, 'passed': False, 'source_functions_sha256':
              hashlib.sha256(functions.encode()).hexdigest(), 'runs': []}
    try:
        for fallback in (False, True):
            binary = args.output / ('timer-fallback' if fallback else 'timer-native')
            command = ['cc', '-std=gnu11', '-O2', '-Wall', '-Wextra', '-Werror',
                       '-I' + str(args.source / 'include'), '-I' + str(args.build),
                       *cflags, str(fixture), '-o', str(binary)]
            if fallback:
                command.insert(1, '-DVENFIRE_NO_INT128')
            subprocess.run(command, check=True, capture_output=True, timeout=30)
            value = json.loads(subprocess.check_output([str(binary)], timeout=20))
            value['configuration'] = 'fallback' if fallback else 'native-int128'
            report['runs'].append(value)
            print(json.dumps(value), flush=True)
        report['passed'] = True
    finally:
        (args.output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    main()
