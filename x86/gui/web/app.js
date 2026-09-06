(() => {
  "use strict";

  const DEFAULT_STEPS = [
    { id: "welcome", title: "시작", heading: "26x86에 오신 것을 환영합니다", desc: "오래된 Mac에서 최신 macOS를 사용할 수 있도록 단계별로 안내합니다." },
    { id: "detect", title: "1. 내 Mac 확인", heading: "내 Mac 확인", desc: "하드웨어 정보를 확인합니다." },
    { id: "build", title: "2. 패치 생성", heading: "패치 생성", desc: "OpenCore EFI를 만듭니다." },
    { id: "patch", title: "3. 설치·패치", heading: "설치·패치", desc: "EFI 설치와 루트 패치를 진행합니다." },
    { id: "done", title: "검증 · 활동", heading: "작업과 검증 기록", desc: "생성 결과와 실제 기기 검증을 따로 확인합니다." },
  ];

  const state = {
    steps: DEFAULT_STEPS.slice(),
    currentStep: 0,
    appInfo: null,
    detect: null,
    macos: null,
    patchSummary: "패치 정보를 불러오는 중…",
    canBuild: false,
    mode: "native",
    sandbox: null,
    sandboxPlan: null,
    sandboxTarget: 26,
    sandboxOutput: "",
    sandboxReceipt: null,
    vmapple: null,
    vmappleConfig: {
      qemu: "",
      qemu_img: "",
      firmware: "",
      build_manifest: "",
      tss_helper: "",
      original_ibss: "",
      original_ibec: "",
      ibss: "",
      ibec: "",
      aux: "",
      root: "",
      output: "",
      // The safe/default path requests fresh tickets for the live USB nonce
      // and wraps the untouched Apple IM4P bytes into a new output folder.
      live_personalize: true,
      // Golden Gate's current original iBEC needs this explicitly selected
      // no-service region to reach its Stage2 prompt in the research QEMU.
      optional_rpc_unavailable: true,
      restore_chain: false,
      restore_role_dir: "",
      restore_timeout: 900,
      machine_type: "iBoot(AArch64)",
      guest_os: "macOS",
      recovery_protocol: "DFU/IPSW",
      recovery_image_name: "_default.ipsw",
      boot_picker_enabled: true,
      boot_delay_seconds: 2,
      boot_selection: null,
      boot_picker_trigger: null,
    },
    vmappleReceipt: null,
    vmappleStorage: null,
    bootPicker: null,
    bootPickerPoll: null,
    activity: [],
    globalActionsBound: false,
    buildCompleted: false,
    busy: false,
    bridgeReady: false,
  };

  const els = {
    stepper: document.getElementById("stepper"),
    stepContent: document.getElementById("step-content"),
    btnPrev: document.getElementById("btn-prev"),
    btnNext: document.getElementById("btn-next"),
    progressBar: document.getElementById("progress-bar"),
    stepCounter: document.getElementById("step-counter"),
    statusText: document.getElementById("status-text"),
    versionText: document.getElementById("version-text"),
    appTitle: document.getElementById("app-title"),
    appSubtitle: document.getElementById("app-subtitle"),
    logo: document.getElementById("logo"),
    logoFallback: document.getElementById("logo-fallback"),
    toastHost: document.getElementById("toast-host"),
    settingsDialog: document.getElementById("settings-dialog"),
    settingAnalytics: document.getElementById("setting-analytics"),
    settingVerbose: document.getElementById("setting-verbose"),
    settingMode: document.getElementById("setting-mode"),
    settingMellow: document.getElementById("setting-mellow"),
    settingPayload: document.getElementById("setting-mellow-payload"),
    settingEfi: document.getElementById("setting-mellow-efi"),
  };

  const QT_BRIDGE_METHODS = [
    "get_sandbox_status",
    "set_execution_mode",
    "get_sandbox_plan",
    "prepare_sandbox",
    "get_vmapple_status",
    "inspect_vmapple_storage",
    "get_boot_picker_status",
    "start_boot_picker",
    "tick_boot_picker",
    "boot_picker_key",
    "select_boot_entry",
    "launch_vmapple",
    "get_app_info",
    "set_hardware_profile",
    "validate_surface_efi",
    "get_steps",
    "detect",
    "get_macos_choices",
    "set_target_os",
    "get_patch_status",
    "get_silicon_sandbox_demo",
    "get_status",
    "get_settings",
    "save_settings",
    "prepare_mellow_efi",
    "prepare_mellow_root_efi",
    "host_can_build",
    "launch_wx_action",
    "reveal_log",
    "open_guide",
  ];

  function promisifyQtBridge(bridge) {
    if (!bridge || bridge.__qtWrapped) {
      return bridge;
    }
    const wrapped = { __qtWrapped: true };
    QT_BRIDGE_METHODS.forEach((name) => {
      wrapped[name] = function (...args) {
        return new Promise((resolve, reject) => {
          try {
            const fn = bridge[name];
            if (typeof fn !== "function") {
              reject(new Error(`${name} is not available`));
              return;
            }
            fn.apply(bridge, args.concat([(result) => resolve(result)]));
          } catch (err) {
            reject(err);
          }
        });
      };
    });
    return wrapped;
  }

  function httpInvoke(method, ...args) {
    return fetch("/api/invoke", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ method, args }),
    }).then(async (response) => {
      let payload = null;
      try {
        payload = await response.json();
      } catch (_) {
        throw new Error(`HTTP bridge ${method}: invalid JSON (${response.status})`);
      }
      if (!response.ok || (payload && payload.ok === false && payload.result === undefined)) {
        throw new Error((payload && payload.error) || `HTTP bridge ${method} failed`);
      }
      return payload.result !== undefined ? payload.result : payload;
    });
  }

  function ensureHttpBridge() {
    if (window.__x86HttpBridge && window.__x86HttpBridge.__httpWrapped) {
      return window.__x86HttpBridge;
    }
    const wrapped = { __httpWrapped: true };
    QT_BRIDGE_METHODS.forEach((name) => {
      wrapped[name] = function (...args) {
        return httpInvoke(name, ...args);
      };
    });
    window.__x86HttpBridge = wrapped;
    return wrapped;
  }

  function getBridgeApi() {
    if (window.pywebview && window.pywebview.api) {
      return window.pywebview.api;
    }
    if (window.__x86HttpBridge && window.__x86HttpBridge.__httpWrapped) {
      return window.__x86HttpBridge;
    }
    return null;
  }

  function connectQtWebChannel() {
    if (getBridgeApi()) {
      return;
    }
    if (typeof QWebChannel === "undefined" || typeof qt === "undefined" || !qt.webChannelTransport) {
      return;
    }
    new QWebChannel(qt.webChannelTransport, (channel) => {
      if (channel.objects && channel.objects.bridge) {
        window.pywebview = { api: promisifyQtBridge(channel.objects.bridge) };
        window.dispatchEvent(new Event("pywebviewready"));
      }
    });
  }

  function probeHttpBridge() {
    if (getBridgeApi()) {
      return Promise.resolve(true);
    }
    return fetch("/api/health", { method: "GET", cache: "no-store" })
      .then((response) => (response.ok ? response.json() : null))
      .then((payload) => {
        if (payload && payload.ok) {
          const apiSurface = ensureHttpBridge();
          window.pywebview = { api: apiSurface };
          window.dispatchEvent(new Event("pywebviewready"));
          return true;
        }
        return false;
      })
      .catch(() => false);
  }

  function api(method, ...args) {
    const surface = getBridgeApi();
    if (surface && typeof surface[method] === "function") {
      const result = surface[method](...args);
      return result && typeof result.then === "function" ? result : Promise.resolve(result);
    }
    return httpInvoke(method, ...args);
  }

  function whenBridgeReady(callback) {
    let settled = false;
    const finish = () => {
      if (settled) {
        return;
      }
      settled = true;
      callback();
    };

    if (getBridgeApi()) {
      finish();
      return;
    }

    connectQtWebChannel();
    probeHttpBridge();

    let attempts = 0;
    const maxAttempts = 200;
    const timer = window.setInterval(() => {
      attempts += 1;
      connectQtWebChannel();
      probeHttpBridge().then((ok) => {
        if (settled) {
          window.clearInterval(timer);
          return;
        }
        if (ok || getBridgeApi()) {
          window.clearInterval(timer);
          finish();
        } else if (attempts >= maxAttempts) {
          window.clearInterval(timer);
          const banner = document.getElementById("boot-banner");
          if (banner) {
            banner.innerHTML = "로컬 작업 엔진에 연결하지 못했습니다. 앱을 다시 실행하고 로그를 확인하세요.";
          }
          setStatus("브릿지 대기 시간 초과");
          toast("로컬 작업 엔진 연결 실패", "error");
          try { bindGlobalActions(); renderStepContent(); } catch (_) {}
          settled = true;
        }
      });
    }, 50);

    window.addEventListener(
      "pywebviewready",
      () => {
        window.clearInterval(timer);
        finish();
      },
      { once: true }
    );
  }

  function setStatus(text) {
    els.statusText.textContent = text || "준비됨";
  }

  function toast(message, kind = "info") {
    state.activity.unshift({time: new Date().toLocaleTimeString(), message: String(message), kind});
    state.activity = state.activity.slice(0, 100);
    const node = document.createElement("div");
    node.className = `toast${kind === "error" ? " error" : ""}`;
    node.textContent = message;
    els.toastHost.appendChild(node);
    setTimeout(() => node.remove(), 3200);
  }

  function escapeHtml(value) {
    return String(value ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function infoRow(label, value) {
    return `<div class="info-row"><span class="label">${escapeHtml(label)}</span><span class="value">${escapeHtml(value || "—")}</span></div>`;
  }

  function renderStepper() {
    els.stepper.innerHTML = state.steps
      .map(
        (step, index) =>
          `<button type="button" class="step-btn${index === state.currentStep ? " active" : ""}" aria-current="${index === state.currentStep ? "step" : "false"}" data-step="${index}" ${state.busy ? "disabled" : ""}><span class="step-number">${String(index + 1).padStart(2, "0")}</span>${escapeHtml(step.title.replace(/^\d+\.\s*/, ""))}</button>`
      )
      .join("");

    els.stepper.querySelectorAll(".step-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        const idx = Number(btn.dataset.step);
        if (!Number.isNaN(idx)) goToStep(idx);
      });
    });

    const total = state.steps.length || 1;
    const pct = ((state.currentStep + 1) / total) * 100;
    els.progressBar.style.width = `${pct}%`;
    els.stepCounter.textContent = `${state.currentStep + 1} / ${total}`;
    els.btnPrev.disabled = state.currentStep <= 0 || state.busy;
    els.btnNext.disabled = state.currentStep >= total - 1 || state.busy;
    document.getElementById("sidebar-mode").textContent = state.mode === "sandbox" ? "Apple Silicon Sandbox" : "Native Patch";
    document.getElementById("sidebar-host").textContent = isSurface() ? "Surface Pro 6" : (state.detect?.model || "확인 대기");
  }

  function isSurface() {
    return state.appInfo?.hardware_profile === "surface-pro6-i5-tahoe";
  }

  function renderSurfacePreparation() {
    return `<h2>Surface Pro 6 · macOS Tahoe</h2>
      <p class="lead">i5-8250U · UHD 620 · Android USB 테더링</p>
      <p>준비된 Surface 전용 EFI 폴더를 선택해 파일과 설정을 검사합니다. 검사 결과는 실제 부팅 성공을 의미하지 않습니다.</p>
      <label for="surface-efi">EFI 폴더 경로</label>
      <input id="surface-efi" class="field" value="${escapeHtml(state.appInfo?.surface_efi_path || "")}" placeholder="EFI 폴더의 전체 경로" />
      <button type="button" class="btn primary" id="action-validate-surface">EFI 검사</button>
      <pre id="surface-validation" class="patch-summary"></pre>`;
  }

  function renderWelcome() {
    const sandbox = state.mode === "sandbox";
    return `<div class="welcome-hero"><span class="eyebrow">26x86 / CONTROL CENTER</span>
      <h2>당신의 Mac, 다음 장으로.</h2><p class="lead">기기를 확인하고, 실행 방식을 선택하세요.<br>모든 작업의 준비 상태와 검증 결과를 한곳에서 확인합니다.</p>
      <p class="lead">버전 ${escapeHtml(state.appInfo?.version || "")} · ${escapeHtml(state.appInfo?.bundle_id || "")}</p>
      <p class="lead">${sandbox ? "Apple Silicon Sandbox Mode · native 드라이버 사용 안 함" : "x86 Mode"} · Mellow: ${escapeHtml(state.appInfo?.mellow_deployment || "disabled")}</p>
      ${state.appInfo?.execution_error ? `<p class="note">${escapeHtml(state.appInfo.execution_error)}<br />설정에서 실행 모드와 Mellow 배포 방식을 수정하세요.</p>` : ""}
      <div class="overview-meta"><span class="badge">macOS Tahoe 26</span><span class="badge">Golden Gate 27 · 개발 대상</span><span class="badge warning">실험적 프로젝트</span></div></div>
      <div class="section-label"><h3>실행 방식</h3><span>선택 시 디스크를 변경하지 않습니다</span></div>
      <div class="mode-grid" role="group" aria-label="실행 방식">
        <button class="mode-card${!sandbox ? " selected" : ""}" id="mode-native" aria-pressed="${!sandbox}"><span class="mode-kicker">01 / NATIVE</span><span class="mode-selected" aria-hidden="true"></span><strong>Native Patch</strong><p>OpenCore EFI와 기기별 루트 패치.<br>현재 하드웨어에서 실행할 구성을 준비합니다.</p><span class="badge">OpenCore · Root patches</span></button>
        <button class="mode-card${sandbox ? " selected" : ""}" id="mode-sandbox" aria-pressed="${sandbox}"><span class="mode-kicker">02 / VIRTUAL APPLE SILICON</span><span class="mode-selected" aria-hidden="true"></span><strong>Apple Silicon Sandbox</strong><p>EFI에서 직접 실행하는 가상 Apple Silicon.<br>macOS 26 이상을 위한 실험적 실행 경로입니다.</p><span class="badge warning">개발 중 · macOS 부팅 미검증</span></button>
      </div>
      <p class="support-note">Sandbox 최소 대상: Mac Pro 2009 · SSE4.1 + SSE4.2. 비 Apple 기기는 동작을 보증하지 않으며 관련 이슈를 받지 않습니다.</p>
      <div class="actions"><button class="btn primary" id="action-start">기기 확인하기 →</button><button class="btn secondary" id="action-guide">사용 설명서</button></div>
      <details><summary>기존 하드웨어 프로필</summary><div class="actions"><button class="btn secondary" id="action-surface">Surface Pro 6 · Tahoe</button><button class="btn ghost" id="action-mac">일반 Mac 프로필</button></div><p class="support-note">${isSurface() ? "선택: Surface Pro 6" : "선택: 일반 Mac"} · 이 프로필은 Native Patch에서 사용됩니다.</p></details>`;
  }

  function renderSandbox(stage) {
    const report = state.sandboxPlan || state.sandbox || {};
    const blockers = report.blockers || ["EFI 실행 엔진의 상태를 아직 확인하지 못했습니다."];
    const receipt = state.sandboxReceipt;
    const vm = state.vmapple || {};
    const vmConfig = state.vmappleConfig;
    const livePersonalize = vmConfig.live_personalize !== false;
    const optionalRpcUnavailable = vmConfig.optional_rpc_unavailable === true;
    const restoreChain = vmConfig.restore_chain === true;
    const vmFields = [
      ["qemu", "VMApple QEMU", "/home/developer/.../qemu-system-aarch64"],
      ["qemu_img", "qemu-img", "/usr/bin/qemu-img"],
      ["firmware", "AVPBooter EFI", "원본 AVPBooter.vmapple2.bin 경로"],
      ["build_manifest", "공식 BuildManifest.plist", "Golden Gate IPSW의 BuildManifest.plist"],
      ["tss_helper", "로컬 TSS 요청 도구", "libtatsu 호환 TSS request helper 경로"],
      ["original_ibss", "원본 iBSS IM4P", "변경하지 않은 iBSS.vma2.RELEASE.im4p"],
      ["original_ibec", "원본 iBEC IM4P", "변경하지 않은 iBEC.vma2.RELEASE.im4p"],
      ["aux", "AUX 원본 이미지", "읽기 전용 AUX raw 경로"],
      ["root", "Root 원본 이미지", "읽기 전용 root raw 경로"],
      ["output", "새 VM 출력 폴더", "기존 경로가 아닌 새 폴더 경로"],
    ].map(([key, label, placeholder]) => `<div><label for="vmapple-${key}">${label}</label><input class="field" id="vmapple-${key}" value="${escapeHtml(vmConfig[key] || "")}" placeholder="${escapeHtml(placeholder)}" /></div>`).join("");
    const legacyFields = [
      ["ibss", "기존 개인화 iBSS (진단용)", "이미 개인화된 iBSS.img4"],
      ["ibec", "기존 개인화 iBEC (선택)", "이미 개인화된 iBEC.img4"],
    ].map(([key, label, placeholder]) => `<div><label for="vmapple-${key}">${label}</label><input class="field" id="vmapple-${key}" value="${escapeHtml(vmConfig[key] || "")}" placeholder="${escapeHtml(placeholder)}" /></div>`).join("");
    const requiredVmFields = ["qemu", "qemu_img", "firmware", "aux", "root", "output"].concat(
      livePersonalize ? ["build_manifest", "tss_helper", "original_ibss", "original_ibec"] : ["ibss"]
    ).concat(restoreChain ? ["restore_role_dir"] : []);
    const vmReady = requiredVmFields.every((key) => String(vmConfig[key] || "").trim());
    const vmConfigured = livePersonalize
      ? (vm.live_personalization_configured ? "실시간 TSS 경로 확인됨" : "공식 원본·TSS 경로 입력 필요")
      : (vm.legacy_configured ? "기존 개인화 경로 확인됨" : "경로 입력 필요");
    const vmReceipt = state.vmappleReceipt;
    const storage = state.vmappleStorage;
    const storageStatus = storage
      ? (storage.provisioning_status === "unprovisioned-zero"
        ? "빈 AUX/root · 설치 차단"
        : storage.provisioning_status === "partially-unprovisioned"
          ? "일부 저장장치 비어 있음 · 설치 차단"
        : storage.provisioning_status === "unverified-bounded-scan"
          ? "범위 검사 완료 · 확인 필요"
          : "읽기 검사 완료 · 프로비저닝 미확인")
      : "검사 대기";
    const storageStatusClass = ["unprovisioned-zero", "partially-unprovisioned"].includes(storage?.provisioning_status) ? " warning" : "";
    const storageBlockers = Array.isArray(storage?.blockers) ? storage.blockers : [];
    const picker = state.bootPicker || report.boot_picker || {
      state: "idle", delay_seconds: 2, remaining_seconds: 0, alt_key: "Alt",
      picker_visible: false, selected_entry: null, selection: null, entries: [],
    };
    const pickerEntries = (picker.entries || []).map((entry) => `<button type="button" class="boot-entry${picker.selected_entry === entry.id ? " selected" : ""}" data-boot-entry="${escapeHtml(entry.id)}"><span><strong>${escapeHtml(entry.label)}</strong><small>${escapeHtml(entry.kind)} · macOS ${escapeHtml(entry.target_major)}</small></span><span class="badge${entry.id === "recovery" ? " warning" : ""}">${entry.id === "recovery" ? "복구" : "일반"}</span></button>`).join("");
    const recoverySelected = picker.selection === "recovery" || vmConfig.boot_selection === "recovery";
    // Require an explicit read-only inspection before the launch control is
    // enabled.  A non-zero file is still only ``unverified``; this gate keeps
    // an uninspected or known-empty fixture from being mistaken for an
    // install target while preserving the protocol runner's evidence path.
    const storageLaunchAllowed = Boolean(storage)
      && !["unprovisioned-zero", "partially-unprovisioned"].includes(storage?.provisioning_status);
    const pickerStateLabel = picker.state === "armed" ? `Alt/Option 대기 · ${Number(picker.remaining_seconds || 0).toFixed(2)}초` : picker.state === "picker" ? "부트 피커 표시 중" : picker.state === "selected" && recoverySelected ? "macOS Recovery 선택됨" : picker.state === "default" ? "시간 만료 · macOS 기본 항목" : "대기하지 않음";
    return `<span class="eyebrow">EFI NATIVE / APPLE SILICON SANDBOX</span><h2>${stage === "patch" ? "EFI 준비 결과" : "Sandbox 준비"}</h2>
      <p class="lead">macOS 게스트 부팅에 필요한 구성 요소와 현재 구현 상태를 확인합니다.</p>
      <div class="metric-grid"><div class="metric"><span>실행 계층</span><strong>EFI · AIC · ARM64 JIT</strong></div><div class="metric"><span>최소 CPU</span><strong>SSE4.1 + SSE4.2</strong></div><div class="metric"><span>macOS 실제 부팅</span><strong>미검증</strong></div></div>
      <div class="form-row"><div><label for="sandbox-target">대상 macOS</label><select class="field" id="sandbox-target"><option value="26" ${state.sandboxTarget === 26 ? "selected" : ""}>macOS Tahoe 26</option><option value="27" ${state.sandboxTarget === 27 ? "selected" : ""}>macOS Golden Gate 27</option></select></div><div><label for="sandbox-output">새 출력 폴더 경로</label><input class="field" id="sandbox-output" value="${escapeHtml(state.sandboxOutput)}" placeholder="예: C:/26x86-Sandbox 또는 /Users/me/26x86-Sandbox" /></div></div>
      <div class="policy-grid"><div class="policy-card"><span>MachineType</span><strong>${escapeHtml(vm.machine_type || vmConfig.machine_type || "iBoot(AArch64)")}</strong></div><div class="policy-card"><span>게스트 OS</span><strong class="good-text">${escapeHtml(vm.guest_os || vmConfig.guest_os || "macOS")}</strong></div><div class="policy-card"><span>복구</span><strong>${escapeHtml(vm.recovery_scope?.protocol || vmConfig.recovery_protocol || "DFU/IPSW")} · ${escapeHtml(vm.recovery_scope?.default_image_name || vmConfig.recovery_image_name || "_default.ipsw")}</strong></div></div>
      <p class="support-note policy-note"><strong>iBoot(AArch64) 범위:</strong> macOS만 지원합니다. iOS · iPadOS · 기타 모바일 Apple OS는 부팅·DFU·<code>_default.ipsw</code> 복구 대상으로 받지 않습니다. VMApple 게스트 메타데이터는 <strong>Apple M1 (Virtual)</strong>로 고정되며 실제 Apple 하드웨어 인증을 뜻하지 않습니다.</p>
      <section class="boot-picker-card" aria-labelledby="boot-picker-heading"><div class="boot-picker-heading"><div><span class="eyebrow">POWER ON / 2.0 SEC WINDOW</span><h3 id="boot-picker-heading">부트 피커 · macOS Recovery</h3></div><span class="badge${picker.state === "picker" || picker.state === "selected" ? " good" : " warning"}">${escapeHtml(pickerStateLabel)}</span></div><p class="support-note">전원 인가 후 정확히 2초 동안 <kbd>Alt</kbd>/<kbd>Option</kbd>을 누르면 피커가 표시됩니다. Recovery를 선택한 뒤에만 DFU/IPSW 복구 VM을 시작합니다.</p><div class="boot-picker-status">${infoRow("선택 항목", picker.selection === "recovery" ? "macOS Recovery · _default.ipsw" : picker.selection === "macos" ? `macOS ${state.sandboxTarget}` : "선택 대기")} ${infoRow("입력 기록", picker.trigger || "—")}</div><div class="boot-entries" ${picker.picker_visible ? "" : "hidden"}>${pickerEntries || '<span class="muted">표시할 부트 항목이 없습니다.</span>'}</div><div class="actions"><button type="button" class="btn secondary" id="vmapple-boot-start" ${state.busy ? "disabled" : ""}>2초 부트 피커 시작</button><button type="button" class="btn primary" id="vmapple-launch" ${vmReady && state.bridgeReady && recoverySelected && storageLaunchAllowed ? "" : "disabled"}>Recovery VM 창 열기</button></div>${picker.state === "default" ? '<p class="support-note warning-text">시간이 만료되어 macOS 기본 항목이 선택되었습니다. 현재 VMApple 엔진은 직접 macOS 부팅을 인증하지 않으므로 Recovery를 실행하려면 다시 Alt를 누르세요.</p>' : ""}</section>
      <div class="proof-list"><div class="proof-item"><span>EFI 자체 검사 파일</span><span class="badge${report.artifact_available ? " good" : " warning"}">${report.artifact_available ? "파일 존재" : "미생성"}</span></div><div class="proof-item"><span>VSK 생산 EFI · 외부 trust anchor</span><span class="badge${report.vsk_artifact_available ? " good" : " warning"}">${report.vsk_artifact_available ? "생성됨 · EBS 미호출" : "미생성"}</span></div><div class="proof-item"><span>원본 macOS 부팅</span><span class="badge warning">아직 준비되지 않음</span></div><div class="proof-item"><span>실제 Mac USB 부팅</span><span class="badge warning">실기 검증 필요</span></div></div>
      ${blockers.length ? `<div class="note"><strong>남은 구현 항목</strong><ul>${blockers.map(x => `<li>${escapeHtml(x)}</li>`).join("")}</ul></div>` : ""}
      <p class="support-note">구성: OpenCore config.plist · iBoot 엔진 · SandboxSMBIOS · Hardware/DevProp. 현재 준비 기능은 EFI 자체 검사 패키지를 생성합니다. macOS 설치 또는 부팅을 시작하지 않습니다. 기존 디스크에 자동으로 기록하지 않습니다.</p>
      <div class="actions"><button class="btn secondary" id="sandbox-refresh">준비 상태 다시 확인</button><button class="btn primary" id="sandbox-prepare" ${report.stageable && state.bridgeReady ? "" : "disabled"}>EFI 자체 검사 패키지 준비</button></div>
      ${receipt ? `<pre class="patch-summary" role="status">${escapeHtml(JSON.stringify(receipt, null, 2))}</pre>` : ""}
      <details class="vm-panel" open><summary>실제 보이는 VMApple 복구 VM · <span class="badge${vmConfigured.includes("확인됨") ? " good" : " warning"}">${vmConfigured}</span></summary>
        <p class="support-note">WSLg GTK 창을 표시하는 연구용 실행 경로입니다. 아래 기본 경로는 공식 BuildManifest와 현재 USB nonce로 Apple TSS 티켓을 요청하고, 변경하지 않은 원본 iBSS/iBEC를 새 출력 폴더에만 IMG4로 감쌉니다. IPSW·설치 파일·기존 ESP는 수정하지 않습니다. 실제 USB descriptor가 bulk endpoint 4를 광고할 때만 iBSS→iBEC를 시도하며 전환을 강제하지 않습니다.</p>
        <label class="check-row" for="vmapple-live"><input type="checkbox" id="vmapple-live" ${livePersonalize ? "checked" : ""} /> <span><strong>실시간 Apple TSS 개인화</strong><small>현재 USB nonce에 묶인 티켓을 새 폴더에 생성 (권장)</small></span></label>
        <label class="check-row" for="vmapple-rpc"><input type="checkbox" id="vmapple-rpc" ${optionalRpcUnavailable ? "checked" : ""} /> <span><strong>Golden Gate Stage2 연구 경로</strong><small>원본 iBEC의 선택 RPC 주소를 무서비스 상태로 매핑합니다. 게스트 서비스나 서명 우회가 아니며 연구 산출물로만 남습니다.</small></span></label>
        <div class="vm-fields">${vmFields}</div>
        <details class="vm-legacy"><summary>iBootStage2 뒤 공식 복구 역할 전송 (선택)</summary><p class="support-note">BuildManifest와 일치하는 원본 RestoreTrustCache/RestoreRamDisk/RestoreDeviceTree/RestoreKernelCache IM4P를 새 폴더에서 정규화하고, 이미 발급된 iBEC 티켓으로 감싼 뒤 <code>bootx</code>까지 보냅니다. XNU나 설치 화면을 증명하지 않습니다.</p><label class="check-row" for="vmapple-restore"><input type="checkbox" id="vmapple-restore" ${restoreChain ? "checked" : ""} /> <span><strong>Stage2 복구 체인 실행</strong><small>대용량 RamDisk/KernelCache 전송이 포함되며 COW 디스크에서만 실행</small></span></label><div class="vm-fields"><div><label for="vmapple-restore_role_dir">원본 Restore 역할 폴더</label><input class="field" id="vmapple-restore_role_dir" value="${escapeHtml(vmConfig.restore_role_dir || "")}" placeholder="RestoreTrustCache.im4p 등이 있는 폴더" /></div><div><label for="vmapple-restore_timeout">복구 체인 제한 시간(초)</label><input class="field" id="vmapple-restore_timeout" value="${escapeHtml(vmConfig.restore_timeout || 900)}" inputmode="numeric" /></div></div></details>
        <section class="storage-preflight" aria-labelledby="storage-preflight-heading"><div class="boot-picker-heading"><div><span class="eyebrow">READ ONLY / STORAGE GATE</span><h3 id="storage-preflight-heading">AUX · root 설치 대상 검사</h3></div><span class="badge${storageStatusClass}">${escapeHtml(storageStatus)}</span></div><p class="support-note">원본 파일을 열어 쓰지 않고, 빈 fixture 여부와 일부 APFS 표식만 확인합니다. Apple Silicon의 정확한 hardware model로 생성된 AUX와 설치 대상이 있는 root라는 사실은 별도 영수증 없이는 인증하지 않습니다.</p><div class="boot-picker-status">${infoRow("프로비저닝", storage?.provisioning_status || "검사하지 않음")} ${infoRow("설치 UI 가능성", storage ? (storage.installer_ui_possible === false ? "차단됨" : "확인되지 않음") : "검사 대기")}</div>${storageBlockers.length ? `<ul class="support-note warning-text">${storageBlockers.map(item => `<li>${escapeHtml(item)}</li>`).join("")}</ul>` : ""}<div class="actions"><button type="button" class="btn secondary" id="vmapple-storage-inspect" ${state.busy ? "disabled" : ""}>저장장치 읽기 검사</button><button type="button" class="btn secondary" id="vmapple-refresh">VMApple 경로 다시 읽기</button></div></section>
        ${vmReceipt ? `<pre class="patch-summary" role="status">${escapeHtml(JSON.stringify(vmReceipt, null, 2))}</pre>` : ""}
      </details>`;
  }

  function renderDetect(step) {
    if (isSurface()) return `<h2>대상: Surface Pro 6</h2>
      <p class="lead">사용자가 지정한 설치 대상이며, 이 준비용 컴퓨터의 사양을 사용해 EFI를 변경하지 않습니다.</p>
      <div class="info-grid">
        ${infoRow("CPU", "Intel Core i5-8250U")}
        ${infoRow("GPU", "Intel UHD 620 · Kaby Lake")}
        ${infoRow("인터넷", "Android USB 테더링 · HoRNDIS")}
        ${infoRow("무선랜", "순정 Marvell · macOS 드라이버 미지원")}
        ${infoRow("OS", "macOS Tahoe 26 · Darwin 25")}
      </div><p>터치·펜 입력은 EFI의 BigSurface와 macOS IPTSDaemon 설치가 모두 필요합니다. 실제 기기에서 작동을 확인하세요.</p>`;
    const d = state.detect || {};
    const platformNote = !d.host_is_mac && d.macos_only_note
      ? `<div class="note">${escapeHtml(d.macos_only_note)}</div>`
      : "";
    const modelLabel = d.host_is_mac === false ? "호스트" : "Mac 모델";
    const osLabel = d.host_is_mac === false ? "호스트 OS" : "현재 macOS";
    return `
      <h2>${escapeHtml(step.heading)}</h2>
      <p class="lead">${escapeHtml(step.desc)}</p>
      ${platformNote}
      <div class="info-grid">
        ${infoRow(modelLabel, d.model)}
        ${infoRow("제품명", d.marketing_name)}
        ${infoRow("프로세서", d.cpu || "정보 없음")}
        ${infoRow(osLabel, `${d.os_version || "—"} (${d.os_build || "—"})`)}
      </div>
      <div class="actions">
        <button type="button" class="btn secondary" id="action-redetect">다시 확인</button>
        <button type="button" class="btn secondary" id="action-model">모델 변경</button>
      </div>
    `;
  }

  function renderBuild(step) {
    if (state.mode === "sandbox") return renderSandbox("build");
    if (isSurface()) return renderSurfacePreparation();
    const macos = state.macos || { choices: [], selected_kernel: null };
    const selected = macos.choices.find((c) => c.kernel === macos.selected_kernel) || macos.choices[0];
    const warn = !state.canBuild
      ? `<div class="note">${escapeHtml(
          state.buildMessage ||
            state.appInfo?.macos_only_message ||
            "이 Mac에서는 EFI를 만들 수 없습니다. 다른 지원 Mac에서 실행하거나 고급 모드 설정을 확인해 주세요."
        )}</div>`
      : "";
    const options = macos.choices
      .map(
        (c) =>
          `<option value="${c.kernel}"${c.kernel === macos.selected_kernel ? " selected" : ""}>${escapeHtml(c.label)}</option>`
      )
      .join("");

    return `
      <h2>${escapeHtml(step.heading)}</h2>
      <p class="lead">${escapeHtml(step.desc)}</p>
      ${warn}
      <label for="macos-select"><strong>설치할 macOS</strong></label>
      <select id="macos-select" class="field">${options}</select>
      <div class="info-grid">
        ${infoRow("현재 실행 중", macos.current_marketing || "—")}
        ${infoRow("선택한 버전", selected?.label || "—")}
        ${macos.recommended ? infoRow("Apple 공식 지원", macos.recommended) : ""}
        ${infoRow("대상 Mac", state.detect?.marketing_name || state.detect?.model || "—")}
      </div>
      <div class="actions">
        <button type="button" class="btn primary" id="action-build"${state.canBuild ? "" : " disabled"}>패치 생성 시작</button>
      </div>
    `;
  }

  function renderPatch(step) {
    if (state.mode === "sandbox") return renderSandbox("patch");
    if (state.appInfo?.execution?.is_sandbox) return `<h2>Apple Silicon Sandbox Mode</h2>
      <p class="lead">가상화용 모드입니다. Mellow.kext와 native EFI·루트 패치는 사용할 수 없습니다.</p>
      <p>아래는 공개된 Apple Silicon 부트 체인 개념을 <strong>시뮬레이션</strong>한 것입니다. 실제 부팅도, 실제 QEMU·USB 실행도 아닙니다.</p>
      <div class="actions">
        <button type="button" class="btn secondary" id="action-silicon-demo">부트 체인 시뮬레이션 실행</button>
      </div>
      <pre class="patch-summary" id="silicon-demo"></pre>`;
    if (state.appInfo?.mellow_deployment === "efi") return `<h2>Mellow EFI 준비</h2>
      <p class="lead">선택한 EFI를 새 폴더로 복사하고 Mellow 진단 kext를 추가합니다.</p>
      <div class="patch-summary">${escapeHtml(state.patchSummary)}</div>
      <label for="mellow-output">새 출력 폴더</label><input class="field" id="mellow-output" placeholder="아직 존재하지 않는 폴더의 전체 경로" />
      <button type="button" class="btn primary" id="action-mellow-efi">EFI 준비</button>
      <pre class="patch-summary" id="mellow-result"></pre>`;
    if (isSurface()) return `<h2>Surface Pro 6 루트 패치</h2>
      <p>설치된 Tahoe에서 AppleHDA와 KDK 조건을 검사한 뒤 기존 26x86 패치 엔진을 실행합니다. 먼저 USB EFI로 macOS를 부팅하세요.</p>
      <div class="patch-summary" id="patch-summary">${escapeHtml(state.patchSummary)}</div>
      <div class="actions">
        <button type="button" class="btn primary" id="action-patch"${state.appInfo?.host_is_mac ? "" : " disabled"}>macOS 루트 패치 열기</button>
        <button type="button" class="btn secondary" id="action-unpatch"${state.appInfo?.host_is_mac ? "" : " disabled"}>macOS 루트 패치 되돌리기</button>
      </div>`;
    const needBuild = !state.buildCompleted
      ? `<div class="note">먼저 패치(EFI)를 생성해 주세요. 생성 후 EFI 설치와 루트 패치를 진행할 수 있습니다.</div>`
      : "";
    return `
      <h2>${escapeHtml(step.heading)}</h2>
      <p class="lead">${escapeHtml(step.desc)}</p>
      ${needBuild}
      <div class="patch-summary" id="patch-summary">${escapeHtml(state.patchSummary)}</div>
      <div class="actions">
        <button type="button" class="btn primary" id="action-install">EFI 설치 시작</button>
        <button type="button" class="btn secondary" id="action-patch">루트 패치 적용</button>
        <button type="button" class="btn secondary" id="action-unpatch">루트 패치 되돌리기</button>
      </div>
    `;
  }

  function renderDone() {
    return `<span class="eyebrow">EVIDENCE / ACTIVITY</span><h2>작업과 검증 기록</h2><p class="lead">창을 열거나 단계를 이동한 사실은 생성·설치·부팅 성공을 의미하지 않습니다.</p>
      <div class="proof-list"><div class="proof-item"><span>Native EFI 생성</span><span class="badge${state.buildCompleted ? " good" : " warning"}">${state.buildCompleted ? "백엔드 생성 완료 보고" : "완료 보고 없음"}</span></div><div class="proof-item"><span>Sandbox EFI 패키지</span><span class="badge">${state.sandboxReceipt?.ok ? "준비 완료 · 자체 검사용" : "준비 기록 없음"}</span></div><div class="proof-item"><span>실제 macOS / Mac USB 부팅</span><span class="badge warning">미검증</span></div></div>
      <div class="section-label"><h3>이번 세션의 활동</h3><span>최근 100개</span></div>
      ${state.activity.length ? `<ol class="activity-list">${state.activity.map(x => `<li class="${x.kind === "error" ? "error" : ""}"><time>${escapeHtml(x.time)}</time><span>${escapeHtml(x.message)}</span></li>`).join("")}</ol>` : '<p class="empty-state">아직 실행한 작업이 없습니다.</p>'}
      <div class="actions"><button class="btn secondary" id="action-log">로그 파일 열기</button><button class="btn secondary" id="action-advanced" ${state.appInfo?.advanced_enabled ? "" : "disabled"}>고급 모드</button><button class="btn ghost" id="action-finish">창 닫기</button></div>`;
  }

  function renderStepContent() {
    const step = state.steps[state.currentStep];
    if (!step) return;

    const builders = {
      welcome: renderWelcome,
      detect: renderDetect,
      build: renderBuild,
      patch: renderPatch,
      done: renderDone,
    };

    const html = (builders[step.id] || renderWelcome)(step);
    els.stepContent.innerHTML = html;
    // A refreshed Sandbox plan can replace a long step while the user is
    // scrolled near its bottom. Keep each step navigation anchored at its
    // heading so the status and action controls never appear clipped.
    els.stepContent.scrollTop = 0;
    if (!state.appInfo?.execution?.can_native_apply) {
      ["action-build", "action-install", "action-patch", "action-unpatch", "action-advanced", "action-model"].forEach((id) => {
        const button = document.getElementById(id); if (button) button.disabled = true;
      });
    }
    bindStepActions(step.id);
    setStatus(step.title);
    renderStepper();
  }

  function applyBootPickerSnapshot(snapshot) {
    if (!snapshot || typeof snapshot !== "object") return;
    state.bootPicker = snapshot;
    if (snapshot.selection === "recovery" || snapshot.selection === "macos") {
      state.vmappleConfig.boot_selection = snapshot.selection;
      state.vmappleConfig.boot_picker_trigger = snapshot.trigger || null;
    }
  }

  function stopBootPickerPolling() {
    if (state.bootPickerPoll !== null) {
      window.clearInterval(state.bootPickerPoll);
      state.bootPickerPoll = null;
    }
  }

  function startBootPickerPolling() {
    stopBootPickerPolling();
    state.bootPickerPoll = window.setInterval(async () => {
      if (!state.bootPicker || !["armed", "picker"].includes(state.bootPicker.state)) {
        stopBootPickerPolling();
        return;
      }
      try {
        const snapshot = await api("tick_boot_picker");
        applyBootPickerSnapshot(snapshot);
        if (["armed", "picker"].includes(snapshot.state)) {
          if (["build", "patch"].includes(state.steps[state.currentStep]?.id) && state.mode === "sandbox") renderStepContent();
        } else {
          stopBootPickerPolling();
          renderStepContent();
        }
      } catch (err) {
        stopBootPickerPolling();
        toast(String(err.message || err), "error");
      }
    }, 80);
  }

  async function bindStepActions(stepId) {
    const bind = (id, handler) => {
      const node = document.getElementById(id);
      if (node) node.addEventListener("click", async () => {
        if (state.busy) return;
        state.busy = true; renderStepper(); node.disabled = true;
        try { await handler(); } catch (err) { toast(String(err.message || err), "error"); }
        finally { state.busy = false; if (node.isConnected) node.disabled = false; renderStepper(); }
      });
    };
    bind("action-mellow-efi", async () => {
      const button = document.getElementById("action-mellow-efi");
      button.disabled = true;
      try {
        const result = await api("prepare_mellow_efi", document.getElementById("mellow-output").value.trim());
        document.getElementById("mellow-result").textContent = result.ok ? `준비됨: ${result.output}\n실제 부팅 및 Metal 가속은 미검증입니다.` : result.error;
      } catch (err) { toast(String(err.message || err), "error"); }
      finally { button.disabled = false; }
    });

    if ((stepId === "build" || stepId === "patch") && state.mode === "sandbox") {
      const target = document.getElementById("sandbox-target");
      const output = document.getElementById("sandbox-output");
      output.addEventListener("input", () => { state.sandboxOutput = output.value; });
      target.addEventListener("change", async () => {
        state.sandboxTarget = Number(target.value); state.sandboxPlan = null; state.sandboxReceipt = null; state.vmappleStorage = null;
        await refreshSandbox();
      });
      const vmFieldNames = ["qemu", "qemu_img", "firmware", "build_manifest", "tss_helper", "original_ibss", "original_ibec", "ibss", "ibec", "aux", "root", "output"];
      vmFieldNames.forEach((name) => {
        const field = document.getElementById(`vmapple-${name}`);
        if (field) field.addEventListener("input", () => {
          state.vmappleConfig[name] = field.value;
          if (name === "aux" || name === "root") state.vmappleStorage = null;
        });
      });
      const liveToggle = document.getElementById("vmapple-live");
      if (liveToggle) liveToggle.addEventListener("change", () => {
        state.vmappleConfig.live_personalize = liveToggle.checked;
        renderStepContent();
      });
      const rpcToggle = document.getElementById("vmapple-rpc");
      if (rpcToggle) rpcToggle.addEventListener("change", () => {
        state.vmappleConfig.optional_rpc_unavailable = rpcToggle.checked;
      });
      const restoreToggle = document.getElementById("vmapple-restore");
      if (restoreToggle) restoreToggle.addEventListener("change", () => {
        state.vmappleConfig.restore_chain = restoreToggle.checked;
        renderStepContent();
      });
      const restoreTimeout = document.getElementById("vmapple-restore_timeout");
      if (restoreTimeout) restoreTimeout.addEventListener("input", () => {
        const numeric = Number(restoreTimeout.value);
        if (Number.isFinite(numeric)) state.vmappleConfig.restore_timeout = numeric;
      });
      bind("sandbox-refresh", refreshSandbox);
      bind("vmapple-refresh", refreshVmapple);
      bind("vmapple-storage-inspect", async () => {
        const result = await api("inspect_vmapple_storage", {
          aux: state.vmappleConfig.aux,
          root: state.vmappleConfig.root,
          aux_offset: Number(state.vmappleConfig.aux_offset || 0),
        });
        if (!result.ok) throw new Error(result.error || "저장장치 읽기 검사를 완료하지 못했습니다.");
        state.vmappleStorage = result;
        renderStepContent();
        if (["unprovisioned-zero", "partially-unprovisioned"].includes(result.provisioning_status)) {
          toast("빈 AUX/root fixture가 확인되어 설치 VM 실행을 막았습니다.", "error");
        } else {
          toast("저장장치 읽기 검사 완료 · 프로비저닝은 별도 확인이 필요합니다.");
        }
      });
      bind("vmapple-boot-start", async () => {
        const result = await api("start_boot_picker", state.sandboxTarget, state.vmappleConfig.recovery_protocol, state.vmappleConfig.recovery_image_name);
        if (!result.ok) throw new Error(result.error || "부트 피커를 시작하지 못했습니다.");
        state.vmappleConfig.boot_selection = null;
        state.vmappleConfig.boot_picker_trigger = null;
        applyBootPickerSnapshot(result);
        startBootPickerPolling();
        state.busy = false;
        renderStepContent();
        toast("2초 부트 피커를 시작했습니다. 지금 Alt/Option을 누르세요.");
      });
      document.querySelectorAll("[data-boot-entry]").forEach((entry) => {
        entry.addEventListener("click", async () => {
          if (state.busy) return;
          const result = await api("select_boot_entry", entry.dataset.bootEntry);
          if (!result.ok) {
            toast(result.error || "부트 항목을 선택하지 못했습니다.", "error");
            return;
          }
          stopBootPickerPolling();
          applyBootPickerSnapshot(result);
          renderStepContent();
          toast(result.selection === "recovery" ? "macOS Recovery 선택 · _default.ipsw" : "macOS 기본 항목 선택");
        });
      });
      bind("vmapple-launch", async () => {
        if (state.vmappleConfig.boot_selection !== "recovery") {
          throw new Error("먼저 Alt/Option으로 부트 피커를 열고 macOS Recovery를 선택하세요.");
        }
        if (!state.vmappleStorage) {
          throw new Error("먼저 AUX/root 저장장치 읽기 검사를 실행하세요.");
        }
        if (["unprovisioned-zero", "partially-unprovisioned"].includes(state.vmappleStorage?.provisioning_status)) {
          throw new Error("AUX/root가 빈 fixture입니다. hardware-model이 일치하는 프로비저닝 저장장치를 먼저 지정하세요.");
        }
        const config = {
          ...state.vmappleConfig,
          target_major: state.sandboxTarget,
          display: "gtk",
          research_only: true,
        };
        const result = await api("launch_vmapple", config);
        if (!result.ok) throw new Error(result.error || "VMApple 창을 시작하지 못했습니다.");
        state.vmappleReceipt = result;
        toast(`VMApple GTK 창을 열었습니다 · PID ${result.pid} · macOS 부팅 미검증`);
        renderStepContent();
      });
      bind("sandbox-prepare", async () => {
        state.sandboxOutput = output.value.trim();
        if (!state.sandboxOutput) throw new Error("새 출력 폴더의 전체 경로를 입력하세요.");
        const result = await api("prepare_sandbox", state.sandboxTarget, state.sandboxOutput);
        if (!result.ok) throw new Error(result.error || "EFI 패키지를 준비하지 못했습니다.");
        state.sandboxReceipt = result; toast("EFI 자체 검사 패키지 준비 완료 · macOS 부팅 미검증"); renderStepContent();
      });
      return;
    }
    if (stepId === "welcome") {
      const chooseMode = async (mode) => {
        const result = await api("set_execution_mode", mode);
        if (!result.ok) throw new Error(result.error || "실행 방식을 변경하지 못했습니다.");
        state.mode = mode; state.sandboxPlan = null; renderStepContent();
        toast(mode === "sandbox" ? "Apple Silicon Sandbox 선택 · EFI 개발 경로" : "Native Patch 선택");
      };
      bind("mode-native", () => chooseMode("native"));
      bind("mode-sandbox", () => chooseMode("sandbox"));
      const selectProfile = async (profile) => {
        const result = await api("set_hardware_profile", profile);
        if (!result.ok) return toast(result.error, "error");
        state.appInfo.hardware_profile = profile;
        renderStepContent();
      };
      bind("action-surface", () => selectProfile("surface-pro6-i5-tahoe"));
      bind("action-mac", () => selectProfile(null));
      bind("action-start", () => { state.busy = false; goToStep(1); });
      bind("action-guide", () => api("open_guide").catch(() => toast("도움말을 열 수 없습니다.", "error")));
    }

    if (stepId === "detect") {
      bind("action-redetect", async () => {
        setStatus("Mac 정보를 확인하는 중…");
        try {
          const result = await api("detect", true);
          state.detect = result.detect;
          renderStepContent();
          toast("Mac 정보 확인 완료");
        } catch (err) {
          toast(String(err.message || err), "error");
        } finally {
          setStatus("준비됨");
        }
      });
      bind("action-model", async () => {
        const result = await api("launch_wx_action", "model_change");
        if (!result.ok) toast(result.error || "모델 변경을 시작할 수 없습니다.", "error");
        else toast("모델 선택 창을 열었습니다.");
      });
    }

    if (stepId === "build") {
      bind("action-validate-surface", async () => {
        const output = document.getElementById("surface-validation");
        output.textContent = "검사 중…";
        try {
          const result = await api("validate_surface_efi", document.getElementById("surface-efi").value);
          output.textContent = [result.ok ? "정적 EFI 검사 통과 · 실제 부팅 미확인" : "EFI 검사 실패",
            ...(result.errors || []), ...(result.warnings || []),
            `루트 패치 설정: ${result.root_patch_ready ? "준비됨 (macOS 사전 검사 필요)" : "미완료"}`].join("\n");
        } catch (err) { output.textContent = String(err.message || err); }
      });
      const select = document.getElementById("macos-select");
      if (select) {
        select.addEventListener("change", async () => {
          const kernel = Number(select.value);
          const result = await api("set_target_os", kernel);
          if (result.ok) {
            state.macos.selected_kernel = kernel;
            renderStepContent();
          }
        });
      }
      bind("action-build", async () => {
        setStatus("패치 생성 창을 여는 중…");
        const result = await api("launch_wx_action", "build");
        if (!result.ok) {
          toast(result.error || "패치 생성을 시작할 수 없습니다.", "error");
        } else {
          // Opening a build window does not prove the build completed.
          toast("패치 생성 창을 열었습니다.");
        }
        setStatus("준비됨");
      });
    }

    if (stepId === "patch") {
      bind("action-silicon-demo", async () => {
        const result = await api("get_silicon_sandbox_demo");
        const node = document.getElementById("silicon-demo");
        if (!node) return;
        node.textContent = result.ok
          ? JSON.stringify(result.demo, null, 2)
          : (result.error || "시뮬레이션을 실행하지 못했습니다.");
      });
      bind("action-install", async () => {
        const result = await api("launch_wx_action", "install");
        if (!result.ok) toast(result.error || "EFI 설치를 시작할 수 없습니다.", "error");
        else toast("EFI 설치 창을 열었습니다.");
      });
      bind("action-patch", async () => {
        const result = await api("launch_wx_action", "patch");
        if (!result.ok) toast(result.error || "루트 패치를 시작할 수 없습니다.", "error");
        else toast("루트 패치 창을 열었습니다.");
      });
      bind("action-unpatch", async () => {
        const result = await api("launch_wx_action", "unpatch");
        if (!result.ok) toast(result.error || "되돌리기를 시작할 수 없습니다.", "error");
        else toast("루트 패치 되돌리기 창을 열었습니다.");
      });
    }

    if (stepId === "done") {
      bind("action-log", () => api("reveal_log"));
      bind("action-advanced", async () => {
        const result = await api("launch_wx_action", "advanced");
        if (!result.ok) toast(result.error || "고급 모드를 열 수 없습니다.", "error");
      });
      bind("action-finish", () => window.close());
    }
  }

  function goToStep(index) {
    if (state.busy || index < 0 || index >= state.steps.length) return;
    state.currentStep = index;
    renderStepContent();
    els.stepContent.focus({preventScroll: true});
    if (state.mode === "sandbox" && ["build", "patch"].includes(state.steps[index]?.id)) {
      refreshSandbox();
    } else if (state.steps[index]?.id === "patch") {
      refreshPatchStatus();
    }
  }

  async function refreshSandbox() {
    try {
      const target = state.sandboxTarget;
      const result = await api("get_sandbox_plan", target);
      if (!result.ok) throw new Error(result.error || "Sandbox 준비 상태를 불러오지 못했습니다.");
      if (state.sandboxTarget !== target) return;
      state.sandboxPlan = result;
      if (["build", "patch"].includes(state.steps[state.currentStep]?.id) && state.mode === "sandbox") renderStepContent();
    } catch (err) { toast(String(err.message || err), "error"); }
  }

  async function refreshVmapple() {
    try {
      const result = await api("get_vmapple_status");
      state.vmapple = result;
      state.vmappleStorage = null;
      const values = result.values || {};
      Object.keys(state.vmappleConfig).forEach((name) => {
        if (!state.vmappleConfig[name] && typeof values[name] === "string") {
          state.vmappleConfig[name] = values[name];
        }
      });
      if (["build", "patch"].includes(state.steps[state.currentStep]?.id) && state.mode === "sandbox") {
        renderStepContent();
      }
      toast(result.configured ? "VMApple 경로 구성이 확인되었습니다." : "VMApple에 필요한 경로를 입력하세요.");
    } catch (err) {
      toast(String(err.message || err), "error");
    }
  }

  async function refreshPatchStatus() {
    const summaryEl = document.getElementById("patch-summary");
    if (summaryEl) summaryEl.innerHTML = `<span class="spinner"></span>불러오는 중…`;
    try {
      const result = await api("get_patch_status");
      state.patchSummary = result.summary || "패치 정보 없음";
      if (summaryEl) summaryEl.textContent = state.patchSummary;
    } catch (err) {
      state.patchSummary = "패치 정보를 불러오지 못했습니다.";
      if (summaryEl) summaryEl.textContent = state.patchSummary;
    }
  }

  async function loadInitialData() {
    const [appInfo, steps, detectResult, macos, buildCheck, status, vmappleStatus] = await Promise.all([
      api("get_app_info"),
      api("get_steps"),
      api("detect", false),
      api("get_macos_choices"),
      api("host_can_build"),
      api("get_status"),
      api("get_vmapple_status").catch(() => ({ok: false, configured: false, values: {}})),
    ]);

    state.appInfo = appInfo;
    state.steps = steps.map(step => ({...step, title: ({welcome: "개요", detect: "기기 확인", build: "EFI 준비", patch: "설치 · 패치", done: "검증 · 활동"})[step.id] || step.title}));
    state.detect = detectResult.detect;
    state.macos = macos;
    state.canBuild = !!buildCheck.can_build;
    state.buildMessage = buildCheck.message || null;
    state.buildCompleted = !!status.build_completed;
    state.vmapple = vmappleStatus;
    const vmValues = vmappleStatus.values || {};
    Object.keys(state.vmappleConfig).forEach((name) => {
      if (typeof vmValues[name] === "string") state.vmappleConfig[name] = vmValues[name];
    });

    els.appTitle.textContent = appInfo.app_name;
    els.appSubtitle.textContent = appInfo.bundle_id;
    els.versionText.textContent = `v${appInfo.version}`;

    if (appInfo.logo_url) {
      els.logo.src = appInfo.logo_url;
      els.logo.hidden = false;
      els.logoFallback.hidden = true;
    }

    try {
      const report = await api("get_sandbox_status");
      if (report.ok) { state.sandbox = report; state.mode = report.execution_mode === "sandbox" ? "sandbox" : "native"; }
    } catch (err) { state.sandbox = {blockers: ["Sandbox API 연결 실패: " + String(err.message || err)]}; }
    state.bridgeReady = true;
    const connection = document.getElementById("connection-badge");
    connection.textContent = "로컬 엔진 연결됨"; connection.className = "badge good";
    const banner = document.getElementById("boot-banner");
    if (banner) banner.remove();
    renderStepContent();
    setStatus(appInfo.status_ready);
  }

  async function openSettings() {
    try {
      const result = await api("get_settings");
      const settings = result.settings || {};
      els.settingAnalytics.checked = !!settings.analytics;
      els.settingVerbose.checked = !!settings.verbose_logging;
      els.settingMode.value = settings.execution_mode || "x86";
      els.settingMode.disabled = !!state.appInfo?.execution?.environment_locked;
      els.settingMellow.value = settings.mellow_deployment || "disabled";
      els.settingPayload.value = settings.mellow_payload || "";
      els.settingEfi.value = settings.mellow_efi || "";
      updateModeControls();
      els.settingsDialog.showModal();
    } catch (err) {
      toast("설정을 불러올 수 없습니다.", "error");
    }
  }

  async function saveSettings(event) {
    event.preventDefault();
    try {
      const result = await api("save_settings", {
        analytics: els.settingAnalytics.checked,
        verbose_logging: els.settingVerbose.checked,
        execution_mode: els.settingMode.value,
        mellow_deployment: els.settingMellow.value,
        mellow_payload: els.settingPayload.value.trim(),
        mellow_efi: els.settingEfi.value.trim(),
      });
      if (!result.ok) throw new Error(result.error || "save failed");
      els.settingsDialog.close();
      state.appInfo = await api("get_app_info");
      state.canBuild = (await api("host_can_build")).can_build;
      state.buildCompleted = false;
      state.patchSummary = (await api("get_patch_status")).summary || "";
      renderStepContent();
      toast("설정을 저장했습니다.");
    } catch (err) {
      toast(String(err.message || err), "error");
    }
  }

  function bindGlobalActions() {
    if (state.globalActionsBound) return;
    state.globalActionsBound = true;
    els.settingMode.addEventListener("change", updateModeControls);
    els.settingMellow.addEventListener("change", updateModeControls);
    document.getElementById("setting-root-prepare").addEventListener("click", async () => {
      const button = document.getElementById("setting-root-prepare");
      const resultNode = document.getElementById("setting-root-result");
      button.disabled = true;
      try {
        const result = await api("prepare_mellow_root_efi", els.settingEfi.value.trim(),
          document.getElementById("setting-root-output").value.trim(), els.settingPayload.value.trim());
        if (!result.ok) throw new Error(result.error || "EFI 준비 실패");
        els.settingEfi.value = result.output;
        resultNode.textContent = "새 EFI를 준비했습니다. 디스크 Lilu 조건을 확인한 뒤 설정을 저장하세요.";
      } catch (err) { resultNode.textContent = String(err.message || err); }
      finally { button.disabled = false; }
    });
    els.btnPrev.addEventListener("click", () => goToStep(state.currentStep - 1));
    els.btnNext.addEventListener("click", () => goToStep(state.currentStep + 1));
    document.getElementById("btn-settings").addEventListener("click", openSettings);
    document.getElementById("btn-help").addEventListener("click", () => api("open_guide").catch(err => toast(String(err.message || err), "error")));
    document.getElementById("settings-cancel").addEventListener("click", () => els.settingsDialog.close());
    document.getElementById("settings-save").addEventListener("click", saveSettings);

    document.addEventListener("keydown", (event) => {
      const pickerNavigationKey = ["ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight", "Enter", "Return", "Escape", "Esc"].includes(event.key);
      const pickerHotkey = state.bootPicker && state.bootPicker.state === "armed" && (event.key === "Alt" || event.key === "Option");
      const pickerNavigation = state.bootPicker && state.bootPicker.state === "picker" && pickerNavigationKey;
      if (pickerHotkey || pickerNavigation) {
        event.preventDefault();
        api("boot_picker_key", event.key, true).then((snapshot) => {
          if (!snapshot || snapshot.ok === false) {
            toast(snapshot?.error || "Alt 입력을 처리하지 못했습니다.", "error");
            return;
          }
          applyBootPickerSnapshot(snapshot);
          startBootPickerPolling();
          renderStepContent();
          toast(pickerHotkey ? "Alt/Option 입력 확인 · 부트 피커를 표시했습니다." : "부트 피커 키 입력을 반영했습니다.");
        }).catch((err) => toast(String(err.message || err), "error"));
        return;
      }
      if (event.key === "ArrowRight" && (event.metaKey || event.ctrlKey)) {
        goToStep(Math.min(state.steps.length - 1, state.currentStep + 1));
      }
      if (event.key === "ArrowLeft" && (event.metaKey || event.ctrlKey)) {
        goToStep(Math.max(0, state.currentStep - 1));
      }
    });
  }

  function updateModeControls() {
    const sandbox = els.settingMode.value === "apple-silicon-sandbox";
    if (sandbox) els.settingMellow.value = "disabled";
    [els.settingMellow, els.settingPayload, els.settingEfi].forEach((node) => { node.disabled = sandbox; });
    document.getElementById("setting-root-preparation").hidden = sandbox || els.settingMellow.value !== "root-patch";
    const rootPrepare = document.getElementById("setting-root-prepare");
    rootPrepare.disabled = !!state.appInfo?.execution?.is_sandbox;
    if (!sandbox && els.settingMellow.value === "root-patch" && rootPrepare.disabled) {
      document.getElementById("setting-root-result").textContent = "현재 저장된 모드는 Sandbox입니다. 먼저 x86 Mode와 Mellow 사용 안 함을 저장한 뒤 EFI를 준비하세요.";
    }
    document.getElementById("setting-mode-note").textContent = sandbox
      ? "Sandbox를 선택하면 Mellow native 배포가 사용 안 함으로 변경됩니다."
      : "x86에서는 Mellow EFI·루트 패치를 준비할 수 있습니다.";
  }

  document.addEventListener("DOMContentLoaded", () => {
    try { renderStepper(); if (!state.bridgeReady) setStatus("로컬 엔진 연결 중…"); } catch (_) {}
  });

  whenBridgeReady(() => {
    bindGlobalActions();
    loadInitialData().catch((err) => {
      toast(String(err.message || err), "error");
      const banner = document.getElementById("boot-banner");
      if (banner) banner.textContent = "기기 정보를 불러오지 못했습니다. 연결 상태와 로그를 확인하세요.";
      setStatus("데이터 로드 실패");
      renderStepContent();
    });
  });
})();
