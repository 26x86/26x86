#!/bin/sh

# Best-effort, read-only system inspection for Mellow bring-up.
# The only writes are new files inside the newly created output directory.
# No sudo, kext load/unload, NVRAM changes, MMIO access, or configuration changes.

set -u
umask 077

timestamp="$(date -u '+%Y%m%dT%H%M%SZ')"
output_dir="${1:-mellow-diagnostics-${timestamp}}"
log_window="1h"

if [ -e "$output_dir" ]; then
    printf '%s\n' "Refusing to overwrite existing path: $output_dir" >&2
    exit 2
fi

if ! mkdir -m 700 "$output_dir"; then
    printf '%s\n' "Could not create output directory: $output_dir" >&2
    exit 2
fi

successes=0
failures=0

collect() {
    name=$1
    shift
    destination="$output_dir/$name.txt"

    if (
        printf 'command:'
        for argument in "$@"; do
            printf ' [%s]' "$argument"
        done
        printf '\n\n'
        "$@"
        status=$?
        printf '\nexit_status: %s\n' "$status"
        exit "$status"
    ) >"$destination" 2>&1; then
        successes=$((successes + 1))
    else
        failures=$((failures + 1))
    fi
}

collect_optional() {
    name=$1
    command_name=$2
    shift 2

    if command -v "$command_name" >/dev/null 2>&1; then
        collect "$name" "$command_name" "$@"
    else
        printf 'unavailable: %s\n' "$command_name" >"$output_dir/$name.txt"
        failures=$((failures + 1))
    fi
}

{
    printf 'collector_version: 1\n'
    printf 'started_utc: %s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
    printf 'output_directory: %s\n' "$output_dir"
    printf 'unified_log_window: %s\n' "$log_window"
    printf 'effective_uid: %s\n' "$(id -u)"
    printf 'note: collection is best-effort; individual command failures are retained.\n'
    printf 'privacy: inspect serial numbers, paths, and other metadata before sharing.\n'
} >"$output_dir/metadata.txt"

if [ "$(id -u)" -eq 0 ]; then
    printf '%s\n' "warning: running as root is unnecessary and discouraged" >>"$output_dir/metadata.txt"
fi

collect_optional "sw-vers" sw_vers
collect_optional "uname" uname -a
collect_optional "sysctl-platform" sysctl \
    hw.model hw.memsize kern.osrelease kern.osversion kern.version \
    machdep.cpu.brand_string machdep.cpu.family machdep.cpu.model machdep.cpu.stepping
collect_optional "csrutil-status" csrutil status

collect_optional "ioreg-pci" ioreg -lw0 -p IOService -c IOPCIDevice
collect_optional "ioreg-igpu" ioreg -lw0 -p IOService -n IGPU
collect_optional "ioreg-gfx0" ioreg -lw0 -p IOService -n GFX0
collect_optional "ioreg-framebuffer" ioreg -lw0 -p IOService -c AppleIntelFramebufferController
collect_optional "ioreg-accelerator" ioreg -lw0 -p IOService -c IntelAccelerator
collect_optional "system-profiler-displays" system_profiler SPDisplaysDataType -detailLevel full

collect_optional "kmutil-showloaded" kmutil showloaded
collect_optional "kextstat" kextstat
collect_optional "dmesg" dmesg
collect_optional "mellow-unified-log" /usr/bin/log show --last "$log_window" \
    --style syslog --info --debug \
    --predicate '(eventMessage CONTAINS[c] "mellow") OR (process CONTAINS[c] "mellow")'

key_lines="$output_dir/key-lines.txt"
: >"$key_lines"
for source_file in \
    "$output_dir/ioreg-pci.txt" \
    "$output_dir/ioreg-igpu.txt" \
    "$output_dir/ioreg-gfx0.txt" \
    "$output_dir/ioreg-framebuffer.txt" \
    "$output_dir/ioreg-accelerator.txt" \
    "$output_dir/system-profiler-displays.txt" \
    "$output_dir/kmutil-showloaded.txt" \
    "$output_dir/kextstat.txt" \
    "$output_dir/mellow-unified-log.txt"
do
    if [ -f "$source_file" ]; then
        printf '\n===== %s =====\n' "$(basename "$source_file")" >>"$key_lines"
        LC_ALL=C grep -Eai \
            'mellow|appleinteltgl|intelaccelerator|igpu|gfx0|8086|7d41|9a49|bar0|mmio|dmc|panic|fault|hang|timeout|fence|interrupt|metal' \
            "$source_file" >>"$key_lines" 2>/dev/null || true
    fi
done

{
    printf 'completed_utc: %s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
    printf 'successful_commands: %s\n' "$successes"
    printf 'failed_or_unavailable_commands: %s\n' "$failures"
    printf 'interpretation: command success is collection success, not GPU success.\n'
} >>"$output_dir/metadata.txt"

if command -v shasum >/dev/null 2>&1; then
    (
        cd "$output_dir" || exit 1
        find . -type f ! -name SHA256SUMS -exec shasum -a 256 '{}' ';' | LC_ALL=C sort
    ) >"$output_dir/SHA256SUMS" 2>"$output_dir/SHA256SUMS.error" || true
fi

printf '%s\n' "Collected diagnostics in: $output_dir"
printf '%s\n' "Review and redact private metadata before sharing."
printf '%s\n' "Collection failures are recorded; they do not imply GPU failure."
