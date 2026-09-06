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
  };

  const QT_BRIDGE_METHODS = [
    "get_sandbox_status",
    "set_execution_mode",
    "get_sandbox_plan",
    "prepare_sandbox",
    "get_app_info",
    "set_hardware_profile",
    "validate_surface_efi",
    "get_steps",
    "detect",
    "get_macos_choices",
    "set_target_os",
    "get_patch_status",
    "get_status",
    "get_settings",
    "save_settings",
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
    return `<span class="eyebrow">EFI NATIVE / APPLE SILICON SANDBOX</span><h2>${stage === "patch" ? "EFI 준비 결과" : "Sandbox 준비"}</h2>
      <p class="lead">macOS 게스트 부팅에 필요한 구성 요소와 현재 구현 상태를 확인합니다.</p>
      <div class="metric-grid"><div class="metric"><span>실행 계층</span><strong>EFI · AIC · ARM64 JIT</strong></div><div class="metric"><span>최소 CPU</span><strong>SSE4.1 + SSE4.2</strong></div><div class="metric"><span>macOS 실제 부팅</span><strong>미검증</strong></div></div>
      <div class="form-row"><div><label for="sandbox-target">대상 macOS</label><select class="field" id="sandbox-target"><option value="26" ${state.sandboxTarget === 26 ? "selected" : ""}>macOS Tahoe 26</option><option value="27" ${state.sandboxTarget === 27 ? "selected" : ""}>macOS Golden Gate 27</option></select></div><div><label for="sandbox-output">새 출력 폴더 경로</label><input class="field" id="sandbox-output" value="${escapeHtml(state.sandboxOutput)}" placeholder="예: C:/26x86-Sandbox 또는 /Users/me/26x86-Sandbox" /></div></div>
      <div class="proof-list"><div class="proof-item"><span>EFI 자체 검사 파일</span><span class="badge${report.artifact_available ? " good" : " warning"}">${report.artifact_available ? "파일 존재" : "미생성"}</span></div><div class="proof-item"><span>VSK 생산 EFI · 외부 trust anchor</span><span class="badge${report.vsk_artifact_available ? " good" : " warning"}">${report.vsk_artifact_available ? "생성됨 · EBS 미호출" : "미생성"}</span></div><div class="proof-item"><span>원본 macOS 부팅</span><span class="badge warning">아직 준비되지 않음</span></div><div class="proof-item"><span>실제 Mac USB 부팅</span><span class="badge warning">실기 검증 필요</span></div></div>
      ${blockers.length ? `<div class="note"><strong>남은 구현 항목</strong><ul>${blockers.map(x => `<li>${escapeHtml(x)}</li>`).join("")}</ul></div>` : ""}
      <p class="support-note">구성: OpenCore config.plist · iBoot 엔진 · SandboxSMBIOS · Hardware/DevProp. 현재 준비 기능은 EFI 자체 검사 패키지를 생성합니다. macOS 설치 또는 부팅을 시작하지 않습니다. 기존 디스크에 자동으로 기록하지 않습니다.</p>
      <div class="actions"><button class="btn secondary" id="sandbox-refresh">준비 상태 다시 확인</button><button class="btn primary" id="sandbox-prepare" ${report.stageable && state.bridgeReady ? "" : "disabled"}>EFI 자체 검사 패키지 준비</button></div>
      ${receipt ? `<pre class="patch-summary" role="status">${escapeHtml(JSON.stringify(receipt, null, 2))}</pre>` : ""}`;
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
    bindStepActions(step.id);
    setStatus(step.title);
    renderStepper();
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

    if ((stepId === "build" || stepId === "patch") && state.mode === "sandbox") {
      const target = document.getElementById("sandbox-target");
      const output = document.getElementById("sandbox-output");
      output.addEventListener("input", () => { state.sandboxOutput = output.value; });
      target.addEventListener("change", async () => {
        state.sandboxTarget = Number(target.value); state.sandboxPlan = null; state.sandboxReceipt = null;
        await refreshSandbox();
      });
      bind("sandbox-refresh", refreshSandbox);
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
    const [appInfo, steps, detectResult, macos, buildCheck, status] = await Promise.all([
      api("get_app_info"),
      api("get_steps"),
      api("detect", false),
      api("get_macos_choices"),
      api("host_can_build"),
      api("get_status"),
    ]);

    state.appInfo = appInfo;
    state.steps = steps.map(step => ({...step, title: ({welcome: "개요", detect: "기기 확인", build: "EFI 준비", patch: "설치 · 패치", done: "검증 · 활동"})[step.id] || step.title}));
    state.detect = detectResult.detect;
    state.macos = macos;
    state.canBuild = !!buildCheck.can_build;
    state.buildMessage = buildCheck.message || null;
    state.buildCompleted = !!status.build_completed;

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
      });
      if (!result.ok) throw new Error(result.error || "save failed");
      els.settingsDialog.close();
      toast("설정을 저장했습니다.");
    } catch (err) {
      toast(String(err.message || err), "error");
    }
  }

  function bindGlobalActions() {
    if (state.globalActionsBound) return;
    state.globalActionsBound = true;
    els.btnPrev.addEventListener("click", () => goToStep(state.currentStep - 1));
    els.btnNext.addEventListener("click", () => goToStep(state.currentStep + 1));
    document.getElementById("btn-settings").addEventListener("click", openSettings);
    document.getElementById("btn-help").addEventListener("click", () => api("open_guide").catch(err => toast(String(err.message || err), "error")));
    document.getElementById("settings-cancel").addEventListener("click", () => els.settingsDialog.close());
    document.getElementById("settings-save").addEventListener("click", saveSettings);

    document.addEventListener("keydown", (event) => {
      if (event.key === "ArrowRight" && (event.metaKey || event.ctrlKey)) {
        goToStep(Math.min(state.steps.length - 1, state.currentStep + 1));
      }
      if (event.key === "ArrowLeft" && (event.metaKey || event.ctrlKey)) {
        goToStep(Math.max(0, state.currentStep - 1));
      }
    });
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
