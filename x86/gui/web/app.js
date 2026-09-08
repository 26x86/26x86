(() => {
  "use strict";

  const DEFAULT_STEPS = [
    { id: "welcome", title: "시작", heading: "NextCore에 오신 것을 환영합니다", desc: "오래된 Mac에서 최신 macOS를 사용할 수 있도록 단계별로 안내합니다." },
    { id: "detect", title: "1. 내 Mac 확인", heading: "내 Mac 확인", desc: "하드웨어 정보를 확인합니다." },
    { id: "build", title: "2. 패치 생성", heading: "패치 생성", desc: "부팅할 EFI 구성을 준비합니다." },
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
    "set_execution_mode",
    "get_app_info",
    "get_steps",
    "detect",
    "get_macos_choices",
    "set_target_os",
    "get_patch_status",
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
    if (window.__x86QtBridge && window.__x86QtBridge.__qtWrapped) {
      return window.__x86QtBridge;
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
        window.__x86QtBridge = promisifyQtBridge(channel.objects.bridge);
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
          ensureHttpBridge();
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
    document.getElementById("sidebar-mode").textContent = state.mode === "sandbox" ? "ARM macOS EFI" : "Native Patch";
    document.getElementById("sidebar-host").textContent = state.detect?.model || "확인 대기";
  }

  function renderWelcome() {
    const sandbox = state.mode === "sandbox";
    return `<div class="welcome-hero"><span class="eyebrow">NextCore / CONTROL CENTER</span>
      <h2>당신의 Mac, 다음 장으로.</h2><p class="lead">기기를 확인하고, 실행 방식을 선택하세요.<br>모든 작업의 준비 상태와 검증 결과를 한곳에서 확인합니다.</p>
      <p class="lead">버전 ${escapeHtml(state.appInfo?.version || "")} · ${escapeHtml(state.appInfo?.bundle_id || "")}</p>
      <p class="lead">${sandbox ? "ARM64e macOS · EFI 실행" : "x86 Mode"} · Mellow: ${escapeHtml(state.appInfo?.mellow_deployment || "disabled")}</p>
      ${state.appInfo?.execution_error ? `<p class="note">${escapeHtml(state.appInfo.execution_error)}<br />설정에서 실행 모드와 Mellow 배포 방식을 수정하세요.</p>` : ""}
      <div class="overview-meta"><span class="badge">macOS Tahoe 26</span><span class="badge">Golden Gate 27 · 개발 대상</span><span class="badge warning">실험적 프로젝트</span></div></div>
      <div class="section-label"><h3>실행 방식</h3><span>선택 시 디스크를 변경하지 않습니다</span></div>
      <div class="mode-grid" role="group" aria-label="실행 방식">
        <button class="mode-card${!sandbox ? " selected" : ""}" id="mode-native" aria-pressed="${!sandbox}"><span class="mode-kicker">01 / NATIVE</span><span class="mode-selected" aria-hidden="true"></span><strong>Native Patch</strong><p>EFI 구성과 기기별 루트 패치.<br>현재 하드웨어에서 실행할 구성을 준비합니다.</p><span class="badge">EFI · Root patches</span></button>
        <button class="mode-card${sandbox ? " selected" : ""}" id="mode-sandbox" aria-pressed="${sandbox}"><span class="mode-kicker">02 / VIRTUAL APPLE SILICON</span><span class="mode-selected" aria-hidden="true"></span><strong>ARM macOS EFI</strong><p>EFI에서 직접 실행하는 ARM64e macOS.<br>macOS 27을 위한 실행 경로를 준비합니다.</p><span class="badge warning">개발 중 · macOS 부팅 미검증</span></button>
      </div>
      <div class="actions"><button class="btn primary" id="action-start">기기 확인하기 →</button><button class="btn secondary" id="action-guide">사용 설명서</button></div>
      `;
  }

  function renderArmEfiPreparation() {
    return `<span class="eyebrow">ARM64e macOS / x86_64 EFI</span><h2>ARM macOS EFI 준비</h2>
      <p class="lead">x86_64 컴퓨터의 EFI에서 ARM64e macOS 27을 실행하는 구성입니다.</p>
      <div class="info-grid">${infoRow("실행 환경", "x86_64 EFI")}${infoRow("대상", "macOS 27 · ARM64e")}${infoRow("배포 상태", "설치용 EFI 준비 중")}</div>
      <p class="note">현재 macOS 부팅과 Metal 가속은 미검증입니다. 설치용 EFI와 사용 절차는 개발 진행에 맞춰 제공됩니다.</p>
      <div class="actions"><button type="button" class="btn secondary" id="arm-efi-guide">EFI 준비 안내</button></div>`;
  }

  function renderDetect(step) {
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
    if (state.mode === "sandbox") return renderArmEfiPreparation();
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
    if (state.mode === "sandbox" || state.appInfo?.execution?.is_sandbox) return renderArmEfiPreparation();
    if (state.appInfo?.mellow_deployment === "efi") return `<h2>Mellow EFI 준비</h2>
      <p class="lead">선택한 EFI를 새 폴더로 복사하고 Mellow 진단 kext를 추가합니다.</p>
      <div class="patch-summary">${escapeHtml(state.patchSummary)}</div>
      <label for="mellow-output">새 출력 폴더</label><input class="field" id="mellow-output" placeholder="아직 존재하지 않는 폴더의 전체 경로" />
      <button type="button" class="btn primary" id="action-mellow-efi">EFI 준비</button>
      <pre class="patch-summary" id="mellow-result"></pre>`;
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
      <div class="proof-list"><div class="proof-item"><span>Native EFI 생성</span><span class="badge${state.buildCompleted ? " good" : " warning"}">${state.buildCompleted ? "백엔드 생성 완료 보고" : "완료 보고 없음"}</span></div><div class="proof-item"><span>실제 macOS / Mac USB 부팅</span><span class="badge warning">미검증</span></div></div>
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

    bind("arm-efi-guide", () => api("open_guide"));
    if (["build", "patch"].includes(stepId) && state.mode === "sandbox") return;
    if (stepId === "welcome") {
      const chooseMode = async (mode) => {
        const result = await api("set_execution_mode", mode);
        if (!result.ok) throw new Error(result.error || "실행 방식을 변경하지 못했습니다.");
        state.mode = mode; state.appInfo = await api("get_app_info"); renderStepContent();
        toast(mode === "sandbox" ? "ARM64e macOS EFI 선택" : "Native Patch 선택");
      };
      bind("mode-native", () => chooseMode("native"));
      bind("mode-sandbox", () => chooseMode("sandbox"));
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
    if (state.mode !== "sandbox" && state.steps[index]?.id === "patch") {
      refreshPatchStatus();
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
    state.mode = appInfo.execution?.is_sandbox ? "sandbox" : "native";

    els.appTitle.textContent = appInfo.app_name;
    els.appSubtitle.textContent = "Boot & compatibility";
    els.versionText.textContent = `v${appInfo.version}`;

    if (appInfo.logo_url) {
      els.logo.src = appInfo.logo_url;
      els.logo.hidden = false;
      els.logoFallback.hidden = true;
    }

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
      state.mode = state.appInfo.execution?.is_sandbox ? "sandbox" : "native";
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
