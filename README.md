# 26x86

<div align="center">
<img src="resources/branding/26x86-logo-256.png" alt="26x86 로고" width="256" />
<h1>26x86</h1>
<h3>x86 Mac을 위한 macOS 26 (Tahoe) 패처</h3>
</div>

> **실험적 알파** — [면책 조항](DISCLAIMER.md) 확인 · **전체 백업** 후 테스트용 Mac에서 시험하세요.

## 문서

| 문서 | 설명 |
|------|------|
| **[위키 홈](docs/wiki/Home.md)** | 주의사항, 설치, 설정, 이전 패처에서 전환 |
| [Releases](https://github.com/NiSeullent/26x86/releases) | 안정 빌드 |
| [SOURCE.md](SOURCE.md) | 소스 실행·빌드 |
| [iBoot Personality 범위](docs/IBOOT_PERSONALITY.md) | macOS 전용 게스트·DFU/IPSW 정책 |

영문: [docs/README.en.md](docs/README.en.md)

## 실행

Surface Pro 6 i5-8250U / Tahoe 준비·검사와 macOS 루트 패치 경로:
[Surface Pro 6 안내](docs/SURFACE_PRO6.md). Windows/Linux GUI는 EFI 준비와 검사를
지원하며 APFS 루트 패치는 설치된 macOS에서 실행합니다.

`26x86.command` 또는 `python3 -m x86 wizard`

기본 GUI: **Tauri** (WKWebView / WebView2, Chromium Qt 아님). 폴백: Cocoa pywebview.
셸 소스: [`gui-tauri/`](gui-tauri/).

## Windows EXE CI 빌드

- 워크플로우: `.github/workflows/windows-exe.yml`
- 실행 조건: `main` 브랜치 `push`, `main` 대상 `pull_request`, 수동 `workflow_dispatch`
- 빌드 명령: `.\scripts\build-windows-exe.ps1 -Clean` (내부적으로 `python -m PyInstaller 26x86-Windows.spec`)
- 산출물: Actions Artifact `26x86-windows-exe` (내용: `dist/**`, 실행 파일 `dist/26x86/26x86.exe`)

### 아티팩트 다운로드

1. GitHub 저장소의 [Actions](https://github.com/NiSeullent/26x86/actions) 탭 진입
2. `Build Windows EXE` 워크플로우 실행 선택
3. 페이지 하단 `Artifacts`에서 `26x86-windows-exe` 다운로드

### 실패 시 빠른 점검

- `No module named webview`: 빌드 로그의 의존성 설치 단계에서 `pywebview` 설치 성공 여부 확인
- EXE 실행 시 빈 화면: 대상 PC에 Microsoft Edge WebView2 Runtime 설치 확인
- `dist/26x86/26x86.exe not found`: PyInstaller 단계 실패 로그(숨김 import/경로 오류) 확인

## 법적

[DISCLAIMER.md](DISCLAIMER.md) · [LICENSE.txt](LICENSE.txt) · [NOTICE.md](NOTICE.md) · [원본 저장소](docs/wiki/Upstream-Repositories.md) · [CREDITS.md](CREDITS.md)

## Apple Silicon Sandbox integration

EFI-native AArch64 translation, AIC and iBoot integration for macOS 26/27 is in development. See [architecture and actual validation status](docs/APPLE_SILICON_SANDBOX.md) and the adopted [VSK isolation design and implementation](docs/VSK.md). VSK product admission is fixed to approved Intel Macs and requires VMX/EPT, VT-d and interrupt remapping. The existing EFI self-test is not a VSK kernel or macOS boot environment.

The reproducible QEMU GUI commands and their result boundaries are documented
in [QEMU Golden Gate GUI validation](docs/QEMU_GOLDEN_GATE_GUI.md). A visible
QEMU window is diagnostic evidence only; it does not certify iBoot, XNU or
physical-Mac boot.

The Sandbox screen in the 26x86 GUI now exposes the caller-supplied VMApple
inputs and a `GTK VM 창 열기` action. On Windows, a Linux VMApple QEMU path is
re-executed in WSLg with a shell-free `wsl.exe` command; the CLI equivalent is
`python3 -m x86 vmapple run --research-only`. Both paths preserve immutable
firmware/iBSS inputs, use COW overlays, and stop at a real post-reset
descriptor boundary instead of forcing iBEC admission.

The iBoot(AArch64) personality is deliberately macOS-only: macOS is supported,
while iOS, iPadOS and other mobile Apple OS requests are rejected before DFU.
Its DFU/IPSW recovery scope uses `_default.ipsw` for Local Recovery. Inspect the
enforced matrix without starting a VM with
`python3 -m x86 personality validate --guest-os macOS`.
