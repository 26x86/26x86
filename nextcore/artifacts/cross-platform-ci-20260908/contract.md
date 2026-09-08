# Cross-platform CI correction

Current: commit dcc90013109eac694ccbf997b1e44a7018480f78 passes the Windows
EXE build and frozen backend smoke, but the preparation tests fail on Windows
and macOS and the Linux Qt GUI aborts before its smoke report.
Desired: retain the payload validation contract and run the real GUI successfully
on the documented host dependencies, with specific failures if libraries are absent.

DECIDED: resolve the authored test fixture's temporary directory before creating
the copied Mellow package. Windows' short temporary-directory alias differs from
the loader's canonical path; macOS' `/var` ancestor is a symlink rejected by the
existing strict loader. Production link/reparse-point rejection remains unchanged.
A separate authored ancestor-link fixture must still be rejected.

DECIDED: install `libxcb-icccm4`, `libxcb-keysyms1` and `libxcb-shape0` with the
existing Ubuntu Qt runtime dependencies. A fresh PySide6 6.11.2 environment
reproduces these three missing libraries through `ldd libqxcb.so`. Check the
platform plugin's dependency resolution before starting the real Xvfb GUI; do not
convert an abort or absent smoke report into success. These libraries are part
of Qt's public [Linux/X11 requirements](https://doc.qt.io/qt-6/linux-requirements.html).

Scope: `.github/workflows/cross-platform.yml`, `tests/test_mellow_payload.py`
and this evidence directory. The EXE workflow already passes and needs no
speculative packaging changes. No EFI, kernel, macOS runtime or Metal claim is
derived from the host application CI result. Root owns Git commits and other CI.

Evidence: [failed cross-platform run](https://github.com/26x86/26x86/actions/runs/34195631087)
and [successful Windows EXE run](https://github.com/26x86/26x86/actions/runs/34195631076).
Original failure output and EXE job status are retained beside this contract.

The actual Qt GUI exposed a second failure after dependency resolution: the
frontend's successful HTTP probe replaced `window.pywebview` with an API-only
object, removing pywebview's runtime helpers during injection. The observed
errors name `_createApi` and `stringify`; the GUI produced a failing smoke report.
DECIDED, explicitly delegated by the Build Plan owner: keep HTTP and custom Qt
transports in their own objects, preserve pywebview's object and helpers, and
retain native → Qt → HTTP API preference. Add execution tests for the browser,
Qt, native and asynchronous native-injection cases, then repeat the real GUI.
Additional scope is `x86/gui/web/app.js` and its transport regression tests.

Final local validation: Windows preparation 132 tests passed (one skip), the
focused payload suite passed 27 tests, and the existing GUI bridge suite passed
25 tests (one skip). Linux passed the same 27 payload tests. Four Node transport
tests pass against the correction; all four reject the original dcc9001 source.
The actual Xvfb/PySide6 6.11.2/pywebview 6.2.1 window reports `NextCore` and
`준비됨`, then exits naturally with code zero in 2.7415 seconds. The external
supervisor reaps remaining Qt children and reports no process-group or adopted
child remnants. Its `stopped_by_harness` flag describes that child cleanup after
the successful main exit, not a timeout or a substituted GUI result.

The first local GUI verifier reused a HAL-only 2 MiB file cap, which also bounded
Qt/Xvfb screen backing files; the attempted 3.87 MiB screen allocation failed.
That separate verifier error is preserved. The final verifier uses a 128 MiB cap
and a 60-second process deadline. CI does not inherit the local HAL limit.

Local Linux uses Python 3.12.3 and Node 22.23.2; CI requests Python 3.13 and Node
22. The original Windows EXE CI passes, but a remote CI rerun of this correction
and macOS verification are still pending root's commit/push. No runtime result is
promoted across those host/version boundaries. Public production changes are
limited to the four source/workflow/test files recorded in `result.json`.
