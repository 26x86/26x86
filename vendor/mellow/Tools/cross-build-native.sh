#!/bin/bash
# Final kext linking uses Apple's toolchain; this script NEVER installs/loads it.
set -euo pipefail
project_root="$(cd "$(dirname "$0")/.." && pwd)"
configuration="${1:-Debug}"
case "$configuration" in Debug|Release) ;; *) echo 'Use Debug or Release' >&2; exit 2 ;; esac
if [ "$(uname -s)" != Darwin ]; then
  echo 'Native final linking requires macOS with full Xcode selected by xcode-select.' >&2
  exit 2
fi
command -v python3 >/dev/null
xcrun --find clang >/dev/null
xcrun --find ld >/dev/null
xcodebuild -version
build_dir="${MELLOW_BUILD_DIR:-$project_root/build/native-$configuration}"
mkdir -p "$build_dir"
build_dir="$(cd "$build_dir" && pwd)"
if [ "$build_dir" = "$project_root" ]; then
  echo 'Build output must be a separate directory.' >&2
  exit 2
fi
build_args=(-project "$project_root/Mellow.xcodeproj" -scheme Mellow
  -configuration "$configuration" -derivedDataPath "$build_dir/DerivedData"
  ARCHS=x86_64 ONLY_ACTIVE_ARCH=NO CODE_SIGNING_ALLOWED=NO CODE_SIGNING_REQUIRED=NO)
xcodebuild "${build_args[@]}" build 2>&1 | tee "$build_dir/xcodebuild.log"
xcodebuild "${build_args[@]}" -showBuildSettings -json > "$build_dir/build-settings.json"
bundle_path="$(python3 - "$build_dir/build-settings.json" <<'PY'
import json, pathlib, sys
entries = json.load(open(sys.argv[1]))
settings = next(x['buildSettings'] for x in entries if x.get('target') == 'Mellow')
print(pathlib.Path(settings['TARGET_BUILD_DIR']) / settings['FULL_PRODUCT_NAME'])
PY
)"
python3 "$project_root/Tools/validate-macho.py" "$bundle_path" --output "$build_dir/macho-validation.json"
printf 'Built and structurally checked: %s\n' "$bundle_path"
printf '%s\n' 'Unsigned research artifact only. No load, kernel collection rebuild, root patch, or EFI modification performed.'
