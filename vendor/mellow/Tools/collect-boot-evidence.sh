#!/bin/sh
# Runs in Tahoe Recovery or installed macOS. System inspection only.
# Writes exclusively to a NEW output directory; no Python/Xcode required.
set -u
umask 077
if [ "$(uname -s)" != Darwin ]; then
    printf '%s\n' 'NOT RUN: macOS/Recovery is required.' >&2
    exit 2
fi
if [ "$#" -ne 2 ]; then
    printf '%s\n' 'Usage: sh collect-boot-evidence.sh recovery|installed NEW_OUTPUT_DIRECTORY' >&2
    exit 2
fi
phase=$1
out=$2
case "$phase" in recovery|installed) ;; *) exit 2;; esac
case "$out" in ''|-*) exit 2;; esac
if [ -e "$out" ] || ! mkdir -m 700 "$out"; then
    printf '%s\n' 'Output must be a new directory in an existing writable parent.' >&2
    exit 2
fi
printf 'name\texit_status\ttimed_out\n' > "$out/commands.tsv"
collect() {
    name=$1
    shift
    "$@" > "$out/$name.txt" 2>&1 &
    child=$!
    (
        sleep 30
        if kill -0 "$child" 2>/dev/null; then
            printf 'true\n' > "$out/$name.timeout"
            kill -TERM "$child" 2>/dev/null || true
            sleep 2
            kill -KILL "$child" 2>/dev/null || true
        fi
    ) &
    watchdog=$!
    wait "$child"
    status=$?
    kill "$watchdog" 2>/dev/null || true
    wait "$watchdog" 2>/dev/null || true
    expired=false
    [ ! -f "$out/$name.timeout" ] || expired=true
    printf '%s\t%s\t%s\n' "$name" "$status" "$expired" >> "$out/commands.tsv"
}
{
    printf 'schema_version=1\nrequested_phase=%s\n' "$phase"
    printf 'started_utc=%s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
    printf '%s\n' 'scope=system evidence collection only; requested phase is not a passed gate'
    printf '%s\n' 'hardware_gpu_execution_verified=false' 'metal_acceleration_verified=false'
} > "$out/metadata.txt"
collect sw-vers /usr/bin/sw_vers
collect uname /usr/bin/uname -a
collect boot-session /usr/sbin/sysctl kern.boottime kern.bootsessionuuid kern.osversion
collect root-volume /usr/sbin/diskutil info -plist /
collect apfs /usr/sbin/diskutil apfs list -plist
collect disk-list /usr/sbin/diskutil list -plist
collect mount /sbin/mount
collect boot-args /usr/sbin/sysctl kern.bootargs
collect cpu /usr/sbin/sysctl machdep.cpu.brand_string machdep.cpu.family machdep.cpu.model
collect sip /usr/bin/csrutil status
collect authenticated-root /usr/bin/csrutil authenticated-root status
collect loaded-kexts /usr/bin/kmutil showloaded
collect pci /usr/sbin/ioreg -a -l -r -c IOPCIDevice
collect accelerator /usr/sbin/ioreg -a -l -r -c IOAccelerator
collect framebuffer /usr/sbin/ioreg -a -l -r -c IOFramebuffer
collect nvme /usr/sbin/ioreg -a -l -r -c IONVMeController
collect usb /usr/sbin/ioreg -p IOUSB -l -w0
collect network /sbin/ifconfig -a
collect route /sbin/route -n get default
collect displays /usr/sbin/system_profiler SPDisplaysDataType -json
collect windowserver /bin/ps -axo pid,comm
collect graphics-log /usr/bin/log show --last 30m --style json --info --debug --predicate '(eventMessage CONTAINS[c] "Mellow") OR (eventMessage CONTAINS[c] "GuC") OR (eventMessage CONTAINS[c] "GPU Restart") OR (eventMessage CONTAINS[c] "GPU Panic") OR (eventMessage CONTAINS[c] "page fault") OR (eventMessage CONTAINS[c] "fence") OR (process == "WindowServer")'
collect install-log /usr/bin/tail -n 1500 /var/log/install.log
{
    for name in AppleIntelTGLGraphicsFramebuffer.kext AppleIntelTGLGraphics.kext AppleIntelTGLGraphicsMTLDriver.bundle; do
        found=false
        for base in /System/Library/Extensions /Library/Extensions /Library/GPUBundles; do
            bundle="$base/$name"
            [ -d "$bundle" ] || continue
            found=true
            printf 'PRESENT=%s\n' "$bundle"
            /usr/libexec/PlistBuddy -c 'Print :CFBundleIdentifier' "$bundle/Contents/Info.plist" 2>&1 || true
            /usr/libexec/PlistBuddy -c 'Print :CFBundleVersion' "$bundle/Contents/Info.plist" 2>&1 || true
        done
        [ "$found" = true ] || printf 'MISSING=%s\n' "$name"
    done
} > "$out/tgl-bundles.txt"
printf 'completed_utc=%s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" >> "$out/metadata.txt"
(cd "$out" && find . -type f ! -name SHA256SUMS -exec /usr/bin/shasum -a 256 '{}' ';') > "$out/SHA256SUMS"
printf 'Saved: %s\n' "$out"
printf '%s\n' 'Collection success does not prove installation, network reachability, Metal, or WindowServer acceleration.'
printf '%s\n' 'Keep this evidence local until private machine and volume metadata have been reviewed.'
