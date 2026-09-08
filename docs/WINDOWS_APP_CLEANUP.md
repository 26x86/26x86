# Windows application cleanup — BP27-C

Current: the shared desktop frontend exposes a retired device-specific profile,
EFI self-test packaging, synthetic execution demonstrations and research VM
launch controls beside the intended ARM EFI preparation workflow. The user
requested removal of the dedicated device content and unnecessary app testers.

Decision and ownership: the cleanup agent removes that dedicated profile module,
documentation, CLI/GUI profile selection and profile-only assertions. General
platform isolation, root-patch result and HTTP bridge tests move into appropriate
existing/general test coverage. The shared Windows webview frontend drops its
self-test/demo/research-VM launcher panels, state, event handlers and app transport
exports. ARM EFI mode selection, preparation information, normal settings and
native preparation remain. App packaging stops bundling diagnostic EFI artifacts.
Related obsolete screenshots/GUI-only test expectations and documentation links
are cleaned up. Root owns Build Plan, repository metadata, commits and publication.

The actual JIT/EFI/macOS boot implementation, VSK grant policy and runtime,
research CLI/QEMU harnesses and their executable tests, and genuine GPU compute
backends are outside removal scope. Existing bridge wrappers used by those tests
may remain internal; they are no longer exposed as app controls. Frozen APLS/GPU
module sources are unchanged. No new graphics or boot success is claimed.

Validate JavaScript transport and frontend behavior, Python imports/CLI/platform
boundaries and Windows PyInstaller packaging. A build result is only an app
build; it does not establish guest boot or physical graphics acceleration.

OPEN_QUESTION: None within the delegated cleanup scope.

Completed validation: the Python runtime regression suite passed 165 tests with
3 existing skips, and the final boundary suite passed 19 tests. JavaScript
transport passed 4 tests; the real Chrome frontend test covered removed controls,
ARM mode preparation, native dispatch, saved settings, errors and a 390px layout.
The actual Windows build script produced an EXE; all 6 final EXE startup checks
passed. Build snapshot hashes match the final edited app sources. Evidence is in
[the validation receipt](validation/windows-app-cleanup-20260908/receipt.json).
The startup check does not exercise a rendered EXE WebView window, and these
results do not establish guest macOS boot, guest Metal or an EFI GPU backend.

PR regression follow-up: the separate GUI smoke suites still expected removed
application endpoints. Update their real HTTP GET/POST checks to require404,
verify the WebView facade no longer exports the removed operation, and retain
the existing settings roundtrip. No application endpoint is reintroduced.
