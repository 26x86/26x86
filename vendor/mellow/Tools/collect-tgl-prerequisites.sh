#!/bin/sh
# Read-only macOS dependency inventory. Writes only its new output directory.
# Does not load code, alter boot arguments, request sudo, or apply a root patch.
set -u
umask 077
if [ "$(uname -s)" != Darwin ]; then
    printf '%s\n' 'NOT RUN: this collector requires macOS.' >&2
    exit 2
fi
out=${1:-tgl-prerequisites-$(date -u '+%Y%m%dT%H%M%SZ')}
case "$out" in -*) printf '%s\n' 'Output path must not begin with -.' >&2; exit 2;; esac
if [ -e "$out" ] || ! mkdir -m 700 "$out"; then
    printf '%s\n' "Refusing existing or unavailable output path: $out" >&2
    exit 2
fi
run() {
    name=$1
    shift
    ( "$@"; result=$?; printf '\ncommand_exit_status=%s\n' "$result" ) >"$out/$name.txt" 2>&1
}
run sw-vers sw_vers
run uname uname -a
run cpu sysctl machdep.cpu.brand_string machdep.cpu.family machdep.cpu.model
run kexts kmutil showloaded
run graphics system_profiler SPDisplaysDataType -detailLevel full
run pci ioreg -lw0 -p IOService -c IOPCIDevice
run accelerator ioreg -lw0 -p IOService -c IntelAccelerator
run sip csrutil status
run developer-path xcode-select -p
{
    printf 'state=INVENTORY_ONLY\nstarted_utc=%s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
    for name in AppleIntelTGLGraphicsFramebuffer.kext AppleIntelTGLGraphics.kext AppleIntelTGLGraphicsMTLDriver.bundle AppleIntelTGLGraphicsGLDriver.bundle AppleIntelTGLGraphicsVADriver.bundle; do
        found=0
        for base in /Library/Extensions /Library/GPUBundles /System/Library/Extensions; do
            bundle="$base/$name"
            [ -d "$bundle" ] || continue
            found=1
            printf '\nbundle=%s\n' "$bundle"
            plist="$bundle/Contents/Info.plist"
            for key in CFBundleIdentifier CFBundleVersion CFBundleShortVersionString CFBundleExecutable; do
                printf '%s=' "$key"
                /usr/libexec/PlistBuddy -c "Print :$key" "$plist" 2>&1 || true
            done
            /usr/bin/codesign -dv --verbose=4 "$bundle" 2>&1 || true
            /usr/bin/codesign --verify --strict --verbose=2 "$bundle" 2>&1 || true
            executable=$(/usr/libexec/PlistBuddy -c 'Print :CFBundleExecutable' "$plist" 2>/dev/null) || executable=''
            case "$executable" in ''|*/*|*\\*) printf '%s\n' 'Executable missing or not a basename; skipped.'; continue;; esac
            binary="$bundle/Contents/MacOS/$executable"
            if [ -f "$binary" ]; then
                /usr/bin/file "$binary"
                /usr/bin/shasum -a 256 "$binary"
                # Symbol-list absence is inconclusive for stripped binaries.
                /usr/bin/nm "$binary" 2>&1 | /usr/bin/grep -E 'gPlatformInformationList|setCDClockFrequency|AppleIntelBaseController.*start|no symbols|error' || true
            fi
        done
        [ "$found" -eq 1 ] || printf '\nMISSING=%s\n' "$name"
    done
} >"$out/tgl-bundles.txt" 2>&1
{
    printf '%s\n' 'This is inventory, not verified GPU execution.'
    printf '%s\n' 'Missing symbols in stripped binaries do not establish incompatibility.'
    printf '%s\n' 'Review serial numbers and paths before sharing the diagnostic directory.'
} >"$out/interpretation.txt"
( cd "$out" && find . -type f ! -name SHA256SUMS -exec /usr/bin/shasum -a 256 '{}' ';' ) >"$out/SHA256SUMS"
printf 'Inventory saved: %s\n' "$out"
